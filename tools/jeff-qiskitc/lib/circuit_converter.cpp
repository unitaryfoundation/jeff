#include "circuit_converter.h"

#include "gate_converter.h"

#include <cstdio>
#include <cstdlib>
#include <limits>

namespace JeffToQiskit {

namespace {
constexpr uint32_t kNone = std::numeric_limits<uint32_t>::max();

struct Measurement {
    uint32_t qubit;  // Qubit identity, following the qubit through the ops.
    uint32_t result; // The int(1) measurement result value.
};

// The clbit of a measurement after `m` whose result is a target clbit, preferring one on the
// same qubit. That measurement is the clbit's final write, so anything written to the clbit
// before it is overwritten.
uint32_t overwritten_clbit(const std::vector<Measurement>& measurements, size_t m,
                           const std::vector<uint32_t>& target_clbit) {
    for (size_t later = m + 1; later < measurements.size(); later++) {
        if (measurements[later].qubit == measurements[m].qubit &&
            target_clbit.at(measurements[later].result) != kNone)
            return target_clbit.at(measurements[later].result);
    }
    for (size_t later = m + 1; later < measurements.size(); later++) {
        if (target_clbit.at(measurements[later].result) != kNone)
            return target_clbit.at(measurements[later].result);
    }
    return kNone;
}
} // namespace

uint32_t assign_clbits(jeff::Function::Definition::Reader def, ValueMap& values) {
    jeff::Region::Reader body = def.getBody();
    auto value_types = def.getValues();

    // The int(1) targets, in order, are the circuit's clbits.
    std::vector<uint32_t> target_clbit(value_types.size(), kNone);
    uint32_t num_clbits = 0;
    for (uint32_t value : body.getTargets()) {
        auto type = value_types[value].getType();
        if (!type.isInt() || type.getInt() != 1)
            continue;
        if (target_clbit.at(value) != kNone) {
            std::fprintf(stderr,
                         "JeffToQiskit::assign_clbits: int(1) value %u is returned more than "
                         "once, but a measurement can only write one clbit\n",
                         value);
            std::exit(1);
        }
        target_clbit.at(value) = num_clbits++;
    }

    // Follow each qubit through the ops: a qubit output takes the identity of the input at the
    // same position, which holds for every qubit op the converter supports.
    std::vector<uint32_t> qubit_id(value_types.size(), kNone);
    uint32_t num_qubits = 0;
    std::vector<Measurement> measurements;
    for (jeff::Op::Reader op : body.getOperations()) {
        auto instr = op.getInstruction();
        auto inputs = op.getInputs();
        auto outputs = op.getOutputs();

        if (instr.isInt() && instr.getInt().isConst1() && instr.getInt().getConst1() &&
            target_clbit.at(outputs[0]) != kNone) {
            std::fprintf(stderr, "JeffToQiskit::assign_clbits: a clbit returned as the constant "
                                 "1 has no Qiskit equivalent\n");
            std::exit(1);
        }

        if (instr.isQubit() && instr.getQubit().isAlloc()) {
            qubit_id.at(outputs[0]) = num_qubits++;
            continue;
        }
        for (uint32_t i = 0; i < outputs.size() && i < inputs.size(); i++) {
            if (qubit_id.at(inputs[i]) != kNone)
                qubit_id.at(outputs[i]) = qubit_id.at(inputs[i]);
        }
        if (instr.isQubit() && instr.getQubit().isMeasureNd())
            measurements.push_back({qubit_id.at(inputs[0]), outputs[1]});
    }

    for (size_t m = 0; m < measurements.size(); m++) {
        uint32_t clbit = target_clbit.at(measurements[m].result);
        if (clbit == kNone)
            clbit = overwritten_clbit(measurements, m, target_clbit);
        if (clbit == kNone)
            clbit = num_clbits++;
        values.record_clbit(measurements[m].result, clbit);
    }

    return num_clbits;
}

GateOp::GateOp(jeff::Op::Reader jeff_op) : jeff_op_(jeff_op) {}

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

AllocOp::AllocOp(jeff::Op::Reader jeff_op) : jeff_op_(jeff_op) {}

void AllocOp::build(QkCircuit*, ValueMap& values) const {
    values.record_qubit(jeff_op_.getOutputs()[0], values.allocate_qubit());
}

MeasureNdOp::MeasureNdOp(jeff::Op::Reader jeff_op) : jeff_op_(jeff_op) {}

void MeasureNdOp::build(QkCircuit* circuit, ValueMap& values) const {
    std::vector<uint32_t> qubits;
    for (uint32_t value : jeff_op_.getInputs())
        qubits.push_back(values.resolve_qubit(value));

    auto outputs = jeff_op_.getOutputs();
    qk_circuit_measure(circuit, qubits[0], values.resolve_clbit(outputs[1]));

    for (uint32_t i = 0; i < qubits.size(); i++)
        values.record_qubit(outputs[i], qubits[i]);
}

QubitOp::QubitOp(jeff::Op::Reader jeff_op)
    : qubit_op_([&]() -> std::variant<AllocOp, MeasureNdOp, GateOp> {
          auto qubit_op = jeff_op.getInstruction().getQubit();
          if (qubit_op.isAlloc())
              return AllocOp(jeff_op);
          if (qubit_op.isMeasureNd())
              return MeasureNdOp(jeff_op);
          if (qubit_op.isGate())
              return GateOp(jeff_op);
          std::fprintf(stderr, "QubitOp: unhandled QubitOp kind\n");
          std::exit(1);
      }()) {}

void QubitOp::build(QkCircuit* circuit, ValueMap& values) const {
    std::visit([&](const auto& op) { op.build(circuit, values); }, qubit_op_);
}

ResourceCount QubitOp::resource_count() const {
    return std::visit([](const auto& op) { return op.resource_count(); }, qubit_op_);
}

FloatOp::FloatOp(jeff::Op::Reader jeff_op) : jeff_op_(jeff_op) {}

void FloatOp::build(QkCircuit*, ValueMap& values) const {
    auto float_op = jeff_op_.getInstruction().getFloat();
    double value;
    if (float_op.isConst32()) {
        value = float_op.getConst32();
    } else if (float_op.isConst64()) {
        value = float_op.getConst64();
    } else {
        std::fprintf(
            stderr,
            "FloatOp::build: unhandled FloatOp kind (only const32/const64 are supported)\n");
        std::exit(1);
    }
    values.record_float(jeff_op_.getOutputs()[0], value);
}

IntOp::IntOp(jeff::Op::Reader jeff_op) : jeff_op_(jeff_op) {}

void IntOp::build(QkCircuit*, ValueMap&) const {
    if (!jeff_op_.getInstruction().getInt().isConst1()) {
        std::fprintf(stderr, "IntOp::build: unhandled IntOp kind (only const1 is supported)\n");
        std::exit(1);
    }
}

Op::Op(jeff::Op::Reader jeff_op)
    : op_([&]() -> std::variant<QubitOp, FloatOp, IntOp> {
          auto instr = jeff_op.getInstruction();
          if (instr.isQubit())
              return QubitOp(jeff_op);
          if (instr.isFloat())
              return FloatOp(jeff_op);
          if (instr.isInt())
              return IntOp(jeff_op);
          std::fprintf(stderr, "Op: unhandled instruction kind\n");
          std::exit(1);
      }()) {}

void Op::build(QkCircuit* circuit, ValueMap& values) const {
    std::visit([&](const auto& op) { op.build(circuit, values); }, op_);
}

ResourceCount Op::resource_count() const {
    return std::visit([](const auto& op) { return op.resource_count(); }, op_);
}

} // namespace JeffToQiskit

