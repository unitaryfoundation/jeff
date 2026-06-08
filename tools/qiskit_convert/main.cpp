#include <Python.h>
#include <capnp/message.h>
#include <capnp/serialize.h>
#include <fcntl.h>
#include <kj/io.h>
#include <math.h>
#include <qiskit.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <string>
#include <vector>

#include "jeff.capnp.h"

// -----------------------------------------------------------------------
// Gate metadata — data-driven, single source of truth
// -----------------------------------------------------------------------

struct GateInfo {
    const char *name;
    QkGate gate;
    uint8_t n_qubits;
    uint8_t n_targets;
    uint8_t n_params;
};

static const GateInfo GATES[] = {
    {"h", QkGate_H, 1, 1, 0},
    {"i", QkGate_I, 1, 1, 0},
    {"x", QkGate_X, 1, 1, 0},
    {"y", QkGate_Y, 1, 1, 0},
    {"z", QkGate_Z, 1, 1, 0},
    {"phase", QkGate_Phase, 1, 1, 1},
    {"r", QkGate_R, 1, 1, 1},
    {"rx", QkGate_RX, 1, 1, 1},
    {"ry", QkGate_RY, 1, 1, 1},
    {"rz", QkGate_RZ, 1, 1, 1},
    {"s", QkGate_S, 1, 1, 0},
    {"sdg", QkGate_Sdg, 1, 1, 0},
    {"sx", QkGate_SX, 1, 1, 0},
    {"sxdg", QkGate_SXdg, 1, 1, 0},
    {"t", QkGate_T, 1, 1, 0},
    {"tdg", QkGate_Tdg, 1, 1, 0},
    {"u", QkGate_U, 1, 1, 3},
    {"u1", QkGate_U1, 1, 1, 1},
    {"u2", QkGate_U2, 1, 1, 2},
    {"u3", QkGate_U3, 1, 1, 3},
    {"ch", QkGate_CH, 2, 1, 0},
    {"cx", QkGate_CX, 2, 1, 0},
    {"cy", QkGate_CY, 2, 1, 0},
    {"cz", QkGate_CZ, 2, 1, 0},
    {"dcx", QkGate_DCX, 2, 2, 0},
    {"ecr", QkGate_ECR, 2, 2, 0},
    {"swap", QkGate_Swap, 2, 2, 0},
    {"iswap", QkGate_ISwap, 2, 2, 0},
    {"cphase", QkGate_CPhase, 2, 1, 1},
    {"cp", QkGate_CPhase, 2, 1, 1},
    {"crx", QkGate_CRX, 2, 1, 1},
    {"cry", QkGate_CRY, 2, 1, 1},
    {"crz", QkGate_CRZ, 2, 1, 1},
    {"cs", QkGate_CS, 2, 1, 0},
    {"csdg", QkGate_CSdg, 2, 1, 0},
    {"csx", QkGate_CSX, 2, 1, 0},
    {"cu", QkGate_CU, 2, 1, 3},
    {"cu1", QkGate_CU1, 2, 1, 1},
    {"cu3", QkGate_CU3, 2, 1, 3},
    {"rxx", QkGate_RXX, 2, 2, 1},
    {"ryy", QkGate_RYY, 2, 2, 1},
    {"rzz", QkGate_RZZ, 2, 2, 1},
    {"rzx", QkGate_RZX, 2, 2, 1},
    {"xx_minus_yy", QkGate_XXMinusYY, 2, 2, 1},
    {"xx_plus_yy", QkGate_XXPlusYY, 2, 2, 1},
    {"ccx", QkGate_CCX, 3, 1, 0},
    {"ccz", QkGate_CCZ, 3, 1, 0},
    {"cswap", QkGate_CSwap, 3, 2, 0},
    {"rccx", QkGate_RCCX, 3, 1, 0},
    {"c3x", QkGate_C3X, 4, 1, 0},
    {"c3sx", QkGate_C3SX, 4, 1, 0},
    {"rc3x", QkGate_RC3X, 4, 1, 0},
};

