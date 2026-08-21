#include "gate_converter.h"

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <memory>


namespace JeffToQiskit{

WellKnownGate::WellKnownGate(jeff::QubitGate::Reader gate) : gate_(gate) {}

void WellKnownGate::operand_counts(
    uint32_t* num_qubits,
    uint32_t* num_params
) const {
    QkGate qk_gate;
    if (!to_gate(&qk_gate)) {
        std::fprintf(stderr, "WellKnownGate::operand_counts: unrecognized wellKnown value or no matching QkGate\n");
        std::exit(1);
    }
    *num_qubits = qk_gate_num_qubits(qk_gate);
    *num_params = qk_gate_num_params(qk_gate);
}

bool WellKnownGate::to_gate(QkGate* gate) const {
    auto well_known_it = WellKnownToQkGateMap.find(gate_.getWellKnown());
    if (well_known_it == WellKnownToQkGateMap.end()) {
        return false;
    }
    QkGate base_gate = well_known_it->second;

    uint8_t control_qubits = gate_.getControlQubits();
    if (control_qubits == 0) {
        *gate = base_gate;
        return true;
    }

    auto controlled_it = ControlledQkGateMap.find({control_qubits, base_gate});
    if (controlled_it == ControlledQkGateMap.end()) {
        return false;
    }
    *gate = controlled_it->second;
    return true;
}

void WellKnownGate::emit(
    QkCircuit* circuit,
    std::vector<uint32_t> qubits,
    std::vector<double> params
) const {
    QkGate qk_gate;
    if (!to_gate(&qk_gate)) {
        std::fprintf(
            stderr,
            "WellKnownGate::emit: unrecognized wellKnown value or no matching QkGate\n"
        );
        std::exit(1);
    }

    if (qubits.size() != qk_gate_num_qubits(qk_gate)) {
        std::fprintf(
            stderr,
            "WellKnownGate::emit: expected %u qubits for this QkGate, got %zu\n",
            qk_gate_num_qubits(qk_gate),
            qubits.size()
        );
        std::exit(1);
    }
    if (params.size() != qk_gate_num_params(qk_gate)) {
        std::fprintf(
            stderr,
            "WellKnownGate::emit: expected %u params for this QkGate, got %zu\n",
            qk_gate_num_params(qk_gate),
            params.size()
        );
        std::exit(1);
    }


    uint8_t control_qubits = gate_.getControlQubits();
    std::rotate(
        qubits.begin(),
        qubits.begin() + (qubits.size() - control_qubits),
        qubits.end()
    );
    qk_circuit_gate(
        circuit, qk_gate,
        qubits.data(),
        params.empty() ? nullptr : params.data()
    );
}


PauliProductRotationGate::PauliProductRotationGate(jeff::QubitGate::Reader gate) : gate_(gate) {}

void PauliProductRotationGate::operand_counts(uint32_t* num_qubits, uint32_t* num_params) const {
    if (gate_.getControlQubits() != 0) {
        std::fprintf(
            stderr,
            "PauliProductRotationGate::operand_counts: controlled Pauli product rotation has no QkCircuit equivalent\n"
        );
        std::exit(1);
    }
    *num_qubits = gate_.getPpr().getPauliString().size();
    *num_params = 1;
}

PauliProductRotationGate::PauliRotation PauliProductRotationGate::to_gate(
    const std::vector<double>& params
) const {
    if (gate_.getControlQubits() != 0) {
        std::fprintf(
            stderr,
            "PauliProductRotationGate::to_rotation: controlled Pauli product rotation has no QkCircuit equivalent\n"
        );
        std::exit(1);
    }
    if (params.size() != 1) {
        std::fprintf(
            stderr,
            "PauliProductRotationGate::to_rotation: expected exactly 1 param (the rotation angle), got %zu\n",
            params.size()
        );
        std::exit(1);
    }

    double angle = params[0];
    if (gate_.getAdjoint()) angle = -angle;
    angle *= gate_.getPower();

    auto pauli_string = gate_.getPpr().getPauliString();
    auto z = std::make_unique<bool[]>(pauli_string.size());
    auto x = std::make_unique<bool[]>(pauli_string.size());

    for (uint32_t i = 0; i < pauli_string.size(); i++) {
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
    QkPauliProductRotation rotation{z.get(), x.get(), pauli_string.size(), angle_param.get()};
    return PauliRotation{std::move(z), std::move(x), std::move(angle_param), rotation};
}

void PauliProductRotationGate::emit(
    QkCircuit* circuit,
    std::vector<uint32_t> qubits,
    std::vector<double> params
) const {
    PauliRotation gate = to_gate(params);

    if (qubits.size() != gate.rotation.len) {
        std::fprintf(
            stderr,
            "PauliProductRotationGate::emit: expected %zu qubits for this ppr, got %zu\n",
            gate.rotation.len, qubits.size()
        );
        std::exit(1);
    }
    qk_circuit_pauli_product_rotation(circuit, &gate.rotation, qubits.data());
}

QubitGate::QubitGate(jeff::QubitGate::Reader gate):
    gate_(
        [&]() -> std::variant<WellKnownGate, PauliProductRotationGate> {
            if (gate.isWellKnown()) return WellKnownGate(gate);
            if (gate.isPpr()) return PauliProductRotationGate(gate);
            std::fprintf(stderr, "QubitGate: unhandled gate (custom gate, not wellKnown or ppr)\n");
            std::exit(1);
        }()
    ) {}


void QubitGate::operand_counts(uint32_t* num_qubits, uint32_t* num_params) const {
    std::visit(
        [&](const auto& g) {
            g.operand_counts(num_qubits, num_params);
        },
        gate_
    );
}

void QubitGate::emit(
    QkCircuit* circuit,
    std::vector<uint32_t> qubits,
    std::vector<double> params)
const {
    std::visit(
        [&](const auto& g){
            g.emit(
                circuit,
                std::move(qubits),
                std::move(params)
            );
        },
        gate_
    );
}
} // namespace JeffToQiskit

namespace QiskitToJeff {

WellKnownGate::WellKnownGate(QkGate gate) : gate_(gate) {}

bool WellKnownGate::to_gate(jeff::QubitGate::Builder gate) const {
    uint8_t control_qubits = 0;
    QkGate base_gate = gate_;

    auto controlled_it = QkGateToControlledMap.find(gate_);
    if (controlled_it != QkGateToControlledMap.end()) {
        control_qubits = controlled_it->second.first;
        base_gate = controlled_it->second.second;
    }

    auto well_known_it = QkGateToWellKnownMap.find(base_gate);
    if (well_known_it == QkGateToWellKnownMap.end()) return false;

    gate.setWellKnown(well_known_it->second);
    gate.setControlQubits(control_qubits);
    gate.setAdjoint(false);
    gate.setPower(1);
    return true;
}

void WellKnownGate::emit(jeff::Op::Builder op) const {
    jeff::QubitGate::Builder gate_builder = op.getInstruction().initQubit().initGate();
    if (!to_gate(gate_builder)) {
        std::fprintf(stderr, "WellKnownGate::emit: QkGate has no jeff wellKnown equivalent\n");
        std::exit(1);
    }

    // Qiskit orders a controlled gate's qubits as {controls..., targets...};
    // jeff orders them as {targets..., controls...}. Caller has already
    // populated inputs/outputs in Qiskit order, so rotate in place now
    // that controlQubits is known.
    uint8_t control_qubits = gate_builder.getControlQubits();
    uint32_t num_qubits = qk_gate_num_qubits(gate_);

    auto inputs = op.getInputs();
    std::vector<uint32_t> qubits(num_qubits);
    for (uint32_t i = 0; i < num_qubits; i++) qubits[i] = inputs[i];
    std::rotate(qubits.begin(), qubits.begin() + control_qubits, qubits.end());
    for (uint32_t i = 0; i < num_qubits; i++) inputs.set(i, qubits[i]);

    auto outputs = op.getOutputs();
    std::vector<uint32_t> out(num_qubits);
    for (uint32_t i = 0; i < num_qubits; i++) out[i] = outputs[i];
    std::rotate(out.begin(), out.begin() + control_qubits, out.end());
    for (uint32_t i = 0; i < num_qubits; i++) outputs.set(i, out[i]);
}


PauliProductRotationGate::PauliProductRotationGate(const QkPauliProductRotation& gate) : gate_(&gate) {}

bool PauliProductRotationGate::to_gate(jeff::QubitGate::Builder gate) const {
    auto pauli_string = gate.initPpr().initPauliString(static_cast<unsigned int>(gate_->len));
    for (size_t i = 0; i < gate_->len; i++) {
        bool z = gate_->z[i];
        bool x = gate_->x[i];
        jeff::Pauli pauli;
        if (!z && !x) pauli = jeff::Pauli::I;
        else if (!z && x) pauli = jeff::Pauli::X;
        else if (z && !x) pauli = jeff::Pauli::Z;
        else pauli = jeff::Pauli::Y;
        pauli_string.set(i, pauli);
    }

    gate.setControlQubits(0);
    gate.setAdjoint(false);
    gate.setPower(1);
    return true;
}

void PauliProductRotationGate::emit(jeff::Op::Builder op) const {
    jeff::QubitGate::Builder gate_builder = op.getInstruction().initQubit().initGate();
    to_gate(gate_builder);
}

}  // namespace QiskitToJeff
