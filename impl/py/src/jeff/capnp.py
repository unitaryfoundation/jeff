"""Utility functions for tket extensions."""

import os
from pathlib import Path

from typing import Any


def load_schema() -> Any:
    import capnp

    capnp.remove_import_hook()

    import jeff

    # capnp warns about this environment variable being set
    if "PWD" in os.environ:
        del os.environ["PWD"]

    capnp_file = Path(jeff.__file__).parent.joinpath("data", "jeff.capnp")
    return capnp.load(str(capnp_file))
