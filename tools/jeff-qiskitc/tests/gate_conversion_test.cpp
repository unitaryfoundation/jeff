// Tests for both jeff <-> QkCircuit directions (jeff_to_qiskitc,
// qiskitc_to_jeff). Each test builds one gate/ppr op directly and checks
// the single result -- no round-tripping through the other direction.
//
// Covers every gate in WellKnownToQkGateMap/ControlledQkGateMap plus a
// few Pauli product rotations.
//
//   cmake --build build --target gate_conversion_test
//   ./build/tests/gate_conversion_test

#include <cstdio>
#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

#include <qiskit.h>

#include <capnp/message.h>
#include <capnp/pretty-print.h>
#include <capnp/serialize.h>

#include "capnp/jeff.capnp.h"

#include "jeff_qiskitc.h"
#include "../lib/gate_converter.h"

namespace {

int g_failures = 0;

void expect(bool cond, const std::string& what) {
  std::printf(cond ? "  ok   %s\n" : "  FAIL %s\n", what.c_str());
  if (!cond) g_failures++;
}

// QkGate -> Qiskit instruction name, reversed from NameToQkGateMap.
const std::unordered_map<QkGate, std::string> kQkGateNames = [] {
  std::unordered_map<QkGate, std::string> reverse;
  for (const auto& [name, qk_gate] : NameToQkGateMap) reverse.emplace(qk_gate, name);
  return reverse;
}();

// Builds a jeff::Module with one function: num_qubits qubit allocs, one
// FloatOp.const64 per entry in params, then a single QubitGate op
// (configured by configure_gate) consuming all of them.
jeff::Module::Reader build_single_gate_module(capnp::MessageBuilder& message, uint32_t num_qubits,
                                               const std::vector<double>& params,
                                               const std::function<void(jeff::QubitGate::Builder)>& configure_gate) {
  uint32_t num_floats = static_cast<uint32_t>(params.size());
  uint32_t num_values = num_qubits * 2 + num_floats;
  uint32_t num_ops = num_qubits + num_floats + 1;

  jeff::Module::Builder module = message.initRoot<jeff::Module>();
  module.setVersion(0);
  module.setVersionMinor(3);
  module.setVersionPatch(0);
  module.setEntrypoint(0);
  module.initStrings(1).set(0, "gate_conversion_test");

  jeff::Function::Builder fn = module.initFunctions(1)[0];
  fn.setName(0);
  jeff::Function::Definition::Builder def = fn.initDefinition();

  auto values = def.initValues(num_values);
  for (uint32_t i = 0; i < num_qubits * 2; i++) {
    values[i].initType().setQubit();
  }
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
  for (uint32_t q = 0; q < num_qubits; q++) gate_op.getInputs().set(q, input_qubits[q]);
  for (uint32_t i = 0; i < num_floats; i++) gate_op.getInputs().set(num_qubits + i, input_floats[i]);

  gate_op.initOutputs(num_qubits);
  for (uint32_t q = 0; q < num_qubits; q++) gate_op.getOutputs().set(q, next_value++);

  configure_gate(gate_op.getInstruction().initQubit().initGate());

  jeff::Module::Reader reader = module.asReader();
  std::printf("--- jeff module for this test ---\n%s\n", capnp::prettyPrint(reader).flatten().cStr());
  return reader;
}

// Builds a QkCircuit with num_qubits qubits and one qk_gate instruction
// on physical qubits {0..num_qubits-1} ({controls..., targets...}).
QkCircuit* build_single_gate_circuit(QkGate qk_gate, uint32_t num_qubits, const std::vector<double>& params) {
  QkCircuit* qc = qk_circuit_new(num_qubits, 0);
  std::vector<uint32_t> qubits(num_qubits);
  for (uint32_t i = 0; i < num_qubits; i++) qubits[i] = i;
  qk_circuit_gate(qc, qk_gate, qubits.data(), params.empty() ? nullptr : params.data());
  return qc;
}

// jeff_to_qiskitc: a wellKnown gate maps to expected_gate, with the
// right name, qubit order, and params.
void test_gate(jeff::WellKnownGate well_known, uint8_t control_qubits, QkGate expected_gate) {
  const std::string& name = kQkGateNames.at(expected_gate);
  std::printf("%s (controlQubits=%u):\n", name.c_str(), control_qubits);

  uint32_t num_qubits = qk_gate_num_qubits(expected_gate);
  uint32_t num_targets = num_qubits - control_qubits;
  uint32_t num_params = qk_gate_num_params(expected_gate);
  std::vector<double> params(num_params);
  for (uint32_t i = 0; i < num_params; i++) params[i] = 0.5 + i;  // distinct, nonzero test values

  capnp::MallocMessageBuilder message;
  jeff::Module::Reader module =
      build_single_gate_module(message, num_qubits, params, [&](jeff::QubitGate::Builder gate) {
        gate.setWellKnown(well_known);
        gate.setControlQubits(control_qubits);
        gate.setAdjoint(false);
        gate.setPower(1);
      });

  QkCircuit* circuit = jeff_to_qiskitc(module);

  expect(qk_circuit_num_qubits(circuit) == num_qubits, "circuit has the right number of qubits");
  expect(qk_circuit_num_instructions(circuit) == 1, "exactly one instruction");

  QkCircuitInstruction inst;
  qk_circuit_get_instruction(circuit, 0, &inst);
  expect(std::string(inst.name) == name, "instruction name is \"" + name + "\"");
  expect(inst.num_qubits == num_qubits, "instruction has the right number of qubits");

  // jeff orders qubits {targets..., controls...}; Qiskit wants {controls..., targets...}.
  bool qubits_in_order = true;
  for (uint32_t i = 0; i < control_qubits; i++) {
    if (inst.qubits[i] != num_targets + i) qubits_in_order = false;
  }
  for (uint32_t i = 0; i < num_targets; i++) {
    if (inst.qubits[control_qubits + i] != i) qubits_in_order = false;
  }
  expect(qubits_in_order, "instruction qubits are {controls..., targets...}");

  expect(inst.num_params == num_params, "instruction has the right number of params");
  bool params_match = true;
  for (uint32_t i = 0; i < num_params; i++) {
    if (qk_param_as_real(inst.params[i]) != params[i]) params_match = false;
  }
  expect(params_match, "instruction params match what was fed in");

  qk_circuit_instruction_clear(&inst);
  qk_circuit_free(circuit);
}

// qiskitc_to_jeff: a QkGate produces expected_well_known, with the
// alloc/const64/gate ops in the right slots and order.
void test_gate_reverse(QkGate qk_gate, uint8_t control_qubits, jeff::WellKnownGate expected_well_known) {
  const std::string& name = kQkGateNames.at(qk_gate);
  std::printf("%s (controlQubits=%u) [reverse]:\n", name.c_str(), control_qubits);

  uint32_t num_qubits = qk_gate_num_qubits(qk_gate);
  uint32_t num_targets = num_qubits - control_qubits;
  uint32_t num_params = qk_gate_num_params(qk_gate);
  std::vector<double> params(num_params);
  for (uint32_t i = 0; i < num_params; i++) params[i] = 0.5 + i;  // distinct, nonzero test values

  QkCircuit* circuit = build_single_gate_circuit(qk_gate, num_qubits, params);
  kj::Array<capnp::word> serialized = qiskitc_to_jeff(circuit);
  qk_circuit_free(circuit);

  capnp::FlatArrayMessageReader reader(serialized.asPtr());
  jeff::Module::Reader module = reader.getRoot<jeff::Module>();
  std::printf("--- jeff module for this test ---\n%s\n", capnp::prettyPrint(module).flatten().cStr());

  auto operations = module.getFunctions()[0].getDefinition().getBody().getOperations();
  expect(operations.size() == num_qubits + num_params + 1, "right number of Ops (allocs + param consts + gate)");

  // operations[0..num_qubits) are the qubit allocs, output q = physical qubit q.
  std::vector<uint32_t> qubit_values(num_qubits);
  for (uint32_t q = 0; q < num_qubits; q++) {
    qubit_values[q] = operations[q].getOutputs()[0];
  }

  bool params_match = true;
  std::vector<uint32_t> float_values(num_params);
  for (uint32_t i = 0; i < num_params; i++) {
    jeff::Op::Reader op = operations[num_qubits + i];
    float_values[i] = op.getOutputs()[0];
    auto instr = op.getInstruction();
    if (!instr.isFloat() || !instr.getFloat().isConst64() || instr.getFloat().getConst64() != params[i]) {
      params_match = false;
    }
  }
  expect(params_match, "param FloatOp.const64 values match what was fed in");

  jeff::Op::Reader gate_op = operations[num_qubits + num_params];
  auto instr = gate_op.getInstruction();
  expect(instr.isQubit() && instr.getQubit().isGate(), "last op is a QubitOp.gate");

  jeff::QubitGate::Reader gate = instr.getQubit().getGate();
  expect(gate.isWellKnown() && gate.getWellKnown() == expected_well_known, "gate is the expected wellKnown value");
  expect(gate.getControlQubits() == control_qubits, "gate has the right controlQubits");
  expect(!gate.getAdjoint(), "gate is not adjoint");
  expect(gate.getPower() == 1, "gate has power 1");

  auto inputs = gate_op.getInputs();
  expect(inputs.size() == num_qubits + num_params, "gate op has the right number of inputs");

  // Qiskit built {controls..., targets...}; jeff wants {targets..., controls...}.
  bool qubits_in_order = true;
  for (uint32_t i = 0; i < num_targets; i++) {
    if (inputs[i] != qubit_values[control_qubits + i]) qubits_in_order = false;
  }
  for (uint32_t i = 0; i < control_qubits; i++) {
    if (inputs[num_targets + i] != qubit_values[i]) qubits_in_order = false;
  }
  expect(qubits_in_order, "gate op's qubit inputs are {targets..., controls...}, referencing the alloc Values");

  bool float_inputs_match = true;
  for (uint32_t i = 0; i < num_params; i++) {
    if (inputs[num_qubits + i] != float_values[i]) float_inputs_match = false;
  }
  expect(float_inputs_match, "gate op's float inputs reference the param FloatOp Values");
}

// jeff_to_qiskitc: a ppr gate produces a matching QkPauliProductRotation.
void test_ppr(const char* label, const std::vector<jeff::Pauli>& pauli_string, double angle) {
  std::printf("ppr %s:\n", label);

  uint32_t num_qubits = static_cast<uint32_t>(pauli_string.size());

  capnp::MallocMessageBuilder message;
  jeff::Module::Reader module =
      build_single_gate_module(message, num_qubits, {angle}, [&](jeff::QubitGate::Builder gate) {
        auto pauli_list = gate.initPpr().initPauliString(static_cast<unsigned int>(pauli_string.size()));
        for (size_t i = 0; i < pauli_string.size(); i++) {
          pauli_list.set(i, pauli_string[i]);
        }
        gate.setControlQubits(0);
        gate.setAdjoint(false);
        gate.setPower(1);
      });

  QkCircuit* circuit = jeff_to_qiskitc(module);

  expect(qk_circuit_num_instructions(circuit) == 1, "exactly one instruction");
  expect(qk_circuit_instruction_kind(circuit, 0) == QkOperationKind_PauliProductRotation,
         "instruction kind is PauliProductRotation");

  QkPauliProductRotation rotation;
  qk_circuit_inst_pauli_product_rotation(circuit, 0, &rotation);

  expect(rotation.len == num_qubits, "rotation has the right length");
  bool zx_match = true;
  for (uint32_t i = 0; i < num_qubits; i++) {
    bool expected_z = false, expected_x = false;
    switch (pauli_string[i]) {
      case jeff::Pauli::I:
        break;
      case jeff::Pauli::X:
        expected_x = true;
        break;
      case jeff::Pauli::Z:
        expected_z = true;
        break;
      case jeff::Pauli::Y:
        expected_z = true;
        expected_x = true;
        break;
    }
    if (rotation.z[i] != expected_z || rotation.x[i] != expected_x) zx_match = false;
  }
  expect(zx_match, "z/x arrays match the Pauli string");
  expect(qk_param_as_real(rotation.angle) == angle, "angle matches");

  qk_pauli_product_rotation_clear(&rotation);
  qk_circuit_free(circuit);
}

// qiskitc_to_jeff: a QkPauliProductRotation produces a matching ppr gate op.
void test_ppr_reverse(const char* label, const std::vector<jeff::Pauli>& pauli_string, double angle) {
  std::printf("ppr %s [reverse]:\n", label);

  uint32_t num_qubits = static_cast<uint32_t>(pauli_string.size());
  auto z = std::make_unique<bool[]>(num_qubits);
  auto x = std::make_unique<bool[]>(num_qubits);
  for (uint32_t i = 0; i < num_qubits; i++) {
    switch (pauli_string[i]) {
      case jeff::Pauli::I:
        z[i] = false;
        x[i] = false;
        break;
      case jeff::Pauli::X:
        z[i] = false;
        x[i] = true;
        break;
      case jeff::Pauli::Z:
        z[i] = true;
        x[i] = false;
        break;
      case jeff::Pauli::Y:
        z[i] = true;
        x[i] = true;
        break;
    }
  }
  std::unique_ptr<QkParam, decltype(&qk_param_free)> angle_param(qk_param_from_double(angle), qk_param_free);
  QkPauliProductRotation rotation{z.get(), x.get(), num_qubits, angle_param.get()};

  QkCircuit* circuit = qk_circuit_new(num_qubits, 0);
  std::vector<uint32_t> qubits(num_qubits);
  for (uint32_t i = 0; i < num_qubits; i++) qubits[i] = i;
  qk_circuit_pauli_product_rotation(circuit, &rotation, qubits.data());

  kj::Array<capnp::word> serialized = qiskitc_to_jeff(circuit);
  qk_circuit_free(circuit);

  capnp::FlatArrayMessageReader reader(serialized.asPtr());
  jeff::Module::Reader module = reader.getRoot<jeff::Module>();
  std::printf("--- jeff module for this test ---\n%s\n", capnp::prettyPrint(module).flatten().cStr());

  auto operations = module.getFunctions()[0].getDefinition().getBody().getOperations();
  expect(operations.size() == num_qubits + 2, "right number of Ops (allocs + angle const + ppr gate)");

  std::vector<uint32_t> qubit_values(num_qubits);
  for (uint32_t q = 0; q < num_qubits; q++) qubit_values[q] = operations[q].getOutputs()[0];

  jeff::Op::Reader angle_op = operations[num_qubits];
  auto angle_instr = angle_op.getInstruction();
  expect(angle_instr.isFloat() && angle_instr.getFloat().isConst64() && angle_instr.getFloat().getConst64() == angle,
         "angle FloatOp.const64 matches");
  uint32_t angle_value = angle_op.getOutputs()[0];

  jeff::Op::Reader gate_op = operations[num_qubits + 1];
  auto instr = gate_op.getInstruction();
  expect(instr.isQubit() && instr.getQubit().isGate(), "last op is a QubitOp.gate");

  jeff::QubitGate::Reader gate = instr.getQubit().getGate();
  expect(gate.isPpr(), "gate is a ppr");
  expect(gate.getControlQubits() == 0, "ppr has no control qubits");
  expect(!gate.getAdjoint(), "ppr is not adjoint");
  expect(gate.getPower() == 1, "ppr has power 1");

  auto result_pauli = gate.getPpr().getPauliString();
  expect(result_pauli.size() == num_qubits, "pauliString has the right length");
  bool pauli_match = true;
  for (uint32_t i = 0; i < num_qubits; i++) {
    if (result_pauli[i] != pauli_string[i]) pauli_match = false;
  }
  expect(pauli_match, "pauliString matches");

  auto inputs = gate_op.getInputs();
  expect(inputs.size() == num_qubits + 1, "ppr gate op has the right number of inputs");
  bool qubits_match = true;
  for (uint32_t i = 0; i < num_qubits; i++) {
    if (inputs[i] != qubit_values[i]) qubits_match = false;
  }
  expect(qubits_match, "ppr gate op's qubit inputs reference the alloc Values in order");
  expect(inputs[num_qubits] == angle_value, "ppr gate op's angle input references the angle FloatOp Value");
}

}  // namespace

