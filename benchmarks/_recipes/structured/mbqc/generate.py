"""Script to generate the MBQC benchmark set."""

import math
from functools import singledispatchmethod
from pathlib import Path

import graphix
import jeff
from graphix import command
from graphix.fundamentals import Plane
from graphix.states import BasicStates
from graphix_qasm_parser.parser import OpenQASMParser
from jeff import JeffOp, JeffValue


def bitwise_xor(x: JeffValue, y: JeffValue) -> JeffOp:
    """Instantiate a bitwise XOR operation."""
    inputs = [x, y]
    outputs = [JeffValue(x.type)]
    return JeffOp("int", "xor", inputs, outputs)


def measure(qubit: JeffValue) -> JeffOp:
    """Single qubit measurement operation."""
    inputs = [qubit]
    outputs = [JeffValue(jeff.IntType(1))]
    return JeffOp("qubit", "measure", inputs, outputs)


def qubit_alloc() -> JeffOp:
    """Single qubit alloc operation."""
    outputs = [JeffValue(jeff.QubitType())]
    return JeffOp("qubit", "alloc", [], outputs)


def const_float(value: float, bitwidth: int) -> JeffOp:
    """Operation that creates a constant float value."""
    assert bitwidth in jeff.FloatPrecisions
    outputs = [JeffValue(jeff.FloatType(bitwidth))]
    return JeffOp("float", f"const{bitwidth}", [], outputs, instruction_data=value)


class PatternConverter:
    qubits: dict[int, JeffValue]
    bits: dict[int, JeffValue]
    ops: list[JeffOp]

    def convert(self, pattern: graphix.Pattern) -> jeff.JeffModule:
        func_inputs = [JeffValue(jeff.QubitType()) for _ in pattern.input_nodes]
        self.qubits = dict(zip(pattern.input_nodes, func_inputs, strict=True))
        self.bits = {}
        self.ops = []
        for cmd in pattern:
            self.process(cmd)
        func_outputs = [self.qubits[i] for i in pattern.output_nodes]
        func_body = jeff.JeffRegion(
            sources=func_inputs, targets=func_outputs, operations=self.ops
        )
        func = jeff.FunctionDef(name="main", body=func_body)
        return jeff.JeffModule([func])

    def add_op(self, op: JeffOp) -> JeffOp:
        self.ops.append(op)
        return op

    @singledispatchmethod
    def process(self, cmd: command.Command) -> None:
        raise NotImplementedError

    @process.register
    def processN(self, cmd: command.N) -> None:
        """Qubit preparation command"""
        [q] = self.add_op(qubit_alloc()).outputs
        assert cmd.state == BasicStates.PLUS
        [q] = self.add_op(jeff.quantum_gate("h", qubits=q)).outputs
        self.qubits[cmd.node] = q

    @process.register
    def processE(self, cmd: command.E) -> None:
        """Qubit entanglement command"""
        [n1, n2] = cmd.nodes
        [self.qubits[n1], self.qubits[n2]] = self.add_op(
            jeff.quantum_gate("cz", qubits=[self.qubits[n1], self.qubits[n2]])
        ).outputs

    @process.register
    def processM(self, cmd: command.M) -> None:
        """Qubit measurement command"""
        q = self.qubits.pop(cmd.node)
        if cmd.s_domain:
            q = self.conditional_gate(q, self.xor(list(sorted(cmd.s_domain))), "x")
        if cmd.t_domain:
            q = self.conditional_gate(q, self.xor(list(sorted(cmd.t_domain))), "z")
        bloch = cmd.measurement.to_bloch()
        if bloch.plane == Plane.XY:
            [q] = self.add_op(jeff.quantum_gate("h", qubits=q)).outputs
        if bloch.angle != 0:
            match bloch.plane:
                case Plane.XY:
                    gate = "rx"
                    angle = -bloch.angle
                case Plane.XZ:
                    gate = "ry"
                    angle = -bloch.angle
                case Plane.YZ:
                    gate = "rx"
                    angle = bloch.angle
                case _:
                    raise NotImplementedError
            assert isinstance(angle, float | int)
            [jeff_angle] = self.add_op(const_float(angle * math.pi, 64)).outputs
            [q] = self.add_op(
                jeff.quantum_gate(gate, qubits=q, params=[jeff_angle])
            ).outputs
        [self.bits[cmd.node]] = self.add_op(measure(q)).outputs

    @process.register
    def processX(self, cmd: command.X) -> None:
        """Pauli X command"""
        self.qubits[cmd.node] = self.conditional_gate(
            self.qubits[cmd.node], self.xor(list(sorted(cmd.domain))), "x"
        )

    @process.register
    def processZ(self, cmd: command.Z) -> None:
        """Pauli Z command"""
        self.qubits[cmd.node] = self.conditional_gate(
            self.qubits[cmd.node], self.xor(list(sorted(cmd.domain))), "z"
        )

    @process.register
    def processC(self, cmd: command.C) -> None:
        """Clifford command"""
        q = self.qubits[cmd.node]
        for gate in cmd.clifford.qasm3:
            [q] = self.add_op(jeff.quantum_gate(gate, qubits=q)).outputs
        self.qubits[cmd.node] = q

    def xor(self, bits: list[int]) -> JeffValue:
        val = self.bits[bits.pop()]
        while bits:
            other = self.bits[bits.pop()]
            [val] = self.add_op(bitwise_xor(val, other)).outputs
        return val

    def conditional_gate(
        self, qubit: JeffValue, condition: JeffValue, gate: str
    ) -> JeffValue:
        # True block
        switch_arg = JeffValue(jeff.QubitType())
        inner = jeff.quantum_gate(gate, qubits=switch_arg)
        then_region = jeff.JeffRegion(
            sources=[inner.inputs[0]], targets=[inner.outputs[0]], operations=[inner]
        )

        # False block
        switch_arg = JeffValue(jeff.QubitType())
        else_region = jeff.JeffRegion(
            sources=[switch_arg], targets=[switch_arg], operations=[]
        )

        # Negate condition so we can put the true branch into the 0 switch position
        [condition] = self.add_op(jeff.bitwise_not(condition)).outputs
        switch = jeff.switch_case(
            index=condition,
            region_args=[qubit],
            branches=[then_region],
            default=else_region,
        )
        self.add_op(switch)
        return switch.outputs[0]  # type: ignore


if __name__ == "__main__":
    circuits_path = Path(__file__).parent / "circuits"
    results_path = Path(__file__).parent.parent.parent.parent / "structured" / "mbqc"

    parser = OpenQASMParser()
    for file in circuits_path.iterdir():
        if not file.is_file() or file.suffix != ".qasm":
            continue
        print(file.name)

        circ = parser.parse_file(file)
        pattern = circ.transpile().pattern
        module = PatternConverter().convert(pattern)
        module.write_out(str(results_path / (file.stem + ".jeff")))
