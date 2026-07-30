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



namespace QiskitToJeff {



FloatOp::FloatOp(double value) : value_(value) {}

uint32_t FloatOp::build(
    capnp::List<jeff::Op>::Builder operations,
    uint32_t op_index,
    ValueMap& values
) const {
    jeff::Op::Builder op = operations[op_index];
    op.initInputs(0);
    uint32_t v = values.allocate_float_value();
    op.initOutputs(1).set(0, v);
    op.getInstruction().initFloat().setConst64(value_);
    return v;
}

AllocOp::AllocOp(uint32_t qubit) : qubit_(qubit) {}

void AllocOp::build(jeff::Op::Builder op, ValueMap& values) const {
    op.initInputs(0);
    uint32_t v = values.allocate_qubit_value();
    op.initOutputs(1).set(0, v);
    op.getInstruction().initQubit().setAlloc();
    values.record_qubit(qubit_, v);
}

MeasureNdOp::MeasureNdOp(const QkCircuitInstruction& inst) : inst_(inst) {}

uint32_t MeasureNdOp::num_jeff_ops() const { return 1; }
uint32_t MeasureNdOp::num_jeff_values() const { return 2; }

void MeasureNdOp::build(
    capnp::List<jeff::Op>::Builder operations,
    uint32_t op_start,
    ValueMap& values
) const {
    jeff::Op::Builder op = operations[op_start];
    op.initInputs(1).set(0, values.resolve_qubit(inst_.qubits[0]));
    uint32_t qubit_value = values.allocate_qubit_value();
    uint32_t clbit_value = values.allocate_bit_value();
    op.initOutputs(2);
    op.getOutputs().set(0, qubit_value);
    op.getOutputs().set(1, clbit_value);
    op.getInstruction().initQubit().setMeasureNd();
    values.record_qubit(inst_.qubits[0], qubit_value);
    values.record_clbit(inst_.clbits[0], clbit_value);
}

WellKnownOp::WellKnownOp(const QkCircuitInstruction& inst) : inst_(inst) {}

uint32_t WellKnownOp::num_jeff_ops() const { return inst_.num_params + 1; }
uint32_t WellKnownOp::num_jeff_values() const { return inst_.num_params + inst_.num_qubits; }

void WellKnownOp::build(capnp::List<jeff::Op>::Builder operations, uint32_t op_start, ValueMap& values) const {
    auto qk_gate_it = NameToQkGateMap.find(inst_.name);
    if (qk_gate_it == NameToQkGateMap.end()) {
      std::fprintf(stderr, "QiskitToJeff::WellKnownOp::build: unrecognized gate name \"%s\"\n", inst_.name);
      std::exit(1);
    }

    jeff::Op::Builder op = operations[op_start + inst_.num_params];

    op.initInputs(inst_.num_qubits + inst_.num_params);
    for (uint32_t i = 0; i < inst_.num_qubits; i++)
        op.getInputs().set(i, values.resolve_qubit(inst_.qubits[i]));

    for (uint32_t i = 0; i < inst_.num_params; i++) {
        uint32_t v = FloatOp(qk_param_as_real(inst_.params[i])).build(operations, op_start + i, values);
        op.getInputs().set(inst_.num_qubits + i, v);
    }

    op.initOutputs(inst_.num_qubits);
    for (uint32_t i = 0; i < inst_.num_qubits; i++) {
        uint32_t v = values.allocate_qubit_value();
        op.getOutputs().set(i, v);
        values.record_qubit(inst_.qubits[i], v);
    }

    WellKnownGate(qk_gate_it->second).emit(op);
}



PPROp::PPROp(const QkCircuit* circuit, size_t index, const QkCircuitInstruction& inst)
    : circuit_(circuit), index_(index), inst_(inst) {}

uint32_t PPROp::num_jeff_ops() const { return 2; }
uint32_t PPROp::num_jeff_values() const { return 1 + inst_.num_qubits; }

void PPROp::build(
    capnp::List<jeff::Op>::Builder operations,
    uint32_t op_start,
    ValueMap& values
) const {
    QkPauliProductRotation rotation;
    qk_circuit_inst_pauli_product_rotation(circuit_, index_, &rotation);

    uint32_t angle_value = FloatOp(qk_param_as_real(rotation.angle)).build(operations, op_start, values);

    jeff::Op::Builder op = operations[op_start + 1];

    op.initInputs(static_cast<unsigned int>(rotation.len) + 1);
    for (size_t i = 0; i < rotation.len; i++)
        op.getInputs().set(i, values.resolve_qubit(inst_.qubits[i]));

    op.getInputs().set(rotation.len, angle_value);

    op.initOutputs(static_cast<unsigned int>(rotation.len));
    for (size_t i = 0; i < rotation.len; i++) {
        uint32_t v = values.allocate_qubit_value();
        op.getOutputs().set(i, v);
        values.record_qubit(inst_.qubits[i], v);
    }

    PauliProductRotationGate(rotation).emit(op);

    qk_pauli_product_rotation_clear(&rotation);
}

Op::Op(const QkCircuit* circuit, size_t index) :
    inst_([&] {
        QkCircuitInstruction i;
        qk_circuit_get_instruction(circuit, index, &i);
        return i;
    }()),
    op_(
        [&]() -> std::variant<WellKnownOp, PPROp, MeasureNdOp> {
            QkOperationKind kind = qk_circuit_instruction_kind(circuit, index);
            if (kind == QkOperationKind_Gate) return WellKnownOp(inst_);
            if (kind == QkOperationKind_PauliProductRotation) return PPROp(circuit, index, inst_);
            if (kind == QkOperationKind_Measure) return MeasureNdOp(inst_);
            std::fprintf(stderr, "QiskitToJeff::Op: unhandled QkOperationKind\n");
            std::exit(1);
        }()
    ) {}

Op::~Op() { qk_circuit_instruction_clear(&inst_); }

uint32_t Op::num_jeff_ops() const {
    return std::visit([](const auto& o) { return o.num_jeff_ops(); }, op_);
}

uint32_t Op::num_jeff_values() const {
    return std::visit([](const auto& o) { return o.num_jeff_values(); }, op_);
}

void Op::build(
    capnp::List<jeff::Op>::Builder operations,
    uint32_t op_start,
    ValueMap& values
) const {
    std::visit([&](const auto& o) { o.build(operations, op_start, values); }, op_);
}

}  // namespace QiskitToJeff
