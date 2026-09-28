#pragma once

#include <gtest/gtest.h>
#include <qiskit.h>

#include <cstdint>
#include <functional>
#include <memory>
#include <numbers>
#include <ostream>
#include <string>
#include <vector>

namespace jeff_qiskitc_test {

// QkCircuit/QkCircuitInstruction are C handles that must be released
// explicitly. GoogleTest's ASSERT_* macros return early from the test body,
// which would skip a manual qk_*_free/clear call, so wrap them in RAII types
// instead.
struct CircuitDeleter {
    void operator()(QkCircuit* circuit) const { qk_circuit_free(circuit); }
};

using CircuitPtr = std::unique_ptr<QkCircuit, CircuitDeleter>;

class ScopedInstruction {
  public:
    ScopedInstruction(const QkCircuit* circuit, size_t index) {
        qk_circuit_get_instruction(circuit, index, &inst_);
    }
    ~ScopedInstruction() { qk_circuit_instruction_clear(&inst_); }

    ScopedInstruction(const ScopedInstruction&) = delete;
    ScopedInstruction& operator=(const ScopedInstruction&) = delete;

    const QkCircuitInstruction& operator*() const { return inst_; }
    const QkCircuitInstruction* operator->() const { return &inst_; }

  private:
    QkCircuitInstruction inst_;
};

// Circuits built only from gates this converter supports, so a lossless
// round trip is expected.
inline CircuitPtr build_bell_pair() {
    CircuitPtr qc(qk_circuit_new(2, 2));
    std::vector<uint32_t> h_qubits = {0};
    std::vector<uint32_t> cx_qubits = {0, 1}; // {control, target}
    qk_circuit_gate(qc.get(), QkGate_H, h_qubits.data(), nullptr);
    qk_circuit_gate(qc.get(), QkGate_CX, cx_qubits.data(), nullptr);
    qk_circuit_measure(qc.get(), 0, 0);
    qk_circuit_measure(qc.get(), 1, 1);
    return qc;
}

inline CircuitPtr build_ghz(uint32_t n) {
    CircuitPtr qc(qk_circuit_new(n, n));
    std::vector<uint32_t> h_qubits = {0};
    qk_circuit_gate(qc.get(), QkGate_H, h_qubits.data(), nullptr);
    for (uint32_t i = 0; i + 1 < n; i++) {
        std::vector<uint32_t> cx_qubits = {i, i + 1}; // {control, target}
        qk_circuit_gate(qc.get(), QkGate_CX, cx_qubits.data(), nullptr);
    }
    for (uint32_t i = 0; i < n; i++)
        qk_circuit_measure(qc.get(), i, i);
    return qc;
}

// Standard QFT: H(i) then a controlled phase from every later qubit j,
// then a swap network to reverse qubit order.
inline CircuitPtr build_qft(uint32_t n) {
    CircuitPtr qc(qk_circuit_new(n, n));
    for (uint32_t i = 0; i < n; i++) {
        std::vector<uint32_t> h_qubits = {i};
        qk_circuit_gate(qc.get(), QkGate_H, h_qubits.data(), nullptr);
        for (uint32_t j = i + 1; j < n; j++) {
            double angle = std::numbers::pi / static_cast<double>(1u << (j - i));
            std::vector<uint32_t> cphase_qubits = {j, i}; // {control, target}
            qk_circuit_gate(qc.get(), QkGate_CPhase, cphase_qubits.data(), &angle);
        }
    }
    for (uint32_t i = 0; i < n / 2; i++) {
        std::vector<uint32_t> swap_qubits = {i, n - 1 - i};
        qk_circuit_gate(qc.get(), QkGate_Swap, swap_qubits.data(), nullptr);
    }
    for (uint32_t i = 0; i < n; i++)
        qk_circuit_measure(qc.get(), i, i);
    return qc;
}

// Shared by the in-memory and through-a-file round-trip tests.
struct CircuitCase {
    std::string name;
    std::function<CircuitPtr()> build;
};

// CMake's gtest_discover_tests names each ctest entry after the printed
// parameter, so without this the test names are raw byte dumps.
inline void PrintTo(const CircuitCase& circuit_case, std::ostream* os) { *os << circuit_case.name; }

inline std::vector<CircuitCase> circuit_cases() {
    return {
        {"BellPair", [] { return build_bell_pair(); }},
        {"GHZ10", [] { return build_ghz(10); }},
        {"QFT5", [] { return build_qft(5); }},
    };
}

inline std::string circuit_case_name(const ::testing::TestParamInfo<CircuitCase>& info) {
    return info.param.name;
}

// Checks roundtripped matches original: same qubit/clbit/instruction counts,
// and each instruction's name, qubits (in order), clbits, and params.
inline void expect_same_circuit(const QkCircuit* original, const QkCircuit* roundtripped) {
    EXPECT_EQ(qk_circuit_num_qubits(roundtripped), qk_circuit_num_qubits(original));
    EXPECT_EQ(qk_circuit_num_clbits(roundtripped), qk_circuit_num_clbits(original));
    ASSERT_EQ(qk_circuit_num_instructions(roundtripped), qk_circuit_num_instructions(original));

    for (size_t i = 0; i < qk_circuit_num_instructions(original); i++) {
        const ScopedInstruction orig(original, i);
        const ScopedInstruction rt(roundtripped, i);

        SCOPED_TRACE("instruction[" + std::to_string(i) + "] (" + orig->name + ")");

        EXPECT_STREQ(rt->name, orig->name);
        ASSERT_EQ(rt->num_qubits, orig->num_qubits);
        ASSERT_EQ(rt->num_clbits, orig->num_clbits);
        ASSERT_EQ(rt->num_params, orig->num_params);

        for (uint32_t q = 0; q < orig->num_qubits; q++) {
            EXPECT_EQ(rt->qubits[q], orig->qubits[q]) << "qubit " << q;
        }
        for (uint32_t c = 0; c < orig->num_clbits; c++) {
            EXPECT_EQ(rt->clbits[c], orig->clbits[c]) << "clbit " << c;
        }
        for (uint32_t p = 0; p < orig->num_params; p++) {
            EXPECT_EQ(qk_param_as_real(rt->params[p]), qk_param_as_real(orig->params[p]))
                << "param " << p;
        }
    }
}

} // namespace jeff_qiskitc_test