static const GateInfo *find_gate(QkGate ge) {
    for (auto &g : GATES) {
        if (g.gate == ge) return &g;
    }
    return nullptr;
}

static const GateInfo *find_gate_by_name(const char *name) {
    if (!name) return nullptr;
    for (auto &g : GATES) {
        if (!strcmp(g.name, name)) return &g;
    }
    return nullptr;
}

// -----------------------------------------------------------------------
// Well-known gate mapping: jeff ↔ Qiskit
// -----------------------------------------------------------------------

struct WkMap {
    int wk;
    QkGate qk;
};

static const WkMap WK_TO_QK[] = {
    {0, QkGate_X},
    {1, QkGate_Y},
    {2, QkGate_Z},
    {3, QkGate_S},
    {4, QkGate_T},
    {5, QkGate_Phase},
    {6, QkGate_RX},
    {7, QkGate_RY},
    {8, QkGate_RZ},
    {9, QkGate_H},
    {10, QkGate_U},
    {11, QkGate_Swap},
    {12, QkGate_I},
};

static QkGate wk_to_qk(int wk) {
    for (auto &m : WK_TO_QK) {
        if (m.wk == wk) return m.qk;
    }
    return (QkGate)-1;
}

static int qk_to_wk(QkGate qe) {
    for (auto &m : WK_TO_QK) {
        if (m.qk == qe) return m.wk;
    }
    return -1;
}

struct CtrlMap {
    QkGate target_ge;
    int n_ctrl;
    QkGate ctrl_ge;
};

static const CtrlMap CTRL_MAP[] = {
    {QkGate_X, 1, QkGate_CX},
    {QkGate_Y, 1, QkGate_CY},
    {QkGate_Z, 1, QkGate_CZ},
    {QkGate_H, 1, QkGate_CH},
    {QkGate_RX, 1, QkGate_CRX},
    {QkGate_RY, 1, QkGate_CRY},
    {QkGate_RZ, 1, QkGate_CRZ},
    {QkGate_Phase, 1, QkGate_CPhase},
    {QkGate_Swap, 1, QkGate_CSwap},
    {QkGate_S, 1, QkGate_CS},
    {QkGate_Sdg, 1, QkGate_CSdg},
    {QkGate_SX, 1, QkGate_CSX},
    {QkGate_X, 2, QkGate_CCX},
    {QkGate_Z, 2, QkGate_CCZ},
    {QkGate_X, 3, QkGate_C3X},
};

static QkGate ctrl_to_qk(QkGate target_ge, int n_ctrl) {
    for (auto &m : CTRL_MAP) {
        if (m.target_ge == target_ge && m.n_ctrl == n_ctrl) return m.ctrl_ge;
    }
    return (QkGate)-1;
}

struct CtrlWkMap {
    QkGate ctrl_ge;
    int target_wk;
};

static const CtrlWkMap CTRL_WK_MAP[] = {
    {QkGate_CX, 0},
    {QkGate_CY, 1},
    {QkGate_CZ, 2},
    {QkGate_CH, 9},
    {QkGate_CPhase, 5},
    {QkGate_CCX, 0},
    {QkGate_CCZ, 2},
    {QkGate_CSwap, 11},
};

static int ctrl_to_wk(QkGate ctrl_ge) {
    for (auto &m : CTRL_WK_MAP) {
        if (m.ctrl_ge == ctrl_ge) return m.target_wk;
    }
    return -1;
}

// -----------------------------------------------------------------------
// Qiskit → jeff conversion
// -----------------------------------------------------------------------

