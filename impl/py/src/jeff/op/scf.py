"""Structured control flow operations."""

from __future__ import annotations

from abc import ABC
import textwrap
from typing import TYPE_CHECKING, Literal

from jeff.op.kind import OpKind, OpType

from ..capnp import LazyUpdate, schema
from ..string_table import StringTable

if TYPE_CHECKING:
    from ..region import Region
    from ..function import FunctionDef


class Scf(ABC, OpType[schema.ScfOp, schema.ScfOp.Builder], LazyUpdate):  # type: ignore
    """A structured control flow operation."""

    # The read-only buffer backing this object.
    _raw_data: schema.ScfOp | None = None  # type: ignore

    def _mark_dirty(self) -> None:
        """Mark the object as dirty.

        This call spreads recursively to parent objects.
        """
        self._is_dirty = True
        if self._op:
            self._op._mark_dirty()

    @staticmethod
    def _read_from_buffer(reader: schema.ScfOp) -> Scf:  # type: ignore
        scf: Scf
        match reader.which:
            case "switch":
                switch = reader.switch
                branches = [
                    Region._read_from_buffer(branch) for branch in switch.branches
                ]
                if switch.default:
                    default = Region._read_from_buffer(switch.default)
                else:
                    default = None
                scf = SwitchSCF(branches, default)
            case "for":
                for_loop = getattr(reader, "for")
                body = Region._read_from_buffer(for_loop)
                scf = ForSCF(body)
            case "while":
                while_loop = getattr(reader, "while")
                condition = Region._read_from_buffer(while_loop.condition)
                body = Region._read_from_buffer(while_loop.body)
                scf = WhileSCF(condition, body)
            case "doWhile":
                do_while = getattr(reader, "doWhile")
                body = Region._read_from_buffer(do_while.body)
                condition = Region._read_from_buffer(do_while.condition)
                scf = DoWhileSCF(body, condition)
            case _:
                raise ValueError(f"unknown scf type: {reader.which}")
        scf._raw_data = reader
        scf._mark_clean()
        return scf

    def _force_read_all(self) -> None:
        self._raw_data = None
        self._mark_dirty()

    def _write_to_buffer(
        self,
        writer: schema.ScfOp.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        self._raw_data = writer.as_reader()
        self._mark_clean()

    @property
    def op_kind(self) -> OpKind:
        """The kind of operation."""
        return OpKind.SCF

    @property
    def parent_func(self) -> FunctionDef | None:
        """Returns the parent function to this scf, if any."""
        if self._op is None:
            return None
        return self._op._func


class SwitchSCF(Scf):
    """Switch-statement operation.

    Switch operations contain a list of regions that are indexed into by an
    integer parameter, as well as an optional default region that is triggered
    when the index is out of bounds.

    All regions must have the same input/output port signature.

    :param branches: List of regions to switch between.
    :param default: Optional default region to execute when the index is out of bounds.
    """

    _branches: list[Region] | None = None

    # The default branch, if any.
    # We use a literal False to indicate that the switch does not have a default branch.
    _default: Region | Literal[False] | None = None

    def __init__(self, branches: list[Region], default: Region | None = None):
        self.branches = branches
        self.default = default
        self._mark_dirty()

    def _force_read_all(self) -> None:
        branches = self.branches
        default = self.default
        for branch in branches:
            branch._force_read_all()
        if default is not None:
            default._force_read_all()
        super()._force_read_all()

    def _write_to_buffer(
        self,
        writer: schema.ScfOp.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        switch = writer.init("switch")

        _branches = self.branches
        branches = switch.init("branches", len(_branches))
        for i, branch in enumerate(_branches):
            branch._write_to_buffer(branches[i], string_table)

        if _default := self.default:
            _default._write_to_buffer(switch.default, string_table)

        super()._write_to_buffer(writer, string_table)

    # settable fields

    @property
    def branches(self) -> list[Region]:
        """Returns the list of branches in this switch operation.

        If the input index is out of bounds, the default branch is executed instead.
        """
        if self._branches is None:
            if self._raw_data is None:
                raise ValueError("SwitchSCF branches haven't been assigned yet")
            self._branches = [
                Region._read_from_buffer(branch)
                for branch in self._raw_data.switch.branches
            ]
            for branch in self._branches:
                branch._set_parent(self)

        return self._branches

    @branches.setter
    def branches(self, branches: list[Region]) -> None:
        """Set the list of branches in this switch operation."""
        for branch in branches:
            branch._force_read_all()
            branch._parent = self
        self._branches = branches
        self._mark_dirty()

    @property
    def default(self) -> Region | None:
        """Returns the default branch in this switch operation.

        If the input index is out of range of the branches, the default branch is executed instead.
        """
        if self._default is None:
            if self._raw_data is None:
                raise ValueError("SwitchSCF default branch hasn't been assigned yet")
            if region := self._raw_data.switch.default:
                self._default = Region._read_from_buffer(region)
                self._default._set_parent(self)
            else:
                self._default = False

        if self._default is None or self._default is False:
            return None
        return self._default

    @default.setter
    def default(self, default: Region | None) -> None:
        """Set the default branch in this switch operation."""
        if default is None:
            self._default = False
        else:
            default._force_read_all()
            default._set_parent(self)
            self._default = default
        self._mark_dirty()

    # Python integration

    def __str__(self) -> str:
        string = "\n"

        for i, branch in enumerate(self.branches):
            string += f"  case {i}:\n"
            string += f"{textwrap.indent(str(branch), '  ')}"

        if default := self.default:
            string += "\n"
            string += "  default:\n"
            string += f"{textwrap.indent(str(default), '  ')}"

        return string


class ForSCF(Scf):
    """For-loop instruction.

    For loop operations contain a single region that represents the loop body.
    The loop iterates from start to stop (exclusive) by step, maintaining state
    from region output to input ports.

    :param body: The region to execute as the loop body.
    """

    _body: Region | None = None

    def __init__(self, body: Region):
        body._set_parent(self)
        self._body = body
        self._mark_dirty()

    def _force_read_all(self) -> None:
        body = self.body
        body._force_read_all()
        super()._force_read_all()

    def _write_to_buffer(
        self,
        writer: schema.ScfOp.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        forloop = writer.init("for")

        _body = self.body
        _body._write_to_buffer(forloop, string_table)

        super()._write_to_buffer(writer, string_table)

    # settable fields

    @property
    def body(self) -> Region:
        """Returns the region to execute as the loop body."""
        if self._body is None:
            forloop = getattr(self._raw_data, "for")
            self._body = Region._read_from_buffer(forloop)
            self._body._set_parent(self)

        return self._body

    @body.setter
    def body(self, body: Region) -> None:
        """Set the region to execute as the loop body."""
        body._force_read_all()
        body._set_parent(self)
        self._body = body
        self._mark_dirty()

    # Python integration

    def __str__(self) -> str:
        string = "\n"
        string += "  body:\n"
        string += f"{textwrap.indent(str(self.body), '  ')}"
        return string


class WhileSCF(Scf):
    """While-loop instruction.

    While loop operations contain two regions: a condition region and a body
    region.

    The condition region is executed before each iteration and accepts the state
    as input, but only produces a bool as output. The body region takes the same
    state as input and output.

    :param condition: The region to execute as the loop condition.
    :param body: The region to execute as the loop body.
    """

    _condition: Region | None = None
    _body: Region | None = None

    def __init__(self, condition: Region, body: Region):
        condition._set_parent(self)
        body._set_parent(self)
        self._condition = condition
        self._body = body
        self._mark_dirty()

    def _force_read_all(self) -> None:
        condition = self.condition
        body = self.body
        condition._force_read_all()
        body._force_read_all()
        super()._force_read_all()

    def _write_to_buffer(
        self,
        writer: schema.ScfOp.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        while_loop = writer.init("while")

        _condition = self.condition
        _condition._write_to_buffer(while_loop.condition, string_table)

        _body = self.body
        _body._write_to_buffer(while_loop.body, string_table)

        super()._write_to_buffer(writer, string_table)

    # settable fields

    @property
    def condition(self) -> Region:
        """Returns the region to execute as the loop condition."""
        if self._condition is None:
            while_loop = getattr(self._raw_data, "while")
            self._condition = Region._read_from_buffer(while_loop.condition)
            self._condition._set_parent(self)

        return self._condition

    @condition.setter
    def condition(self, condition: Region) -> None:
        """Set the region to execute as the loop condition."""
        condition._force_read_all()
        condition._set_parent(self)
        self._condition = condition
        self._mark_dirty()

    @property
    def body(self) -> Region:
        """Returns the region to execute as the loop body."""
        if self._body is None:
            while_loop = getattr(self._raw_data, "while")
            self._body = Region._read_from_buffer(while_loop.body)
            self._body._set_parent(self)

        return self._body

    @body.setter
    def body(self, body: Region) -> None:
        """Set the region to execute as the loop body."""
        body._force_read_all()
        body._set_parent(self)
        self._body = body
        self._mark_dirty()

    # Python integration

    def __str__(self) -> str:
        string = "\n"
        string += "  while:\n"
        string += f"{textwrap.indent(str(self.condition), '  ')}"
        string += "  do:\n"
        string += f"{textwrap.indent(str(self.body), '  ')}"
        return string


class DoWhileSCF(Scf):
    """Do-while-loop instruction.

    Do-while loop operations contain two regions: a body region and a condition
    region.

    The body is executed first, then the condition is checked. The region
    signatures are the same as for the while loop.

    :param body: The region to execute as the loop body.
    :param condition: The region to execute as the loop condition.
    """

    _body: Region | None = None
    _condition: Region | None = None

    def __init__(self, body: Region, condition: Region):
        body._set_parent(self)
        condition._set_parent(self)
        self._body = body
        self._condition = condition
        self._mark_dirty()

    def _force_read_all(self) -> None:
        body = self.body
        condition = self.condition
        body._force_read_all()
        condition._force_read_all()
        super()._force_read_all()

    def _write_to_buffer(
        self,
        writer: schema.ScfOp.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        do_while = writer.init("doWhile")

        _body = self.body
        _body._write_to_buffer(do_while.body, string_table)

        _condition = self.condition
        _condition._write_to_buffer(do_while.condition, string_table)

        super()._write_to_buffer(writer, string_table)

    # settable fields

    @property
    def body(self) -> Region:
        """Returns the region to execute as the loop body."""
        if self._body is None:
            do_while = getattr(self._raw_data, "doWhile")
            self._body = Region._read_from_buffer(do_while.body)
            self._body._set_parent(self)

        return self._body

    @body.setter
    def body(self, body: Region) -> None:
        """Set the region to execute as the loop body."""
        body._force_read_all()
        body._set_parent(self)
        self._body = body
        self._mark_dirty()

    @property
    def condition(self) -> Region:
        """Returns the region to execute as the loop condition."""
        if self._condition is None:
            do_while = getattr(self._raw_data, "doWhile")
            self._condition = Region._read_from_buffer(do_while.condition)
            self._condition._set_parent(self)

        return self._condition

    @condition.setter
    def condition(self, condition: Region) -> None:
        """Set the region to execute as the loop condition."""
        condition._force_read_all()
        condition._set_parent(self)
        self._condition = condition
        self._mark_dirty()

    # Python integration

    def __str__(self) -> str:
        string = "\n"
        string += "  do:\n"
        string += f"{textwrap.indent(str(self.body), '  ')}"
        string += "  while:\n"
        string += f"{textwrap.indent(str(self.condition), '  ')}"
        return string
