#pragma once

#include "capnp/jeff.capnp.h"

#include <qiskit.h>

#include <cstdint>
#include <map>
#include <memory>
#include <string>
#include <unordered_map>
#include <utility>
#include <variant>
#include <vector>

inline const std::unordered_map<jeff::WellKnownGate, QkGate> WellKnownToQkGateMap = {
    {jeff::WellKnownGate::GPHASE, QkGate_GlobalPhase},
    {jeff::WellKnownGate::I, QkGate_I},
    {jeff::WellKnownGate::X, QkGate_X},
    {jeff::WellKnownGate::Y, QkGate_Y},
    {jeff::WellKnownGate::Z, QkGate_Z},
    {jeff::WellKnownGate::S, QkGate_S},
    {jeff::WellKnownGate::T, QkGate_T},
    {jeff::WellKnownGate::R1, QkGate_Phase},
    {jeff::WellKnownGate::RX, QkGate_RX},
    {jeff::WellKnownGate::RY, QkGate_RY},
    {jeff::WellKnownGate::RZ, QkGate_RZ},
    {jeff::WellKnownGate::H, QkGate_H},
    {jeff::WellKnownGate::U, QkGate_U},
    {jeff::WellKnownGate::SWAP, QkGate_Swap},
};

inline const std::unordered_map<QkGate, jeff::WellKnownGate> QkGateToWellKnownMap = [] {
    std::unordered_map<QkGate, jeff::WellKnownGate> reverse;
    for (const auto& [well_known, qk_gate] : WellKnownToQkGateMap) {
        reverse.emplace(qk_gate, well_known);
    }
    return reverse;
}();

// Well-known gates whose adjoint is a different QkGate. Every other well-known gate is either
// self-inverse or inverted by negating its parameters, so it keeps its QkGate.
inline const std::unordered_map<QkGate, QkGate> AdjointQkGateMap = {
    {QkGate_S, QkGate_Sdg},
    {QkGate_T, QkGate_Tdg},
};

inline const std::unordered_map<QkGate, QkGate> QkGateToAdjointMap = [] {
    std::unordered_map<QkGate, QkGate> reverse;
    for (const auto& [qk_gate, adjoint_gate] : AdjointQkGateMap) {
        reverse.emplace(adjoint_gate, qk_gate);
    }
    return reverse;
}();

inline const std::map<std::pair<uint8_t, QkGate>, QkGate> ControlledQkGateMap = {
    {{1, QkGate_H}, QkGate_CH},         {{1, QkGate_X}, QkGate_CX},
    {{1, QkGate_Y}, QkGate_CY},         {{1, QkGate_Z}, QkGate_CZ},
    {{1, QkGate_Phase}, QkGate_CPhase}, {{1, QkGate_RX}, QkGate_CRX},
    {{1, QkGate_RY}, QkGate_CRY},       {{1, QkGate_RZ}, QkGate_CRZ},
    {{1, QkGate_S}, QkGate_CS},         {{1, QkGate_Sdg}, QkGate_CSdg},
    {{1, QkGate_SX}, QkGate_CSX},       {{1, QkGate_U}, QkGate_CU},
    {{1, QkGate_U1}, QkGate_CU1},       {{1, QkGate_U3}, QkGate_CU3},
    {{1, QkGate_Swap}, QkGate_CSwap},   {{2, QkGate_X}, QkGate_CCX},
    {{2, QkGate_Z}, QkGate_CCZ},        {{3, QkGate_X}, QkGate_C3X},
    {{3, QkGate_SX}, QkGate_C3SX},
};

inline const std::map<QkGate, std::pair<uint8_t, QkGate>> QkGateToControlledMap = [] {
    std::map<QkGate, std::pair<uint8_t, QkGate>> reverse;
    for (const auto& [key, controlled_gate] : ControlledQkGateMap) {
        reverse.emplace(controlled_gate, key);
    }
    return reverse;
}();