static int qiskit_to_jeff(QkCircuit *circuit, const char *output_path) {
    uint32_t n_qubits = qk_circuit_num_qubits(circuit);
    uint32_t n_clbits = qk_circuit_num_clbits(circuit);
    size_t n_inst = qk_circuit_num_instructions(circuit);

    if (n_qubits == 0) {
        fprintf(stderr, "error: circuit has no qubits\n");
        return -1;
    }

    ::capnp::MallocMessageBuilder message;
    ::Module::Builder mod = message.initRoot<::Module>();
    mod.setVersion(0);
    mod.setVersionMinor(2);
    mod.setVersionPatch(0);
    mod.setTool("jeff-qiskit-convert");
    mod.setToolVersion("0.1.0");

    auto strings = mod.initStrings(2);
    strings.set(0, "main");
    strings.set(1, "custom");

    auto funcs = mod.initFunctions(1);
    auto func = funcs[0];
    func.setName(0);
    auto def = func.initDefinition();

    size_t n_gates = 0, n_measures = 0;
    for (size_t i = 0; i < n_inst; i++) {
        QkOperationKind kind = qk_circuit_instruction_kind(circuit, i);
        if (kind == QkOperationKind_Gate) n_gates++;
        else if (kind == QkOperationKind_Measure) n_measures++;
    }
    size_t n_ops = n_qubits + n_gates + n_measures + n_gates * 2;
    size_t n_values = n_qubits + n_clbits + n_gates * 3;

    auto values = def.initValues(n_values);
    auto body = def.initBody();
    auto ops = body.initOperations(n_ops);

    uint32_t vi = 0;
    uint32_t oi = 0;

    std::vector<uint32_t> qubit_value_ids(n_qubits);
    for (uint32_t qi = 0; qi < n_qubits; qi++) {
        auto v = values[vi];
        auto t = v.initType();
        t.setQubit();
        qubit_value_ids[qi] = vi++;

        auto op = ops[oi++];
        uint32_t out = qubit_value_ids[qi];
        op.setOutputs(kj::ArrayPtr<const uint32_t>(&out, 1));
        auto instr = op.initInstruction();
        auto qubit = instr.initQubit();
        qubit.setAlloc();
    }

    std::vector<uint32_t> clbit_value_ids(n_clbits);
    for (uint32_t ci = 0; ci < n_clbits; ci++) {
        auto v = values[vi];
        auto t = v.initType();
        t.setInt(1);
        clbit_value_ids[ci] = vi++;
    }

    auto current_vals = qubit_value_ids;

    for (size_t idx = 0; idx < n_inst; idx++) {
        QkOperationKind kind = qk_circuit_instruction_kind(circuit, idx);
        QkCircuitInstruction inst;
        memset(&inst, 0, sizeof(inst));
        qk_circuit_get_instruction(circuit, idx, &inst);

        if (kind == QkOperationKind_Measure) {
            uint32_t q_idx = inst.qubits[0];
            uint32_t c_idx = inst.clbits[0];
            auto op = ops[oi++];
            uint32_t qi = current_vals[q_idx];
            op.setInputs(kj::ArrayPtr<const uint32_t>(&qi, 1));
            uint32_t co = clbit_value_ids[c_idx];
            op.setOutputs(kj::ArrayPtr<const uint32_t>(&co, 1));
            auto op_instr = op.initInstruction();
            auto qu = op_instr.initQubit();
            qu.setMeasure();
            qk_circuit_instruction_clear(&inst);
            continue;
        }

        if (kind == QkOperationKind_Gate) {
            const GateInfo *gi = find_gate_by_name(inst.name);
            if (!gi) {
                fprintf(stderr, "warning: unknown gate '%s', skipping\n",
                        inst.name ? inst.name : "NULL");
                qk_circuit_instruction_clear(&inst);
                continue;
            }
            QkGate gv = gi->gate;
            uint32_t n_targets = gi->n_targets;
            int np = (int)gi->n_params;
            int nc = (int)inst.num_qubits - (int)n_targets;
            if (nc < 0) nc = 0;
            int ntotal = (int)inst.num_qubits;

            std::vector<uint32_t> gouts;
            for (int i = 0; i < ntotal; i++) {
                auto v = values[vi];
                auto t = v.initType();
                t.setQubit();
                gouts.push_back(vi);
                vi++;
            }

            std::vector<uint32_t> gins;
            for (int i = 0; i < ntotal; i++) {
                gins.push_back(current_vals[inst.qubits[i]]);
            }

            std::vector<uint32_t> pvis;
            for (int pi = 0; pi < np; pi++) {
                auto fop = ops[oi++];
                uint32_t fvi = vi;
                fop.setOutputs(kj::ArrayPtr<const uint32_t>(&fvi, 1));
                vi++;
                pvis.push_back(fvi);

                auto fv = values[fvi];
                auto ft = fv.initType();
                ft.setFloat(FloatPrecision::FLOAT64);

                auto fi = fop.initInstruction();
                auto fl = fi.initFloat();
                double pval = (inst.params && pi < (int)inst.num_params)
                    ? qk_param_as_real(inst.params[pi])
                    : 0.0;
                fl.setConst64(pval);
            }

            auto op = ops[oi++];
            {
                std::vector<uint32_t> ai = gins;
                ai.insert(ai.end(), pvis.begin(), pvis.end());
                op.setInputs(kj::ArrayPtr<const uint32_t>(ai.data(), ai.size()));
            }
            op.setOutputs(kj::ArrayPtr<const uint32_t>(gouts.data(), gouts.size()));

            auto op_instr = op.initInstruction();
            auto qb = op_instr.initQubit();
            auto gate = qb.initGate();

            int wk = qk_to_wk(gv);
            if (wk >= 0) {
                gate.setWellKnown(static_cast<WellKnownGate>(wk));
            } else if (nc > 0) {
                int target_wk = ctrl_to_wk(gv);
                if (target_wk >= 0) {
                    gate.setWellKnown(static_cast<WellKnownGate>(target_wk));
                } else {
                    auto cust = gate.initCustom();
                    cust.setName(1);
                    cust.setNumQubits(n_targets);
                    cust.setNumParams((uint8_t)np);
                }
            } else {
                auto cust = gate.initCustom();
                cust.setName(1);
                cust.setNumQubits(n_targets);
                cust.setNumParams((uint8_t)np);
            }
            gate.setControlQubits((uint8_t)nc);
            gate.setAdjoint(false);
            gate.setPower(1);

            for (int i = 0; i < ntotal; i++) {
                current_vals[inst.qubits[i]] = gouts[i];
            }
        }

        qk_circuit_instruction_clear(&inst);
    }

    std::vector<uint32_t> targets;
    for (uint32_t v : current_vals) targets.push_back(v);
    for (uint32_t v : clbit_value_ids) targets.push_back(v);
    body.setTargets(kj::ArrayPtr<const uint32_t>(
        targets.data(), targets.size()));
    mod.setEntrypoint(0);

    int fd = open(output_path, O_CREAT | O_WRONLY | O_TRUNC, 0644);
    if (fd < 0) {
        perror("open");
        return -1;
    }
    writeMessageToFd(fd, message);
    close(fd);
    return 0;
}