namespace QiskitToJeff {

FloatOp::FloatOp(double value) : value_(value) {}

uint32_t FloatOp::build(capnp::List<jeff::Op>::Builder operations, uint32_t op_index,
                        ValueMap& values) const {
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

ClbitInitOp::ClbitInitOp(uint32_t clbit) : clbit_(clbit) {}

void ClbitInitOp::build(jeff::Op::Builder op, ValueMap& values) const {
    op.initInputs(0);
    uint32_t v = values.allocate_bit_value();
    op.initOutputs(1).set(0, v);
    op.getInstruction().initInt().setConst1(false);
    values.record_clbit(clbit_, v);
}

MeasureNdOp::MeasureNdOp(const QkCircuitInstruction& inst) : inst_(inst) {}

uint32_t MeasureNdOp::num_jeff_ops() const { return 1; }
uint32_t MeasureNdOp::num_jeff_values() const { return 2; }

void MeasureNdOp::build(capnp::List<jeff::Op>::Builder operations, uint32_t op_start,
                        ValueMap& values) const {
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

WellKnownOp::WellKnownOp(const QkCircuitInstruction& inst)
    : inst_(inst), qk_gate_([&] {
          auto qk_gate_it = NameToQkGateMap.find(inst.name);
          if (qk_gate_it == NameToQkGateMap.end()) {
              std::fprintf(stderr,
                           "QiskitToJeff::WellKnownOp: unrecognized gate name \"%s\"\n",
                           inst.name);
              std::exit(1);
          }
          return qk_gate_it->second;
      }()) {}

// The gate op and one float constant per parameter, plus a float constant and an r1 on the
// control qubit if the gate has a control-only phase (see WellKnownGate::control_phase).
uint32_t WellKnownOp::num_jeff_ops() const {
    WellKnownGate gate(qk_gate_);
    return gate.num_params() + 1 + (gate.control_phase(inst_.params) != 0.0 ? 2 : 0);
}

uint32_t WellKnownOp::num_jeff_values() const {
    WellKnownGate gate(qk_gate_);
    return gate.num_params() + inst_.num_qubits +
           (gate.control_phase(inst_.params) != 0.0 ? 2 : 0);
}

void WellKnownOp::build(capnp::List<jeff::Op>::Builder operations, uint32_t op_start,
                        ValueMap& values) const {
    WellKnownGate gate(qk_gate_);
    uint32_t num_params = gate.num_params();

    jeff::Op::Builder op = operations[op_start + num_params];

    op.initInputs(inst_.num_qubits + num_params);
    for (uint32_t i = 0; i < inst_.num_qubits; i++)
        op.getInputs().set(i, values.resolve_qubit(inst_.qubits[i]));

    for (uint32_t i = 0; i < num_params; i++) {
        uint32_t v =
            FloatOp(read_param(inst_.params[i], "QiskitToJeff::WellKnownOp::build"))
                .build(operations, op_start + i, values);
        op.getInputs().set(inst_.num_qubits + i, v);
    }

    op.initOutputs(inst_.num_qubits);
    for (uint32_t i = 0; i < inst_.num_qubits; i++) {
        uint32_t v = values.allocate_qubit_value();
        op.getOutputs().set(i, v);
        values.record_qubit(inst_.qubits[i], v);
    }

    gate.emit(op);

    double phase = gate.control_phase(inst_.params);
    if (phase == 0.0)
        return;

    // Qiskit lists the control qubit first.
    uint32_t control = inst_.qubits[0];
    uint32_t phase_op = op_start + num_params + 1;
    uint32_t phase_value = FloatOp(phase).build(operations, phase_op, values);

    jeff::Op::Builder r1 = operations[phase_op + 1];
    r1.initInputs(2);
    r1.getInputs().set(0, values.resolve_qubit(control));
    r1.getInputs().set(1, phase_value);
    uint32_t v = values.allocate_qubit_value();
    r1.initOutputs(1).set(0, v);
    values.record_qubit(control, v);
    WellKnownGate(QkGate_Phase).emit(r1);
}

PPROp::PPROp(const QkCircuit* circuit, size_t index, const QkCircuitInstruction& inst)
    : circuit_(circuit), index_(index), inst_(inst) {}

uint32_t PPROp::num_jeff_ops() const { return 2; }
uint32_t PPROp::num_jeff_values() const { return 1 + inst_.num_qubits; }

void PPROp::build(capnp::List<jeff::Op>::Builder operations, uint32_t op_start,
                  ValueMap& values) const {
    QkPauliProductRotation rotation;
    qk_circuit_inst_pauli_product_rotation(circuit_, index_, &rotation);
    PauliProductRotationGate gate(rotation);

    uint32_t angle_value = FloatOp(gate.angle()).build(operations, op_start, values);

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

    gate.emit(op);

    qk_pauli_product_rotation_clear(&rotation);
}

Op::Op(const QkCircuit* circuit, size_t index)
    : inst_([&] {
          QkCircuitInstruction i;
          qk_circuit_get_instruction(circuit, index, &i);
          return i;
      }()),
      op_([&]() -> std::variant<WellKnownOp, PPROp, MeasureNdOp> {
          QkOperationKind kind = qk_circuit_instruction_kind(circuit, index);
          if (kind == QkOperationKind_Gate)
              return WellKnownOp(inst_);
          if (kind == QkOperationKind_PauliProductRotation)
              return PPROp(circuit, index, inst_);
          if (kind == QkOperationKind_Measure)
              return MeasureNdOp(inst_);
          std::fprintf(stderr, "QiskitToJeff::Op: unhandled QkOperationKind\n");
          std::exit(1);
      }()) {}

Op::~Op() { qk_circuit_instruction_clear(&inst_); }

uint32_t Op::num_jeff_ops() const {
    return std::visit([](const auto& o) { return o.num_jeff_ops(); }, op_);
}

uint32_t Op::num_jeff_values() const {
    return std::visit([](const auto& o) { return o.num_jeff_values(); }, op_);
}

void Op::build(capnp::List<jeff::Op>::Builder operations, uint32_t op_start,
               ValueMap& values) const {
    std::visit([&](const auto& o) { o.build(operations, op_start, values); }, op_);
}

std::optional<uint32_t> Op::measured_clbit() const {
    if (std::holds_alternative<MeasureNdOp>(op_))
        return inst_.clbits[0];
    return std::nullopt;
}

} // namespace QiskitToJeff
