// Round-trip tests for the .jeff-file wrapper functions:
// QkCircuit -> qiskitc_to_jeff_file -> (real file on disk) ->
// jeff_file_to_qiskitc -> QkCircuit, checked instruction-by-instruction
// against the original.
//
// Unlike circuit_conversion_test.cpp (which round-trips through the
// in-memory Reader/Array<word> API), this exercises the actual file I/O
// path: open/write/close then open/read/close via real file descriptors.
//
//   cmake --build build --target file_conversion_test
//   ./build/tests/file_conversion_test

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include <unistd.h>

#include <qiskit.h>

#include "jeff_qiskitc.h"

namespace {

int g_failures = 0;

void expect(bool cond, const std::string& what) {
  std::printf(cond ? "  ok   %s\n" : "  FAIL %s\n", what.c_str());
  if (!cond) g_failures++;
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

// Checks roundtripped matches original: same qubit/clbit/instruction
// counts, and each instruction's name, qubits (in order), clbits, and params.
void expect_same_circuit(QkCircuit* original, QkCircuit* roundtripped) {
  expect(qk_circuit_num_qubits(roundtripped) == qk_circuit_num_qubits(original), "same qubit count");
  expect(qk_circuit_num_clbits(roundtripped) == qk_circuit_num_clbits(original), "same clbit count");
  expect(qk_circuit_num_instructions(roundtripped) == qk_circuit_num_instructions(original),
         "same instruction count");

  size_t num_instructions = qk_circuit_num_instructions(original);
  for (size_t i = 0; i < num_instructions && i < qk_circuit_num_instructions(roundtripped); i++) {
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

    qk_circuit_instruction_clear(&orig);
    qk_circuit_instruction_clear(&rt);
  }
}

// Runs original through qiskitc_to_jeff_file then jeff_file_to_qiskitc via
// a real temp file and checks the result against it. Takes ownership of
// original (frees it).
void test_file_round_trip(const char* label, QkCircuit* original) {
  std::printf("%s:\n", label);

  char path_template[] = "/tmp/jeff_qiskitc_test_XXXXXX";
  int fd = mkstemp(path_template);
  expect(fd >= 0, "created temp file");
  close(fd);
  std::string path(path_template);

  qiskitc_to_jeff_file(original, path);

  QkCircuit* roundtripped = jeff_file_to_qiskitc(path);
  expect_same_circuit(original, roundtripped);

  unlink(path.c_str());
  qk_circuit_free(original);
  qk_circuit_free(roundtripped);
}

}  // namespace

int main() {
  test_file_round_trip("Bell pair via file", build_bell_pair());

  std::printf("\n%d failure(s)\n", g_failures);
  return g_failures == 0 ? 0 : 1;
}
