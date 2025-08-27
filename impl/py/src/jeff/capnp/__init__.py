"""Utility functions for tket extensions."""

from __future__ import annotations

import os
from pathlib import Path

from typing import Any, Protocol, TypeVar

from jeff.string_table import StringTable


def load_schema() -> Any:
    import capnp  # type: ignore[unused-ignore, import-not-found]

    capnp.remove_import_hook()

    # capnp warns about this environment variable being set
    if "PWD" in os.environ:
        del os.environ["PWD"]

    capnp_file = Path(__file__).parent.joinpath("jeff.capnp")
    return capnp.load(capnp_file)


# The capnp buffer reader for a `JeffCapnp` object.
Reader = TypeVar("Reader", contravariant=True)
# The capnp buffer writer for a `JeffCapnp` object.
Builder = TypeVar("Builder", contravariant=True)


class CapnpBuffer(Protocol[Reader, Builder]):
    """Protocol for objects that have their data backed by a capnp-encoded buffer."""

    @staticmethod
    def _read_from_buffer(reader: Reader) -> CapnpBuffer[Reader, Builder]:
        """Create a new object from a capnp-encoded buffer.

        The reader may be stored internally to avoid caching all the data in memory.
        See
        """

    def _force_read_all(self) -> None:
        """Force the object to read all the data from the buffer into memory,
        and drop any internal references to a Reader.

        This is useful when transitioning an object from "reader" mode to "writer" mode.

        This call spreads recursively to all child objects.
        """

    def _write_to_buffer(
        self,
        new_data: Builder,
        string_table: StringTable,
    ) -> None:
        """Write any cached modifications back to the capnp buffer."""


class LazyUpdate(Protocol):
    """Protocol for objects supported by a capnp buffer that write their modifications in a lazy
    manner.

    An object may be marked as 'dirty' to indicate that it has been modified since the last time
    it was written to a capnp buffer. Use `CapnpBuffer._write_to_buffer` to store the object's
    modifications.

    When implementing this protocol, you may need to override the `_mark_dirty` if there are any
    parent objects that should be marked as clean.
    """

    # Whether the properties have been modified.
    _is_dirty: bool = True

    def _mark_dirty(self) -> None:
        """Mark the object as dirty.

        This call spreads recursively to parent objects.
        """
        self._is_dirty = True

    def _mark_clean(self) -> None:
        """Mark the object as clean.

        An object can be marked clean by itself, but a dirty tag is always propagated upward.
        """
        self._is_dirty = False

    @property
    def is_dirty(self) -> bool:
        """Whether the object has been modified since the last time it was encoded.

        Also returns True if the object has never been written out (e.g. after instantiation).
        """
        return self._is_dirty


# TODO: Temporarily disabled
# schema = load_schema()
schema = None
