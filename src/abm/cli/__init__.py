"""ABM CLI."""


from collections.abc import Sequence

import click

from .exec import exec_and_get_state_seq, compare_output


__all__: Sequence[str] = ('abm_cli',)


@click.group(name='abm',
             cls=click.Group,
             commands={
                 'exec': exec_and_get_state_seq,
                 'compare-output': compare_output,
             },

             # Command kwargs
             context_settings=None,
             # callback=None,
             # params=None,
             help='ABM CLI >>>',
             epilog='^^^ ABM CLI',
             short_help='ABM CLI',
             options_metavar='[OPTIONS]',
             add_help_option=True,
             no_args_is_help=True,
             hidden=False,
             deprecated=False,

             # Group/MultiCommand kwargs
             invoke_without_command=False,
             subcommand_metavar='ABM_SUB_COMMAND',
             chain=False,
             result_callback=None)
def abm_cli():
    """ABM CLI."""