inline const std::unordered_map<std::string, QkGate> NameToQkGateMap = {
    {"global_phase", QkGate_GlobalPhase},
    {"h", QkGate_H},
    {"id", QkGate_I},
    {"x", QkGate_X},
    {"y", QkGate_Y},
    {"z", QkGate_Z},
    {"p", QkGate_Phase},
    {"rx", QkGate_RX},
    {"ry", QkGate_RY},
    {"rz", QkGate_RZ},
    {"s", QkGate_S},
    {"sdg", QkGate_Sdg},
    {"t", QkGate_T},
    {"tdg", QkGate_Tdg},
    {"u", QkGate_U},
    {"swap", QkGate_Swap},
    {"ch", QkGate_CH},
    {"cx", QkGate_CX},
    {"cy", QkGate_CY},
    {"cz", QkGate_CZ},
    {"cp", QkGate_CPhase},
    {"crx", QkGate_CRX},
    {"cry", QkGate_CRY},
    {"crz", QkGate_CRZ},
    {"cs", QkGate_CS},
    {"csdg", QkGate_CSdg},
    {"csx", QkGate_CSX},
    {"cu", QkGate_CU},
    {"cu1", QkGate_CU1},
    {"cu3", QkGate_CU3},
    {"cswap", QkGate_CSwap},
    {"ccx", QkGate_CCX},
    {"ccz", QkGate_CCZ},
    {"mcx", QkGate_C3X},
    {"c3sx", QkGate_C3SX},
};

namespace JeffToQiskit {

class WellKnownGate {
  public:
    explicit WellKnownGate(jeff::QubitGate::Reader gate);

    void operand_counts(uint32_t* num_qubits, uint32_t* num_params) const;

    bool to_gate(QkGate* gate) const;

    void emit(QkCircuit* circuit, std::vector<uint32_t> qubits, std::vector<double> params) const;

  private:
    jeff::QubitGate::Reader gate_;

    // The QkGate for this gate without its controls. A jeff controlled gate takes the same
    // float inputs as its uncontrolled form.
    bool uncontrolled_gate(QkGate* gate) const;

    void apply_adjoint(std::vector<double>& params) const;
};

class PauliProductRotationGate {
  public:
    explicit PauliProductRotationGate(jeff::QubitGate::Reader gate);

    void operand_counts(uint32_t* num_qubits, uint32_t* num_params) const;

    void emit(QkCircuit* circuit, std::vector<uint32_t> qubits, std::vector<double> params) const;

  private:
    jeff::QubitGate::Reader gate_;
    struct PauliRotation {
        std::unique_ptr<bool[]> z;
        std::unique_ptr<bool[]> x;
        std::unique_ptr<QkParam, decltype(&qk_param_free)> angle;
        QkPauliProductRotation rotation;
    };
    PauliRotation to_gate(const std::vector<double>& params) const;
};

class QubitGate {
  public:
    explicit QubitGate(jeff::QubitGate::Reader gate);

    void operand_counts(uint32_t* num_qubits, uint32_t* num_params) const;

    void emit(QkCircuit* circuit, std::vector<uint32_t> qubits, std::vector<double> params) const;

  private:
    std::variant<WellKnownGate, PauliProductRotationGate> gate_;
};

} // namespace JeffToQiskit

namespace QiskitToJeff {

// Converts a Qiskit gate parameter to the numeric value jeff stores. Symbolic (unbound)
// parameters have no jeff equivalent and are rejected.
double read_param(const QkParam* param, const char* context);

class WellKnownGate {
  public:
    explicit WellKnownGate(QkGate gate);

    // Number of float inputs jeff's gate takes. For CU this is 3: Qiskit's fourth parameter is
    // the phase returned by control_phase.
    uint32_t num_params() const;

    // The phase Qiskit applies only when the controls are |1>: CU's γ, and 0 for every other
    // gate. jeff's controlled u has no such phase, so it is emitted as a separate r1 on the
    // control qubit.
    double control_phase(const QkParam* const* params) const;

    bool to_gate(jeff::QubitGate::Builder gate) const;

    void emit(jeff::Op::Builder op) const;

  private:
    QkGate gate_;
};

class PauliProductRotationGate {
  public:
    explicit PauliProductRotationGate(const QkPauliProductRotation& gate);

    // The rotation angle in jeff's convention.
    double angle() const;

    bool to_gate(jeff::QubitGate::Builder gate) const;

    void emit(jeff::Op::Builder op) const;

  private:
    const QkPauliProductRotation* gate_;
};

} // namespace QiskitToJeff
