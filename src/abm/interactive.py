"""Interactive Mode Flag.

In this mode, sensing functions ask for user inputs
when there are no existing set states.
"""


from collections.abc import Sequence
from typing import LiteralString


__all__: Sequence[LiteralString] = ('ON',)


ON: bool = True
