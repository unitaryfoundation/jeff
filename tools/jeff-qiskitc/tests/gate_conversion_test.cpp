// Unit tests for the jeff -> QkCircuit direction (jeff_to_qiskitc). Each
// test hand-builds a minimal jeff::Module directly via capnp Builders and
// checks the single resulting QkCircuit instruction.
//
// Covers every wellKnown gate (uncontrolled, at its own minimum qubit
// count) and every controlled gate, both driven directly off
// WellKnownToQkGateMap/ControlledQkGateMap so the gate lists only live in
// one place, plus a handful of Pauli product rotations.
//
// Compile: this is picked up automatically by CMakeLists.txt.
//   cmake --build build --target gate_conversion_test
//   ./build/tests/gate_conversion_test

#include <cstdio>
#include <cstdint>
#include <functional>
#include <string>
#include <unordered_map>
#include <vector>

#include <qiskit.h>

#include <capnp/message.h>
#include <capnp/pretty-print.h>

#include "capnp/jeff.capnp.h"

#include "jeff_qiskitc.h"
#include "../lib/gate_converter.h"

namespace {

int g_failures = 0;

void expect(bool cond, const std::string& what) {
    std::printf(cond ? "  ok   %s\n" : "  FAIL %s\n", what.c_str());
    if (!cond) g_failures++;
}

const std::unordered_map<QkGate, std::string> kQkGateNames = [] {
    std::unordered_map<QkGate, std::string> reverse;
    for (const auto& [name, qk_gate] : NameToQkGateMap) {
        reverse.emplace(qk_gate, name);
    }
    return reverse;
}();

jeff::Module::Reader build_single_gate_module(
    capnp::MessageBuilder& message,
    uint32_t num_qubits,
    const std::vector<double>& params,
    const std::function<void(jeff::QubitGate::Builder)>& configure_gate)
{
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

// Runs a jeff wellKnown gate (with the given controlQubits) through
// jeff_to_qiskitc and checks the resulting QkCircuit has exactly one
// instruction with the right name, qubit count, qubit order (targets
// first in jeff, but reordered to controls-first for a controlled gate),
// and param values. `expected_gate` is the QkGate the (well_known,
// control_qubits) combination is expected to resolve to.
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

  // build_single_gate_module allocates+feeds qubits as {targets...,
  // controls...} (jeff's own order); Qiskit wants {controls..., targets...}.
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

// Applies a ppr gate with the given Pauli string and angle, and checks the
// resulting QkCircuit has exactly one QkPauliProductRotation instruction
// with the right z/x arrays and angle.
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

}  // namespace

int main() {
    for (const auto& [well_known, qk_gate] : WellKnownToQkGateMap) {
      test_gate(well_known, /*control_qubits=*/0, qk_gate);
    }

    for (const auto& [key, controlled_gate] : ControlledQkGateMap) {
        const auto& [control_qubits, base_gate] = key;
        // ControlledQkGateMap has entries (e.g. Sdg, SX, U1, U3) whose base
        // gate has no jeff WellKnownGate at all -- those combinations can
        // never actually be produced by to_gate(), so skip them here too.
        auto well_known_it = QkGateToWellKnownMap.find(base_gate);
        if (well_known_it == QkGateToWellKnownMap.end()) {
            std::printf("%s (controlQubits=%u): skipped, base QkGate has no jeff WellKnownGate\n",
                        kQkGateNames.at(controlled_gate).c_str(), control_qubits);
            continue;
        }
        test_gate(well_known_it->second, control_qubits, controlled_gate);
    }

    test_ppr("III", {jeff::Pauli::I, jeff::Pauli::I, jeff::Pauli::I}, 0.7);
    test_ppr("IXX", {jeff::Pauli::I, jeff::Pauli::X, jeff::Pauli::X}, 1.1);
    test_ppr("IXZ", {jeff::Pauli::I, jeff::Pauli::X, jeff::Pauli::Z}, -0.3);
    test_ppr("IIY", {jeff::Pauli::I, jeff::Pauli::I, jeff::Pauli::Y}, 2.4);

    std::printf("\n%d failure(s)\n", g_failures);
    return g_failures == 0 ? 0 : 1;
}
