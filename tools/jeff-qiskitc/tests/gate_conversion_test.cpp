// Tests for both jeff <-> QkCircuit directions (jeff_to_qiskitc,
// qiskitc_to_jeff). Each test builds one gate/ppr op directly and checks
// the single result -- no round-tripping through the other direction.
//
// Covers every gate in WellKnownToQkGateMap/ControlledQkGateMap plus a
// few Pauli product rotations, one test case per gate.
//
//   cmake --build build --target gate_conversion_test
//   ./build/tests/gate_conversion_test

#include "../lib/gate_converter.h"
#include "capnp/jeff.capnp.h"
#include "jeff_qiskitc.h"
#include "test_utils.h"

#include <capnp/message.h>
#include <capnp/serialize.h>
#include <gtest/gtest.h>
#include <qiskit.h>

#include <algorithm>
#include <cstdint>
#include <functional>
#include <memory>
#include <ostream>
#include <string>
#include <unordered_map>
#include <vector>

namespace jeff_qiskitc_test {

// QkGate -> Qiskit instruction name, reversed from NameToQkGateMap.
const std::unordered_map<QkGate, std::string> kQkGateNames = [] {
    std::unordered_map<QkGate, std::string> reverse;
    for (const auto& [name, qk_gate] : NameToQkGateMap)
        reverse.emplace(qk_gate, name);
    return reverse;
}();

// Builds a jeff::Module with one function: num_qubits qubit allocs, one
// FloatOp.const64 per entry in params, then a single QubitGate op
// (configured by configure_gate) consuming all of them.
//
// The returned Reader borrows from `message`, which must outlive it.
jeff::Module::Reader
build_single_gate_module(capnp::MessageBuilder& message, uint32_t num_qubits,
                         const std::vector<double>& params,
                         const std::function<void(jeff::QubitGate::Builder)>& configure_gate) {
    uint32_t num_floats = static_cast<uint32_t>(params.size());
    uint32_t num_values = num_qubits * 2 + num_floats;
    uint32_t num_ops = num_qubits + num_floats + 1;

    jeff::Module::Builder mod = message.initRoot<jeff::Module>();
    mod.setVersion(jeff::SCHEMA_VERSION_MAJOR);
    mod.setVersionMinor(jeff::SCHEMA_VERSION_MINOR);
    mod.setVersionPatch(jeff::SCHEMA_VERSION_PATCH);
    mod.setEntrypoint(0);
    mod.initStrings(1).set(0, "gate_conversion_test");

    jeff::Function::Builder fn = mod.initFunctions(1)[0];
    fn.setName(0);
    jeff::Function::Definition::Builder def = fn.initDefinition();

    auto values = def.initValues(num_values);
    for (uint32_t i = 0; i < num_qubits * 2; i++)
        values[i].initType().setQubit();
    for (uint32_t i = 0; i < num_floats; i++) {
        values[num_qubits * 2 + i].initType().setFloat(jeff::FloatPrecision::FLOAT64);
    }

    jeff::Region::Builder body = def.initBody();
    body.initSources(0);
    body.initTargets(0);
    auto operations = body.initOperations(num_ops);

    uint32_t op_idx = 0;
    uint32_t next_value = 0;

    std::vector<uint32_t> input_qubits(num_qubits);
    for (uint32_t q = 0; q < num_qubits; q++) {
        jeff::Op::Builder op = operations[op_idx++];
        op.initInputs(0);
        op.initOutputs(1).set(0, next_value);
        op.getInstruction().initQubit().setAlloc();
        input_qubits[q] = next_value++;
    }

    std::vector<uint32_t> input_floats(num_floats);
    for (uint32_t i = 0; i < num_floats; i++) {
        jeff::Op::Builder op = operations[op_idx++];
        op.initInputs(0);
        op.initOutputs(1).set(0, next_value);
        op.getInstruction().initFloat().setConst64(params[i]);
        input_floats[i] = next_value++;
    }

    jeff::Op::Builder gate_op = operations[op_idx++];
    gate_op.initInputs(num_qubits + num_floats);
    for (uint32_t q = 0; q < num_qubits; q++)
        gate_op.getInputs().set(q, input_qubits[q]);
    for (uint32_t i = 0; i < num_floats; i++) {
        gate_op.getInputs().set(num_qubits + i, input_floats[i]);
    }

    gate_op.initOutputs(num_qubits);
    for (uint32_t q = 0; q < num_qubits; q++)
        gate_op.getOutputs().set(q, next_value++);

    configure_gate(gate_op.getInstruction().initQubit().initGate());

    return mod.asReader();
}

// Builds a QkCircuit with num_qubits qubits and one qk_gate instruction
// on physical qubits {0..num_qubits-1} ({controls..., targets...}).
CircuitPtr build_single_gate_circuit(QkGate qk_gate, uint32_t num_qubits,
                                     const std::vector<double>& params) {
    CircuitPtr qc(qk_circuit_new(num_qubits, 0));
    std::vector<uint32_t> qubits(num_qubits);
    for (uint32_t i = 0; i < num_qubits; i++)
        qubits[i] = i;
    qk_circuit_gate(qc.get(), qk_gate, qubits.data(), params.empty() ? nullptr : params.data());
    return qc;
}

// Distinct, nonzero test values.
std::vector<double> test_params(uint32_t num_params) {
    std::vector<double> params(num_params);
    for (uint32_t i = 0; i < num_params; i++)
        params[i] = 0.5 + i;
    return params;
}

//===--------------------------------------------------------------------===//
// Well-known gates
//===--------------------------------------------------------------------===//

struct GateCase {
    jeff::WellKnownGate well_known;
    uint8_t control_qubits;
    QkGate qk_gate;
};

// CMake's gtest_discover_tests names each ctest entry after the printed
// parameter, so without this the test names are raw byte dumps.
void PrintTo(const GateCase& gate_case, std::ostream* os) {
    *os << kQkGateNames.at(gate_case.qk_gate) << "_c"
        << static_cast<uint32_t>(gate_case.control_qubits);
}

class WellKnownGateTest : public ::testing::TestWithParam<GateCase> {};

// Every gate in WellKnownToQkGateMap uncontrolled, plus every entry of
// ControlledQkGateMap whose base gate has a jeff WellKnownGate equivalent
// (Sdg, SX, U1, U3, ... don't, so they're left out).
std::vector<GateCase> well_known_gate_cases() {
    std::vector<GateCase> cases;
    for (const auto& [well_known, qk_gate] : WellKnownToQkGateMap) {
        cases.push_back({well_known, /*control_qubits=*/0, qk_gate});
    }
    for (const auto& [key, controlled_gate] : ControlledQkGateMap) {
        const auto& [control_qubits, base_gate] = key;
        auto well_known_it = QkGateToWellKnownMap.find(base_gate);
        if (well_known_it == QkGateToWellKnownMap.end())
            continue;
        cases.push_back({well_known_it->second, control_qubits, controlled_gate});
    }
    // The maps are unordered; sort so test ordering is deterministic.
    std::sort(cases.begin(), cases.end(), [](const GateCase& a, const GateCase& b) {
        return std::make_pair(kQkGateNames.at(a.qk_gate), a.control_qubits) <
               std::make_pair(kQkGateNames.at(b.qk_gate), b.control_qubits);
    });
    return cases;
}

std::string gate_case_name(const ::testing::TestParamInfo<GateCase>& info) {
    return kQkGateNames.at(info.param.qk_gate) + "_c" + std::to_string(info.param.control_qubits);
}

// jeff_to_qiskitc: a wellKnown gate maps to the expected QkGate, with the
// right name, qubit order, and params.
TEST_P(WellKnownGateTest, JeffToQiskit) {
    const GateCase& gate_case = GetParam();
    const std::string& name = kQkGateNames.at(gate_case.qk_gate);

    const uint32_t num_qubits = qk_gate_num_qubits(gate_case.qk_gate);
    const uint32_t num_targets = num_qubits - gate_case.control_qubits;
    const std::vector<double> params = test_params(qk_gate_num_params(gate_case.qk_gate));

    capnp::MallocMessageBuilder message;
    jeff::Module::Reader mod =
        build_single_gate_module(message, num_qubits, params, [&](jeff::QubitGate::Builder gate) {
            gate.setWellKnown(gate_case.well_known);
            gate.setControlQubits(gate_case.control_qubits);
            gate.setAdjoint(false);
            gate.setPower(1);
        });

    const CircuitPtr circuit(jeff_to_qiskitc(mod));

    EXPECT_EQ(qk_circuit_num_qubits(circuit.get()), num_qubits);
    ASSERT_EQ(qk_circuit_num_instructions(circuit.get()), 1u);

    const ScopedInstruction inst(circuit.get(), 0);
    EXPECT_EQ(std::string(inst->name), name);
    ASSERT_EQ(inst->num_qubits, num_qubits);

    // jeff orders qubits {targets..., controls...}; Qiskit wants
    // {controls..., targets...}.
    for (uint32_t i = 0; i < gate_case.control_qubits; i++) {
        EXPECT_EQ(inst->qubits[i], num_targets + i) << "control " << i;
    }
    for (uint32_t i = 0; i < num_targets; i++) {
        EXPECT_EQ(inst->qubits[gate_case.control_qubits + i], i) << "target " << i;
    }

    ASSERT_EQ(inst->num_params, params.size());
    for (uint32_t i = 0; i < params.size(); i++) {
        EXPECT_EQ(qk_param_as_real(inst->params[i]), params[i]) << "param " << i;
    }
}

// qiskitc_to_jeff: a QkGate produces the expected wellKnown value, with the
// alloc/const64/gate ops in the right slots and order.
TEST_P(WellKnownGateTest, QiskitToJeff) {
    const GateCase& gate_case = GetParam();

    const uint32_t num_qubits = qk_gate_num_qubits(gate_case.qk_gate);
    const uint32_t num_targets = num_qubits - gate_case.control_qubits;
    const std::vector<double> params = test_params(qk_gate_num_params(gate_case.qk_gate));
    const uint32_t num_params = static_cast<uint32_t>(params.size());

    const CircuitPtr circuit = build_single_gate_circuit(gate_case.qk_gate, num_qubits, params);
    kj::Array<capnp::word> serialized = qiskitc_to_jeff(circuit.get());

    capnp::FlatArrayMessageReader reader(serialized.asPtr());
    jeff::Module::Reader mod = reader.getRoot<jeff::Module>();

    auto operations = mod.getFunctions()[0].getDefinition().getBody().getOperations();
    ASSERT_EQ(operations.size(), num_qubits + num_params + 1) << "allocs + param consts + gate";

    // operations[0..num_qubits) are the qubit allocs, output q = physical qubit q.
    std::vector<uint32_t> qubit_values(num_qubits);
    for (uint32_t q = 0; q < num_qubits; q++)
        qubit_values[q] = operations[q].getOutputs()[0];

    std::vector<uint32_t> float_values(num_params);
    for (uint32_t i = 0; i < num_params; i++) {
        SCOPED_TRACE("param " + std::to_string(i));
        jeff::Op::Reader op = operations[num_qubits + i];
        float_values[i] = op.getOutputs()[0];
        auto instr = op.getInstruction();
        ASSERT_TRUE(instr.isFloat());
        ASSERT_TRUE(instr.getFloat().isConst64());
        EXPECT_EQ(instr.getFloat().getConst64(), params[i]);
    }

    jeff::Op::Reader gate_op = operations[num_qubits + num_params];
    auto instr = gate_op.getInstruction();
    ASSERT_TRUE(instr.isQubit());
    ASSERT_TRUE(instr.getQubit().isGate());

    jeff::QubitGate::Reader gate = instr.getQubit().getGate();
    ASSERT_TRUE(gate.isWellKnown());
    EXPECT_EQ(gate.getWellKnown(), gate_case.well_known);
    EXPECT_EQ(gate.getControlQubits(), gate_case.control_qubits);
    EXPECT_FALSE(gate.getAdjoint());
    EXPECT_EQ(gate.getPower(), 1);

    auto inputs = gate_op.getInputs();
    ASSERT_EQ(inputs.size(), num_qubits + num_params);

    // Qiskit built {controls..., targets...}; jeff wants {targets..., controls...}.
    for (uint32_t i = 0; i < num_targets; i++) {
        EXPECT_EQ(inputs[i], qubit_values[gate_case.control_qubits + i]) << "target " << i;
    }
    for (uint32_t i = 0; i < gate_case.control_qubits; i++) {
        EXPECT_EQ(inputs[num_targets + i], qubit_values[i]) << "control " << i;
    }
    for (uint32_t i = 0; i < num_params; i++) {
        EXPECT_EQ(inputs[num_qubits + i], float_values[i]) << "float input " << i;
    }
}

INSTANTIATE_TEST_SUITE_P(Gates, WellKnownGateTest, ::testing::ValuesIn(well_known_gate_cases()),
                         gate_case_name);

//===--------------------------------------------------------------------===//
// Pauli product rotations
//===--------------------------------------------------------------------===//

struct PprCase {
    std::string label;
    std::vector<jeff::Pauli> pauli_string;
    double angle;
};

void PrintTo(const PprCase& ppr_case, std::ostream* os) { *os << ppr_case.label; }

class PauliProductRotationTest : public ::testing::TestWithParam<PprCase> {};

void pauli_to_zx(jeff::Pauli pauli, bool* z, bool* x) {
    switch (pauli) {
    case jeff::Pauli::I:
        *z = false;
        *x = false;
        break;
    case jeff::Pauli::X:
        *z = false;
        *x = true;
        break;
    case jeff::Pauli::Z:
        *z = true;
        *x = false;
        break;
    case jeff::Pauli::Y:
        *z = true;
        *x = true;
        break;
    }
}

// jeff_to_qiskitc: a ppr gate produces a matching QkPauliProductRotation.
TEST_P(PauliProductRotationTest, JeffToQiskit) {
    const PprCase& ppr_case = GetParam();
    const uint32_t num_qubits = static_cast<uint32_t>(ppr_case.pauli_string.size());

    capnp::MallocMessageBuilder message;
    jeff::Module::Reader mod = build_single_gate_module(
        message, num_qubits, {ppr_case.angle}, [&](jeff::QubitGate::Builder gate) {
            auto pauli_list = gate.initPpr().initPauliString(num_qubits);
            for (uint32_t i = 0; i < num_qubits; i++) {
                pauli_list.set(i, ppr_case.pauli_string[i]);
            }
            gate.setControlQubits(0);
            gate.setAdjoint(false);
            gate.setPower(1);
        });

    const CircuitPtr circuit(jeff_to_qiskitc(mod));

    ASSERT_EQ(qk_circuit_num_instructions(circuit.get()), 1u);
    ASSERT_EQ(qk_circuit_instruction_kind(circuit.get(), 0), QkOperationKind_PauliProductRotation);

    QkPauliProductRotation rotation;
    qk_circuit_inst_pauli_product_rotation(circuit.get(), 0, &rotation);

    EXPECT_EQ(rotation.len, num_qubits);
    for (uint32_t i = 0; i < num_qubits && i < rotation.len; i++) {
        bool expected_z = false, expected_x = false;
        pauli_to_zx(ppr_case.pauli_string[i], &expected_z, &expected_x);
        EXPECT_EQ(rotation.z[i], expected_z) << "z[" << i << "]";
        EXPECT_EQ(rotation.x[i], expected_x) << "x[" << i << "]";
    }
    EXPECT_EQ(qk_param_as_real(rotation.angle), ppr_case.angle);

    qk_pauli_product_rotation_clear(&rotation);
}

// qiskitc_to_jeff: a QkPauliProductRotation produces a matching ppr gate op.
TEST_P(PauliProductRotationTest, QiskitToJeff) {
    const PprCase& ppr_case = GetParam();
    const uint32_t num_qubits = static_cast<uint32_t>(ppr_case.pauli_string.size());

    auto z = std::make_unique<bool[]>(num_qubits);
    auto x = std::make_unique<bool[]>(num_qubits);
    for (uint32_t i = 0; i < num_qubits; i++) {
        pauli_to_zx(ppr_case.pauli_string[i], &z[i], &x[i]);
    }
    std::unique_ptr<QkParam, decltype(&qk_param_free)> angle_param(
        qk_param_from_double(ppr_case.angle), qk_param_free);
    QkPauliProductRotation rotation{z.get(), x.get(), num_qubits, angle_param.get()};

    CircuitPtr circuit(qk_circuit_new(num_qubits, 0));
    std::vector<uint32_t> qubits(num_qubits);
    for (uint32_t i = 0; i < num_qubits; i++)
        qubits[i] = i;
    qk_circuit_pauli_product_rotation(circuit.get(), &rotation, qubits.data());

    kj::Array<capnp::word> serialized = qiskitc_to_jeff(circuit.get());

    capnp::FlatArrayMessageReader reader(serialized.asPtr());
    jeff::Module::Reader mod = reader.getRoot<jeff::Module>();

    auto operations = mod.getFunctions()[0].getDefinition().getBody().getOperations();
    ASSERT_EQ(operations.size(), num_qubits + 2) << "allocs + angle const + ppr gate";

    std::vector<uint32_t> qubit_values(num_qubits);
    for (uint32_t q = 0; q < num_qubits; q++)
        qubit_values[q] = operations[q].getOutputs()[0];

    jeff::Op::Reader angle_op = operations[num_qubits];
    auto angle_instr = angle_op.getInstruction();
    ASSERT_TRUE(angle_instr.isFloat());
    ASSERT_TRUE(angle_instr.getFloat().isConst64());
    EXPECT_EQ(angle_instr.getFloat().getConst64(), ppr_case.angle);
    const uint32_t angle_value = angle_op.getOutputs()[0];

    jeff::Op::Reader gate_op = operations[num_qubits + 1];
    auto instr = gate_op.getInstruction();
    ASSERT_TRUE(instr.isQubit());
    ASSERT_TRUE(instr.getQubit().isGate());

    jeff::QubitGate::Reader gate = instr.getQubit().getGate();
    ASSERT_TRUE(gate.isPpr());
    EXPECT_EQ(gate.getControlQubits(), 0);
    EXPECT_FALSE(gate.getAdjoint());
    EXPECT_EQ(gate.getPower(), 1);

    auto result_pauli = gate.getPpr().getPauliString();
    ASSERT_EQ(result_pauli.size(), num_qubits);
    for (uint32_t i = 0; i < num_qubits; i++) {
        EXPECT_EQ(result_pauli[i], ppr_case.pauli_string[i]) << "pauliString[" << i << "]";
    }

    auto inputs = gate_op.getInputs();
    ASSERT_EQ(inputs.size(), num_qubits + 1);
    for (uint32_t i = 0; i < num_qubits; i++) {
        EXPECT_EQ(inputs[i], qubit_values[i]) << "qubit input " << i;
    }
    EXPECT_EQ(inputs[num_qubits], angle_value) << "angle input";
}

INSTANTIATE_TEST_SUITE_P(
    Rotations, PauliProductRotationTest,
    ::testing::Values(PprCase{"III", {jeff::Pauli::I, jeff::Pauli::I, jeff::Pauli::I}, 0.7},
                      PprCase{"IXX", {jeff::Pauli::I, jeff::Pauli::X, jeff::Pauli::X}, 1.1},
                      PprCase{"IXZ", {jeff::Pauli::I, jeff::Pauli::X, jeff::Pauli::Z}, -0.3},
                      PprCase{"IIY", {jeff::Pauli::I, jeff::Pauli::I, jeff::Pauli::Y}, 2.4}),
    [](const ::testing::TestParamInfo<PprCase>& info) { return info.param.label; });

} // namespace jeff_qiskitc_test
