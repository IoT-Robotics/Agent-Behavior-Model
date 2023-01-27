"""Agent Behavior Modeling Utilities."""


from collections.abc import Sequence
from importlib.metadata import version
from typing import LiteralString


__all__: Sequence[LiteralString] = ('__version__',)


__version__: LiteralString = version(distribution_name='Agent-Behavior-Model')
