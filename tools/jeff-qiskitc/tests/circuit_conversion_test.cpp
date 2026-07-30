// Circuit-level round-trip tests: QkCircuit -> jeff (qiskitc_to_jeff) ->
// QkCircuit (jeff_to_qiskitc), checked instruction-by-instruction against
// the original. Unlike gate_conversion_test.cpp (one instruction at a
// time, isolating each gate/ppr mapping), these exercise the whole
// pipeline on realistic multi-instruction circuits -- SSA Value
// threading across many sequential ops on the same qubit, qubit/clbit
// allocation ordering across an entire program, counting passes sized
// correctly for more than one instruction.
//
// Covers three circuits: a Bell pair, a 10-qubit GHZ state, and a
// 5-qubit QFT (H/CPhase network + swaps) -- all built only from gates
// this converter supports (H, X via CX, Phase via CPhase, Swap, and
// measure), so a lossless round trip is expected: same qubit/clbit
// counts, same instruction count, and each instruction with the same
// name, qubits (in order), clbits, and param values.
//
// Compile: this is picked up automatically by CMakeLists.txt.
//   cmake --build build --target circuit_conversion_test
//   ./build/circuit_conversion_test

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

#include <qiskit.h>

#include <capnp/serialize.h>

#include "capnp/jeff.capnp.h"

#include "jeff_qiskitc.h"