// -----------------------------------------------------------------------
// jeff → Qiskit conversion
// -----------------------------------------------------------------------

static int jeff_to_qiskit(const char *input_path, const char *output_path) {
    int fd = open(input_path, O_RDONLY);
    if (fd < 0) {
        perror("open");
        return -1;
    }

    capnp::StreamFdMessageReader msg_reader(fd);
    auto mod = msg_reader.getRoot<::Module>();
    auto strings = mod.getStrings();
    uint16_t entry = mod.getEntrypoint();
    auto funcs = mod.getFunctions();
    if (entry >= funcs.size()) {
        fprintf(stderr, "error: entrypoint out of range\n");
        close(fd);
        return -1;
    }
    auto func = funcs[entry];
    auto def = func.getDefinition();
    auto body = def.getBody();
    auto ops = body.getOperations();

    uint32_t n_qubits = 0;
    uint32_t n_measures = 0;
    for (auto op : ops) {
        if (op.getInputs().size() == 0 && op.getOutputs().size() == 0) continue;
        auto instr = op.getInstruction();
        if (instr.isQubit()) {
            auto q = instr.getQubit();
            if (q.isAlloc()) n_qubits++;
            else if (q.isMeasure()) n_measures++;
        }
    }

    close(fd);

    if (n_qubits == 0) {
        fprintf(stderr, "error: no qubits in jeff\n");
        return -1;
    }

    QkCircuit *circuit = qk_circuit_new(n_qubits, n_measures);
    if (!circuit) {
        fprintf(stderr, "error: qk_circuit_new failed\n");
        return -1;
    }

    fd = open(input_path, O_RDONLY);
    capnp::StreamFdMessageReader msg_reader2(fd);
    mod = msg_reader2.getRoot<::Module>();
    funcs = mod.getFunctions();
    func = funcs[mod.getEntrypoint()];
    def = func.getDefinition();
    body = def.getBody();
    ops = body.getOperations();

    std::map<uint32_t, uint32_t> val_to_qubit;
    std::map<uint32_t, double> val_to_float;
    uint32_t next_qubit = 0;
    uint32_t next_clbit = 0;

    for (auto op : ops) {
        auto inputs = op.getInputs();
        auto outputs = op.getOutputs();
        auto instr = op.getInstruction();

        if (!instr.isQubit()) {
            if (instr.isFloat()) {
                auto f = instr.getFloat();
                if (outputs.size() > 0) {
                    if (f.isConst64()) {
                        val_to_float[outputs[0]] = f.getConst64();
                    } else if (f.isConst32()) {
                        val_to_float[outputs[0]] = f.getConst32();
                    }
                }
            }
            continue;
        }

        if (inputs.size() == 0 && outputs.size() == 0) continue;

        auto qubit = instr.getQubit();
        if (qubit.isAlloc()) {
            if (outputs.size() > 0) val_to_qubit[outputs[0]] = next_qubit++;
        } else if (qubit.isMeasure()) {
            if (inputs.size() > 0) {
                uint32_t q_idx = val_to_qubit[inputs[0]];
                qk_circuit_measure(circuit, q_idx, next_clbit++);
            }
        } else if (qubit.isGate()) {
            auto gate = qubit.getGate();
            uint8_t n_controls = gate.getControlQubits();
            const GateInfo *gi = nullptr;
            QkGate qk_ge = (QkGate)-1;

            if (gate.isWellKnown()) {
                int wk_val = static_cast<int>(gate.getWellKnown());
                qk_ge = wk_to_qk(wk_val);
                if (n_controls > 0) {
                    QkGate cge = ctrl_to_qk(qk_ge, (int)n_controls);
                    if ((int)cge >= 0) qk_ge = cge;
                }
                gi = find_gate(qk_ge);
            } else if (gate.isCustom()) {
                auto cust = gate.getCustom();
                uint16_t name_idx = cust.getName();
                const char *gname = "unknown";
                if (name_idx < strings.size()) {
                    gname = strings[name_idx].cStr();
                }
                qk_ge = (QkGate)-1;
                const GateInfo *tmp = find_gate_by_name(gname);
                if (tmp) qk_ge = tmp->gate;
                gi = tmp;
            }

            const char *gname = gi ? gi->name : "unknown";
            if ((int)qk_ge < 0 || !gi) {
                fprintf(stderr, "warning: unknown gate '%s', skipping\n",
                        gname);
                for (size_t i = 0; i < outputs.size(); i++) {
                    val_to_qubit[outputs[i]] = next_qubit++;
                }
                continue;
            }

            int n_params = (int)gi->n_params;
            size_t n_qi = inputs.size() - n_params;
            std::vector<uint32_t> qiskit_qubits;
            for (size_t i = 0; i < n_qi; i++) {
                auto it = val_to_qubit.find(inputs[i]);
                if (it != val_to_qubit.end()) {
                    qiskit_qubits.push_back(it->second);
                }
            }

            if (qiskit_qubits.empty()) {
                fprintf(stderr, "warning: no qubits for gate '%s'\n", gname);
                continue;
            }

            std::vector<double> pv;
            for (size_t i = n_qi; i < inputs.size(); i++) {
                auto it = val_to_float.find(inputs[i]);
                pv.push_back(it != val_to_float.end() ? it->second : 0.0);
            }

            qk_circuit_gate(circuit, qk_ge,
                            qiskit_qubits.data(),
                            pv.empty() ? nullptr : pv.data());

            for (size_t i = 0; i < n_qi && i < outputs.size(); i++) {
                val_to_qubit[outputs[i]] = qiskit_qubits[i];
            }
        }
    }
    close(fd);

    size_t n_inst = qk_circuit_num_instructions(circuit);
    uint32_t nq = qk_circuit_num_qubits(circuit);
    uint32_t nc = qk_circuit_num_clbits(circuit);
    printf("Qiskit circuit: %u qubits, %u clbits, %zu instructions\n", nq, nc,
           n_inst);

    if (output_path) {
        std::ofstream out(output_path);
        out << "Qiskit circuit with " << nq << " qubits, " << nc
            << " clbits, " << n_inst << " instructions" << std::endl;
        out.close();
        printf("Wrote summary to %s\n", output_path);
    }

    qk_circuit_free(circuit);
    return 0;
}