int main() {
  for (const auto& [well_known, qk_gate] : WellKnownToQkGateMap) {
    test_gate(well_known, /*control_qubits=*/0, qk_gate);
    test_gate_reverse(qk_gate, /*control_qubits=*/0, well_known);
  }

  for (const auto& [key, controlled_gate] : ControlledQkGateMap) {
    const auto& [control_qubits, base_gate] = key;
    // Some ControlledQkGateMap entries (Sdg, SX, U1, U3, ...) have no jeff WellKnownGate -- skip those.
    auto well_known_it = QkGateToWellKnownMap.find(base_gate);
    if (well_known_it == QkGateToWellKnownMap.end()) {
      std::printf("%s (controlQubits=%u): skipped, base QkGate has no jeff WellKnownGate\n",
                  kQkGateNames.at(controlled_gate).c_str(), control_qubits);
      continue;
    }
    test_gate(well_known_it->second, control_qubits, controlled_gate);
    test_gate_reverse(controlled_gate, control_qubits, well_known_it->second);
  }

  test_ppr("III", {jeff::Pauli::I, jeff::Pauli::I, jeff::Pauli::I}, 0.7);
  test_ppr("IXX", {jeff::Pauli::I, jeff::Pauli::X, jeff::Pauli::X}, 1.1);
  test_ppr("IXZ", {jeff::Pauli::I, jeff::Pauli::X, jeff::Pauli::Z}, -0.3);
  test_ppr("IIY", {jeff::Pauli::I, jeff::Pauli::I, jeff::Pauli::Y}, 2.4);

  test_ppr_reverse("III", {jeff::Pauli::I, jeff::Pauli::I, jeff::Pauli::I}, 0.7);
  test_ppr_reverse("IXX", {jeff::Pauli::I, jeff::Pauli::X, jeff::Pauli::X}, 1.1);
  test_ppr_reverse("IXZ", {jeff::Pauli::I, jeff::Pauli::X, jeff::Pauli::Z}, -0.3);
  test_ppr_reverse("IIY", {jeff::Pauli::I, jeff::Pauli::I, jeff::Pauli::Y}, 2.4);

  std::printf("\n%d failure(s)\n", g_failures);
  return g_failures == 0 ? 0 : 1;
}