namespace {

constexpr double kPi = 3.14159265358979323846;

int g_failures = 0;

void expect(bool cond, const std::string& what) {
  std::printf(cond ? "  ok   %s\n" : "  FAIL %s\n", what.c_str());
  if (!cond) g_failures++;
}

void print_circuit(const char* label, QkCircuit* qc) {
  std::printf("%s: qubits=%u clbits=%u instructions=%zu\n", label, qk_circuit_num_qubits(qc),
              qk_circuit_num_clbits(qc), qk_circuit_num_instructions(qc));
  for (size_t i = 0; i < qk_circuit_num_instructions(qc); i++) {
    QkCircuitInstruction inst;
    qk_circuit_get_instruction(qc, i, &inst);
    std::printf("  [%zu] %s qubits=(", i, inst.name);
    for (uint32_t q = 0; q < inst.num_qubits; q++) std::printf("%s%u", q ? "," : "", inst.qubits[q]);
    std::printf(") clbits=(");
    for (uint32_t c = 0; c < inst.num_clbits; c++) std::printf("%s%u", c ? "," : "", inst.clbits[c]);
    std::printf(") params=(");
    for (uint32_t p = 0; p < inst.num_params; p++) std::printf("%s%g", p ? "," : "", qk_param_as_real(inst.params[p]));
    std::printf(")\n");
    qk_circuit_instruction_clear(&inst);
  }
}

QkCircuit* build_bell_pair() {
  QkCircuit* qc = qk_circuit_new(2, 2);
  std::vector<uint32_t> h_qubits = {0};
  std::vector<uint32_t> cx_qubits = {0, 1};  // {control, target}
  qk_circuit_gate(qc, QkGate_H, h_qubits.data(), nullptr);
  qk_circuit_gate(qc, QkGate_CX, cx_qubits.data(), nullptr);
  qk_circuit_measure(qc, 0, 0);
  qk_circuit_measure(qc, 1, 1);
  return qc;
}

QkCircuit* build_ghz(uint32_t n) {
  QkCircuit* qc = qk_circuit_new(n, n);
  std::vector<uint32_t> h_qubits = {0};
  qk_circuit_gate(qc, QkGate_H, h_qubits.data(), nullptr);
  for (uint32_t i = 0; i + 1 < n; i++) {
    std::vector<uint32_t> cx_qubits = {i, i + 1};  // {control, target}
    qk_circuit_gate(qc, QkGate_CX, cx_qubits.data(), nullptr);
  }
  for (uint32_t i = 0; i < n; i++) {
    qk_circuit_measure(qc, i, i);
  }
  return qc;
}

// Standard QFT: for each qubit i, H(i) followed by a controlled phase
// rotation from every later qubit j, then a final swap network to
// reverse qubit order.
QkCircuit* build_qft(uint32_t n) {
  QkCircuit* qc = qk_circuit_new(n, n);
  for (uint32_t i = 0; i < n; i++) {
    std::vector<uint32_t> h_qubits = {i};
    qk_circuit_gate(qc, QkGate_H, h_qubits.data(), nullptr);
    for (uint32_t j = i + 1; j < n; j++) {
      double angle = kPi / static_cast<double>(1u << (j - i));
      std::vector<uint32_t> cphase_qubits = {j, i};  // {control, target}
      qk_circuit_gate(qc, QkGate_CPhase, cphase_qubits.data(), &angle);
    }
  }
  for (uint32_t i = 0; i < n / 2; i++) {
    std::vector<uint32_t> swap_qubits = {i, n - 1 - i};
    qk_circuit_gate(qc, QkGate_Swap, swap_qubits.data(), nullptr);
  }
  for (uint32_t i = 0; i < n; i++) {
    qk_circuit_measure(qc, i, i);
  }
  return qc;
}

// Checks that `roundtripped` (the result of running `original` through
// qiskitc_to_jeff then jeff_to_qiskitc) has the same qubit/clbit/
// instruction counts as `original`, and that every instruction matches
// name, qubits (in order), clbits, and param values.
void expect_same_circuit(QkCircuit* original, QkCircuit* roundtripped) {
  expect(qk_circuit_num_qubits(roundtripped) == qk_circuit_num_qubits(original), "same qubit count");
  expect(qk_circuit_num_clbits(roundtripped) == qk_circuit_num_clbits(original), "same clbit count");
  expect(qk_circuit_num_instructions(roundtripped) == qk_circuit_num_instructions(original),
         "same instruction count");

  size_t num_instructions = std::min(qk_circuit_num_instructions(original), qk_circuit_num_instructions(roundtripped));
  for (size_t i = 0; i < num_instructions; i++) {
    QkCircuitInstruction orig, rt;
    qk_circuit_get_instruction(original, i, &orig);
    qk_circuit_get_instruction(roundtripped, i, &rt);

    std::string what = "instruction[" + std::to_string(i) + "] (" + orig.name + ")";

    expect(std::string(rt.name) == std::string(orig.name), what + ": same name");
    expect(rt.num_qubits == orig.num_qubits, what + ": same qubit count");
    expect(rt.num_clbits == orig.num_clbits, what + ": same clbit count");
    expect(rt.num_params == orig.num_params, what + ": same param count");

    bool qubits_match = true;
    for (uint32_t q = 0; q < orig.num_qubits && q < rt.num_qubits; q++) {
      if (rt.qubits[q] != orig.qubits[q]) qubits_match = false;
    }
    expect(qubits_match, what + ": same qubits, in the same order");

    bool clbits_match = true;
    for (uint32_t c = 0; c < orig.num_clbits && c < rt.num_clbits; c++) {
      if (rt.clbits[c] != orig.clbits[c]) clbits_match = false;
    }
    expect(clbits_match, what + ": same clbits, in the same order");

    bool params_match = true;
    for (uint32_t p = 0; p < orig.num_params && p < rt.num_params; p++) {
      if (qk_param_as_real(rt.params[p]) != qk_param_as_real(orig.params[p])) params_match = false;
    }
    expect(params_match, what + ": same param values");

    qk_circuit_instruction_clear(&orig);
    qk_circuit_instruction_clear(&rt);
  }
}

// Runs `original` through qiskitc_to_jeff then jeff_to_qiskitc, entirely
// in memory (capnp::FlatArrayMessageReader over the serialized bytes, no
// file involved -- see the earlier discussion on why qiskitc_to_jeff
// returns flat bytes rather than a Builder/Reader directly), and checks
// the round-tripped circuit against the original. Takes ownership of
// `original` (frees it).
void test_round_trip(const char* label, QkCircuit* original) {
  std::printf("%s:\n", label);
  print_circuit("  original", original);

  kj::Array<capnp::word> serialized = qiskitc_to_jeff(original);

  capnp::FlatArrayMessageReader reader(serialized.asPtr());
  jeff::Module::Reader module = reader.getRoot<jeff::Module>();

  QkCircuit* roundtripped = jeff_to_qiskitc(module);
  print_circuit("  roundtripped", roundtripped);

  expect_same_circuit(original, roundtripped);

  qk_circuit_free(original);
  qk_circuit_free(roundtripped);
}

}  // namespace

int main() {
  test_round_trip("Bell pair", build_bell_pair());
  test_round_trip("GHZ(10)", build_ghz(10));
  test_round_trip("QFT(5)", build_qft(5));

  std::printf("\n%d failure(s)\n", g_failures);
  return g_failures == 0 ? 0 : 1;
}
