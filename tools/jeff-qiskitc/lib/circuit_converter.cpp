#include "circuit_converter.h"
#include "gate_converter.h"

#include <cstdio>
#include <cstdlib>

namespace JeffToQiskit {


GateOp::GateOp(jeff::Op::Reader jeff_op): jeff_op_(jeff_op) {}

void GateOp::build(QkCircuit* circuit, ValueMap& values) const {
    auto qubit_gate = jeff_op_.getInstruction().getQubit().getGate();
    QubitGate gate(qubit_gate);

    uint32_t num_qubits, num_params;
    gate.operand_counts(&num_qubits, &num_params);

    auto inputs = jeff_op_.getInputs();
    std::vector<uint32_t> qubits;
    for (uint32_t i = 0; i < num_qubits; i++)
        qubits.push_back(values.resolve_qubit(inputs[i]));

    std::vector<double> params;
    for (uint32_t i = 0; i < num_params; i++)
        params.push_back(values.resolve_float(inputs[num_qubits + i]));

    gate.emit(circuit, qubits, params);

    auto outputs = jeff_op_.getOutputs();
    for (uint32_t i = 0; i < qubits.size(); i++)
        values.record_qubit(outputs[i], qubits[i]);

}

AllocOp::AllocOp(jeff::Op::Reader jeff_op): jeff_op_(jeff_op) {}

void AllocOp::build(QkCircuit*, ValueMap& values) const {
    values.record_qubit(
        jeff_op_.getOutputs()[0],
        values.allocate_qubit()
    );
}

MeasureNdOp::MeasureNdOp(jeff::Op::Reader jeff_op): jeff_op_(jeff_op) {}

void MeasureNdOp::build(QkCircuit* circuit, ValueMap& values) const {
    std::vector<uint32_t> qubits;
    for (uint32_t value : jeff_op_.getInputs())
        qubits.push_back(values.resolve_qubit(value));

    qk_circuit_measure(circuit, qubits[0], values.allocate_clbit());

    auto outputs = jeff_op_.getOutputs();
    for (uint32_t i = 0; i < qubits.size(); i++)
        values.record_qubit(outputs[i], qubits[i]);
}

QubitOp::QubitOp(jeff::Op::Reader jeff_op):
    qubit_op_([&]() -> std::variant<AllocOp, MeasureNdOp, GateOp> {
        auto qubit_op = jeff_op.getInstruction().getQubit();
        if (qubit_op.isAlloc()) return AllocOp(jeff_op);
        if (qubit_op.isMeasureNd()) return MeasureNdOp(jeff_op);
        if (qubit_op.isGate()) return GateOp(jeff_op);
        std::fprintf(stderr, "QubitOp: unhandled QubitOp kind\n");
        std::exit(1);
    }()) {}

void QubitOp::build(QkCircuit* circuit, ValueMap& values) const {
    std::visit(
        [&](const auto& op) {
            op.build(circuit, values);
        },
        qubit_op_
    );
}

ResourceCount QubitOp::resource_count() const {
    return std::visit(
        [](const auto& op) { return op.resource_count(); },
        qubit_op_
    );
}

FloatOp::FloatOp( jeff::Op::Reader jeff_op ): jeff_op_(jeff_op) {}

void FloatOp::build(QkCircuit*, ValueMap& values) const {
    auto float_op = jeff_op_.getInstruction().getFloat();
    double value;
    if (float_op.isConst32()) {
        value = float_op.getConst32();
    } else if (float_op.isConst64()) {
        value = float_op.getConst64();
    } else {
        std::fprintf(stderr, "FloatOp::build: unhandled FloatOp kind (only const32/const64 are supported)\n");
        std::exit(1);
    }
    values.record_float(jeff_op_.getOutputs()[0], value);
}

Op::Op(jeff::Op::Reader jeff_op):
    op_([&]() -> std::variant<QubitOp, FloatOp> {
        auto instr = jeff_op.getInstruction();
        if (instr.isQubit()) return QubitOp(jeff_op);
        if (instr.isFloat()) return FloatOp(jeff_op);
        std::fprintf(stderr, "Op: unhandled instruction kind\n");
        std::exit(1);
    }()) {}


void Op::build(QkCircuit* circuit, ValueMap& values) const {
    std::visit(
        [&](const auto& op) {
            op.build(circuit, values);
        },
        op_
    );
}

ResourceCount Op::resource_count() const {
    return std::visit(
        [](const auto& op) { return op.resource_count(); },
        op_
    );
}

}
