"""Decorators."""


from collections.abc import Sequence
from functools import wraps
from inspect import FullArgSpec, getfullargspec
import json
import re
from typing import Any, Callable, Optional, TypeVar

from . import interactive


__all__: Sequence[str] = 'act', 'sense', 'STATE_SEQ'


_OBJECT_MEMORY_PATTERN: str = ' object at 0x([0-9]|[a-f]|[A-F])+'
CallableTypeVar = TypeVar('CallableTypeVar', bound=Callable[..., Any])


_ACT_DECOR_FLAG: str = '__ACT_DECORATED__'
_SENSE_DECOR_FLAG: str = '__SENSE_DECORATED__'

STATE_SEQ: list = []


def args_dict_from_func_and_given_args(func: CallableTypeVar,
                                       *args: Any, **kwargs: Any) -> dict[str, Any]:  # noqa: E501
    """Get arguments dict from function and given arguments."""
    # extract function's argument specs
    arg_spec: FullArgSpec = getfullargspec(func=func)
    # kw_only_arg_names: list[str] = arg_spec.kwonlyargs
    # kw_only_var_arg_name: Optional[str] = arg_spec.varkw

    # get number of matched positional arguments
    n_matched_pos_args: int = min(len(pos_arg_names := arg_spec.args),
                                  n_args := len(args))

    # initialize args_dict with matched positional arguments and given kwargs
    args_dict: dict[str, Any] = dict(zip(pos_arg_names[:n_matched_pos_args],
                                         args[:n_matched_pos_args])) | kwargs

    # insert positional argument defaults where applicable
    if (pos_arg_defaults_tup := arg_spec.defaults):
        # pylint: disable=invalid-name
        for k, v in zip(pos_arg_names[-len(pos_arg_defaults_tup):],
                        pos_arg_defaults_tup):
            if k not in args_dict:
                args_dict[k] = v

    # record positional varargs where applicable
    if arg_spec.varargs and ((n_var_args := n_args - n_matched_pos_args) > 0):
        args_dict['VARARGS'] = args[-n_var_args:]

    # insert keyword-only argument defaults where applicable
    if (kw_only_arg_defaults := arg_spec.kwonlydefaults):
        # pylint: disable=invalid-name
        for k, v in kw_only_arg_defaults.items():
            if k not in args_dict:
                args_dict[k] = v

    return args_dict


def sanitize_object_name(obj: Any) -> Optional[str]:
    """Sanitize object name."""
    return (None
            if obj is None
            else re.sub(_OBJECT_MEMORY_PATTERN, '', str(obj)))


def check_decor_status(func: callable, /) -> Optional[AssertionError]:
    """Ensure function has NOT been `act`- or `sense`-decorated."""
    assert not getattr(func, _ACT_DECOR_FLAG, False), \
        f'*** {func} ALREADY `act`-DECORATED ***'

    assert not getattr(func, _SENSE_DECOR_FLAG, False), \
        f'*** {func} ALREADY `sense`-DECORATED ***'


def act(actuating_func: CallableTypeVar, /) -> CallableTypeVar:
    """Actuation decorator."""
    # (use same signature for IDE code autocomplete to work)

    check_decor_status(actuating_func)

    @wraps(actuating_func)
    def decor_actuating_func(*args: Any, **kwargs: Any) -> tuple[str, dict[str, Any]]:  # noqa: E501
        actuating_func(*args, **kwargs)

        args_dict: dict[str, Any] = \
            args_dict_from_func_and_given_args(actuating_func, *args, **kwargs)

        print_args: dict[str, Any] = args_dict.copy()
        self_arg: Optional[Any] = print_args.pop('self', None)
        input_arg_strs: list[str] = [f'{k}={v}' for k, v in print_args.items()]
        self_name: Optional[str] = sanitize_object_name(self_arg)
        print((f'ACT: {self_name}.' if self_name else 'ACT: ') +
              f"{actuating_func.__name__}({', '.join(input_arg_strs)})")

        result: tuple[str, dict] = actuating_func.__qualname__, args_dict

        global STATE_SEQ  # pylint: disable=global-variable-not-assigned
        STATE_SEQ.append(result)

        return result

    setattr(decor_actuating_func, _ACT_DECOR_FLAG, True)

    return decor_actuating_func


def sense(sensing_func: CallableTypeVar, /) -> CallableTypeVar:
    """Sensing decorator."""
    # (use same signature for IDE code autocomplete to work)

    check_decor_status(sensing_func)

    # name of private dict storing current sensing states
    sensing_state_dict_name: str = f'_{(sensing_func_name := sensing_func.__name__)}'  # noqa: E501

    @wraps(sensing_func)
    def decor_sensing_func(*args: Any, set: Any = None, **kwargs: Any) -> Any:
        # pylint: disable=redefined-builtin,too-many-locals
        result: Any = sensing_func(*args, **kwargs)

        args_dict: dict[str, Any] = \
            args_dict_from_func_and_given_args(sensing_func, *args, **kwargs)

        print_args: dict[str, Any] = args_dict.copy()

        # get self
        if (self := print_args.pop('self', None)):
            self_dot_str: str = f'{self}.'

        else:
            self: callable = sensing_func
            self_dot_str: str = ''

        # private dict storing current sensing states
        if (sensing_state_dict :=
            getattr(self, sensing_state_dict_name, None)) is None:  # noqa: E129,E501
            setattr(self, sensing_state_dict_name, (sensing_state_dict := {}))

        # tuple & str forms of input args
        input_arg_tuple: tuple[tuple[str, Any], ...] = \
            tuple(input_arg_dict_items := print_args.items())
        input_arg_strs: list[str] = [f'{k}={v}' for k, v in input_arg_dict_items]  # noqa: E501

        if set is None:
            return_annotation: Optional[type] = \
                sensing_func.__annotations__.get('return')
            return_annotation_str: str = (f': {return_annotation}'
                                          if return_annotation
                                          else '')
            print_str: str = (f'SENSE: {self_dot_str}{sensing_func_name}'
                              f"({', '.join(input_arg_strs)})"
                              f'{return_annotation_str} = ')

            # if input_arg_tuple is in current sensing states,
            # then get and return corresponding value
            if input_arg_tuple in sensing_state_dict:
                value: Any = sensing_state_dict.get(input_arg_tuple)

                if isinstance(value, list):
                    if not value:
                        return None

                    return_value: Any = value[0]
                    sensing_state_dict[input_arg_tuple] = value[1:]

                else:
                    return_value: Any = value

                print(f'{print_str}{return_value}')

            elif interactive.ON:
                # ask user for direct input
                return_value: Any = json.loads(input(f'{print_str}? (in JSON)   '))  # noqa: E501

            else:
                # return the sensing function's result
                return_value: Any = result

                print(f'{print_str}{return_value}')

            global STATE_SEQ  # pylint: disable=global-variable-not-assigned
            STATE_SEQ.append((sensing_func.__qualname__, args_dict, return_value))  # noqa: E501

            return return_value

        # else: set the provided value in current sensing states
        sensing_state_dict[input_arg_tuple] = set
        print(f'SET: {self_dot_str}{sensing_state_dict_name}'
              f"[{', '.join(input_arg_strs)}] = {set}")
        return None

    setattr(decor_sensing_func, _SENSE_DECOR_FLAG, True)

    return decor_sensing_func