// -----------------------------------------------------------------------
// CLI
// -----------------------------------------------------------------------

static void usage() {
    printf("Usage:\n");
    printf("  jeff-qiskit-convert read <jeff_file> [diagram.txt]  "
           "Convert jeff -> Qiskit\n");
    printf("  jeff-qiskit-convert write <jeff_output> [n_qubits n_clbits]  "
           "Convert Qiskit circuit -> jeff\n");
    printf("\nRequires Qiskit C API (set QISKIT_ROOT env var if not auto-detected)\n");
}

int main(int argc, char **argv) {
    Py_Initialize();

    if (argc < 2) {
        usage();
        return 1;
    }

    std::string cmd = argv[1];

    if (cmd == "read") {
        if (argc < 3) {
            fprintf(stderr, "error: missing jeff file path\n");
            return 1;
        }
        const char *output_path = (argc > 3) ? argv[3] : nullptr;
        return jeff_to_qiskit(argv[2], output_path);
    }

    if (cmd == "write") {
        if (argc < 3) {
            fprintf(stderr, "error: missing output path\n");
            return 1;
        }
        uint32_t n_qubits = (argc > 3) ? (uint32_t)atoi(argv[3]) : 2;
        uint32_t n_clbits = (argc > 4) ? (uint32_t)atoi(argv[4]) : 2;

        QkCircuit *circuit = qk_circuit_new(n_qubits, n_clbits);
        uint32_t q0[] = {0};
        uint32_t q1[] = {1};
        uint32_t q01[] = {0, 1};

        qk_circuit_gate(circuit, QkGate_X, q0, nullptr);
        qk_circuit_gate(circuit, QkGate_X, q1, nullptr);
        qk_circuit_gate(circuit, QkGate_H, q0, nullptr);
        qk_circuit_gate(circuit, QkGate_CX, q01, nullptr);
        double ry_p[] = {M_PI / 4.0};
        qk_circuit_gate(circuit, QkGate_RY, q1, ry_p);
        qk_circuit_measure(circuit, 0, 0);
        qk_circuit_measure(circuit, 1, 1);

        if (qiskit_to_jeff(circuit, argv[2]) < 0) {
            qk_circuit_free(circuit);
            return 1;
        }
        printf("Wrote %s\n", argv[2]);
        qk_circuit_free(circuit);
        return 0;
    }

    fprintf(stderr, "error: unknown command '%s'\n", argv[1]);
    usage();
    return 1;
}
