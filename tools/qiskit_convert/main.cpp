#include <capnp/message.h>
#include <capnp/serialize.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <kj/io.h>
#include <math.h>
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

#include "capnp/jeff.capnp.h"

// -----------------------------------------------------------------------
// Qiskit C API — loaded at runtime via dlopen
// -----------------------------------------------------------------------

struct QkApi {
    void *lib;
    uint32_t (*api_version)();
    void *(*circuit_new)(uint32_t, uint32_t);
    void (*circuit_free)(void *);
    uint32_t (*circuit_num_qubits)(const void *);
    uint32_t (*circuit_num_clbits)(const void *);
    size_t (*circuit_num_instructions)(const void *);
    uint32_t (*circuit_gate)(void *, uint8_t, const uint32_t *, const double *);
    uint32_t (*circuit_measure)(void *, uint32_t, uint32_t);
    uint8_t (*circuit_instruction_kind)(const void *, size_t);
    void (*circuit_get_instruction)(const void *, size_t, void *);
    void (*circuit_instruction_clear)(void *);
};

static int load_python() {
    // Load the Python framework so the accelerator's Python symbols resolve
    const char *py_path =
        "/usr/local/opt/python@3.12/Frameworks/Python.framework/Versions/3.12/Python";
    void *py = dlopen(py_path, RTLD_LAZY | RTLD_GLOBAL);
    if (!py) {
        fprintf(stderr, "warning: could not load Python: %s\n", dlerror());
        return -1;
    }
    // Initialize Python so extension modules work
    typedef void (*py_init_t)();
    py_init_t Py_Initialize = (py_init_t)dlsym(py, "Py_Initialize");
    if (Py_Initialize) Py_Initialize();
    return 0;
}

static int load_qk_api(QkApi &api, const char *lib_path) {
    load_python();

    api.lib = dlopen(lib_path, RTLD_LAZY | RTLD_GLOBAL);
    if (!api.lib) {
        fprintf(stderr, "error: dlopen failed: %s\n", dlerror());
        return -1;
    }
#define LOAD(name)                                                             \
    do {                                                                       \
        *(void **)&api.name = dlsym(api.lib, "qk_" #name);                    \
        if (!api.name) {                                                       \
            fprintf(stderr, "error: symbol qk_" #name " not found: %s\n",      \
                    dlerror());                                                \
            dlclose(api.lib);                                                  \
            return -1;                                                         \
        }                                                                      \
    } while (0)
    LOAD(api_version);
    LOAD(circuit_new);
    LOAD(circuit_free);
    LOAD(circuit_num_qubits);
    LOAD(circuit_num_clbits);
    LOAD(circuit_num_instructions);
    LOAD(circuit_gate);
    LOAD(circuit_measure);
    LOAD(circuit_instruction_kind);
    LOAD(circuit_get_instruction);
    LOAD(circuit_instruction_clear);
#undef LOAD
    return 0;
}

// -----------------------------------------------------------------------
// Qiskit gate names ↔ enum mapping
// -----------------------------------------------------------------------

struct GateMap {
    const char *name;
    uint8_t gate;
};

static const GateMap GATE_NAMES[] = {
    {"h", 1},    {"i", 2},     {"x", 3},    {"y", 4},    {"z", 5},
    {"phase", 6},{"r", 7},     {"rx", 8},   {"ry", 9},   {"rz", 10},
    {"s", 11},   {"sdg", 12},  {"sx", 13},  {"sxdg", 14},{"t", 15},
    {"tdg", 16}, {"u", 17},    {"u1", 18},  {"u2", 19},  {"u3", 20},
    {"ch", 21},  {"cx", 22},   {"cy", 23},  {"cz", 24},  {"dcx", 25},
    {"ecr", 26}, {"swap", 27}, {"iswap", 28},{"cphase", 29},
    {"cp", 29},  {"crx", 30},  {"cry", 31}, {"crz", 32}, {"cs", 33},
    {"csdg", 34},{"csx", 35},  {"cu", 36},  {"cu1", 37}, {"cu3", 38},
    {"rxx", 39}, {"ryy", 40},  {"rzz", 41}, {"rzx", 42},
    {"xx_minus_yy", 43},{"xx_plus_yy", 44},{"ccx", 45},{"ccz", 46},
    {"cswap", 47},{"rccx", 48},{"c3x", 49}, {"c3sx", 50},{"rc3x", 51},
};

static const char *gate_name(uint8_t gate) {
    for (auto &g : GATE_NAMES) {
        if (g.gate == gate) return g.name;
    }
    return nullptr;
}

static int gate_enum(const char *name) {
    for (auto &g : GATE_NAMES) {
        if (!strcmp(g.name, name)) return g.gate;
    }
    return -1;
}

static int gate_num_qubits(uint8_t gate) {
    switch (gate) {
    case 1: case 2: case 3: case 4: case 5:
    case 6: case 7: case 8: case 9: case 10:
    case 11: case 12: case 13: case 14: case 15: case 16:
    case 17: case 18: case 19: case 20:
        return 1;
    case 21: case 22: case 23: case 24:
    case 25: case 26: case 27: case 28:
    case 29: case 30: case 31: case 32:
    case 33: case 34: case 35: case 36: case 37: case 38:
    case 39: case 40: case 41: case 42: case 43: case 44:
        return 2;
    case 45: case 46: return 3;
    case 47: return 3;
    case 48: return 3;
    case 49: return 4;
    case 50: return 4;
    case 51: return 4;
    default: return 1;
    }
}

static int gate_num_targets(uint8_t gate) {
    // Number of non-control qubit operands
    switch (gate) {
    case 1: case 2: case 3: case 4: case 5:
    case 6: case 7: case 8: case 9: case 10:
    case 11: case 12: case 13: case 14: case 15: case 16:
    case 17: case 18: case 19: case 20:
        return 1;
    case 27: case 28: return 2; // SWAP, ISWAP
    case 25: case 26: return 2; // DCX, ECR
    case 39: case 40: case 41: case 42: return 2; // RXX, RYY, RZZ, RZX
    case 43: case 44: return 2; // XXMinusYY, XXPlusYY
    case 47: return 2;
    default:
        // Controlled gates have 1 target
        if (gate >= 21 && gate <= 46) return 1;
        if (gate >= 48) return 1;
        return 1;
    }
}

static int gate_num_params(uint8_t gate) {
    switch (gate) {
    case 6: case 7: case 8: case 9: case 10: return 1;
    case 17: return 3;
    case 18: return 1;
    case 19: return 2;
    case 20: return 3;
    case 29: case 30: case 31: case 32: return 1;
    case 36: return 3;
    case 37: return 1;
    case 38: return 3;
    case 39: case 40: case 41: case 42: return 1;
    default: return 0;
    }
}

// -----------------------------------------------------------------------
// Well-known gate mapping: jeff ↔ Qiskit
// -----------------------------------------------------------------------

static int wk_to_qk(int wk) {
    switch (wk) {
    case 0: return 3;  // X
    case 1: return 4;  // Y
    case 2: return 5;  // Z
    case 3: return 11; // S
    case 4: return 15; // T
    case 5: return 6;  // R1/Phase
    case 6: return 8;  // RX
    case 7: return 9;  // RY
    case 8: return 10; // RZ
    case 9: return 1;  // H
    case 10: return 17; // U
    case 11: return 27; // SWAP
    case 12: return 2;  // I
    case 13: return 0;  // GPHASE
    default: return -1;
    }
}

static int qk_to_wk(int qe) {
    switch (qe) {
    case 3: return 0;  // X
    case 4: return 1;  // Y
    case 5: return 2;  // Z
    case 11: return 3; // S
    case 15: return 4; // T
    case 6: return 5;  // Phase
    case 8: return 6;  // RX
    case 9: return 7;  // RY
    case 10: return 8; // RZ
    case 1: return 9;  // H
    case 17: return 10; // U
    case 27: return 11; // SWAP
    case 2: return 12; // I
    case 0: return 13; // GPHASE
    default: return -1;
    }
}

// -----------------------------------------------------------------------
// Qiskit → jeff conversion
// -----------------------------------------------------------------------

static int qiskit_to_jeff(const QkApi &api, void *circuit,
                           const char *output_path) {
    uint32_t n_qubits = api.circuit_num_qubits(circuit);
    uint32_t n_clbits = api.circuit_num_clbits(circuit);
    size_t n_inst = api.circuit_num_instructions(circuit);

    if (n_qubits == 0) {
        fprintf(stderr, "error: circuit has no qubits\n");
        return -1;
    }

    ::capnp::MallocMessageBuilder message;
    auto module = message.initRoot<Module>();
    module.setVersion(0);
    module.setVersionMinor(2);
    module.setVersionPatch(0);
    module.setTool("jeff-qiskit-convert");
    module.setToolVersion("0.1.0");

    // String table: indices 0=main, 1=q, 2=c, 3=gate-name placeholder
    auto strings = module.initStrings(4);
    strings.set(0, "main");
    strings.set(1, "q");
    strings.set(2, "c");
    strings.set(3, "gate");

    // Single entrypoint function
    auto funcs = module.initFunctions(1);
    auto func = funcs[0];
    func.setName(0);
    auto def = func.initDefinition();

    // Count ops needed
    size_t n_gates = 0, n_measures = 0;
    for (size_t i = 0; i < n_inst; i++) {
        uint8_t kind = api.circuit_instruction_kind(circuit, i);
        if (kind == 0) n_gates++;
        else if (kind == 3) n_measures++;
    }
    size_t n_params_total = 0;
    for (size_t i = 0; i < n_inst; i++) {
        uint8_t kind = api.circuit_instruction_kind(circuit, i);
        if (kind == 0) {
            // Quick pass: count params per gate
            // We'll just allocate extra
            n_params_total++;
        }
    }
    size_t n_ops = n_qubits + n_gates + n_measures + n_gates * 2;
    size_t n_values = n_qubits + n_clbits + n_gates * 3;

    auto values = def.initValues(n_values);
    auto body = def.initBody();
    auto ops = body.initOperations(n_ops);

    uint32_t vi = 0;
    uint32_t oi = 0;

    // Allocate qubits
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

    // clbit values (int type, width 1)
    std::vector<uint32_t> clbit_value_ids(n_clbits);
    for (uint32_t ci = 0; ci < n_clbits; ci++) {
        auto v = values[vi];
        auto t = v.initType();
        t.setInt(1);
        clbit_value_ids[ci] = vi++;
    }

    // SSA tracking
    auto current_vals = qubit_value_ids;

    struct InstBuf {
        char *name;
        uint32_t *qubits;
        uint32_t *clbits;
        void **params;
        uint32_t num_qubits;
        uint32_t num_clbits;
        uint32_t num_params;
    };

    for (size_t idx = 0; idx < n_inst; idx++) {
        uint8_t kind = api.circuit_instruction_kind(circuit, idx);
        InstBuf inst;
        memset(&inst, 0, sizeof(inst));
        api.circuit_get_instruction(circuit, idx, &inst);

        if (kind == 3) { // Measure
            uint32_t q_idx = inst.qubits[0];
            uint32_t c_idx = inst.clbits[0];
            auto op = ops[oi++];
            uint32_t qi = current_vals[q_idx];
            op.setInputs(kj::ArrayPtr<const uint32_t>(&qi, 1));
            uint32_t co = clbit_value_ids[c_idx];
            op.setOutputs(kj::ArrayPtr<const uint32_t>(&co, 1));
            auto instr = op.initInstruction();
            auto qu = instr.initQubit();
            qu.setMeasure();
            api.circuit_instruction_clear(&inst);
            continue;
        }

        if (kind == 0) { // Gate
            const char *gname = inst.name;
            int ge = gate_enum(gname);
            int n_targets = gate_num_targets(ge);
            int np = gate_num_params(ge);
            int nc = (int)inst.num_qubits - n_targets;
            if (nc < 0) nc = 0;
            int ntotal = (int)inst.num_qubits;

            // Gate output values (SSA)
            std::vector<uint32_t> gouts;
            for (int i = 0; i < ntotal; i++) {
                auto v = values[vi];
                auto t = v.initType();
                t.setQubit();
                gouts.push_back(vi);
                vi++;
            }

            // Gate input values (current SSA)
            std::vector<uint32_t> gins;
            for (int i = 0; i < ntotal; i++) {
                gins.push_back(current_vals[inst.qubits[i]]);
            }

            // Float const ops for each param
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
                fl.setConst64(0.0);
            }

            // Gate operation
            auto op = ops[oi++];
            {
                std::vector<uint32_t> ai = gins;
                ai.insert(ai.end(), pvis.begin(), pvis.end());
                op.setInputs(kj::ArrayPtr<const uint32_t>(ai.data(), ai.size()));
            }
            op.setOutputs(kj::ArrayPtr<const uint32_t>(gouts.data(), gouts.size()));

            auto instr = op.initInstruction();
            auto qb = instr.initQubit();
            auto gate = qb.initGate();
            // For controlled gates: use the well-known target gate with controlQubits set
            int wk = qk_to_wk(ge);
            if (wk >= 0) {
                gate.setWellKnown(static_cast<WellKnownGate>(wk));
            } else if (nc > 0) {
                // If controlled but no direct well-known, try the underlying target gate
                int target_ge = ge;
                // For most standard controlled gates (CX, CY, CZ, CH, CCX, CSWAP),
                // the target gate is well-known even if the combined gate isn't.
                int target_wk = -1;
                switch (ge) {
                case 22: target_wk = 0; break; // CX -> X
                case 23: target_wk = 1; break; // CY -> Y
                case 24: target_wk = 2; break; // CZ -> Z
                case 21: target_wk = 9; break; // CH -> H
                case 29: target_wk = 5; break; // CPhase -> R1
                case 45: target_wk = 0; break; // CCX -> X
                case 46: target_wk = 2; break; // CCZ -> Z
                case 47: target_wk = 11; break; // CSWAP -> SWAP
                }
                if (target_wk >= 0) {
                    gate.setWellKnown(static_cast<WellKnownGate>(target_wk));
                } else {
                    auto cust = gate.initCustom();
                    cust.setName(3);
                    cust.setNumQubits((uint8_t)n_targets);
                    cust.setNumParams((uint8_t)np);
                }
            } else {
                auto cust = gate.initCustom();
                cust.setName(3);
                cust.setNumQubits((uint8_t)n_targets);
                cust.setNumParams((uint8_t)np);
            }
            gate.setControlQubits((uint8_t)nc);
            gate.setAdjoint(false);
            gate.setPower(1);

            // Update SSA
            for (int i = 0; i < ntotal; i++) {
                current_vals[inst.qubits[i]] = gouts[i];
            }
        }

        api.circuit_instruction_clear(&inst);
    }

    // Region sources/targets
    body.setSources(kj::ArrayPtr<const uint32_t>(
        qubit_value_ids.data(), qubit_value_ids.size()));
    std::vector<uint32_t> targets;
    for (uint32_t v : current_vals) targets.push_back(v);
    for (uint32_t v : clbit_value_ids) targets.push_back(v);
    body.setTargets(kj::ArrayPtr<const uint32_t>(
        targets.data(), targets.size()));
    module.setEntrypoint(0);

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

static int jeff_to_qiskit(const QkApi &api, const char *input_path,
                            const char *output_path) {
    int fd = open(input_path, O_RDONLY);
    if (fd < 0) {
        perror("open");
        return -1;
    }

    capnp::StreamFdMessageReader message(fd);
    auto module = message.getRoot<Module>();
    auto strings = module.getStrings();
    uint16_t entry = module.getEntrypoint();
    auto funcs = module.getFunctions();
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

    void *circuit = api.circuit_new(n_qubits, n_measures);
    if (!circuit) {
        fprintf(stderr, "error: qk_circuit_new failed\n");
        return -1;
    }

    // Pass 2: execute operations
    fd = open(input_path, O_RDONLY);
    capnp::StreamFdMessageReader message2(fd);
    module = message2.getRoot<Module>();
    funcs = module.getFunctions();
    func = funcs[module.getEntrypoint()];
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

        // Skip uninitialized padding ops
        if (inputs.size() == 0 && outputs.size() == 0) continue;

        auto qubit = instr.getQubit();
        if (qubit.isAlloc()) {
            if (outputs.size() > 0) val_to_qubit[outputs[0]] = next_qubit++;
        } else if (qubit.isMeasure()) {
            if (inputs.size() > 0) {
                uint32_t q_idx = val_to_qubit[inputs[0]];
                api.circuit_measure(circuit, q_idx, next_clbit++);
            }
        } else if (qubit.isGate()) {
            auto gate = qubit.getGate();
            uint8_t n_controls = gate.getControlQubits();
            const char *gname = nullptr;
            int n_targets = 0;
            int n_params = 0;
            int qk_ge = -1;

            if (gate.isWellKnown()) {
                int wk_val = static_cast<int>(gate.getWellKnown());
                qk_ge = wk_to_qk(wk_val);
                // For controlled well-known gates, translate to the appropriate
                // Qiskit controlled gate
                if (n_controls == 1) {
                    switch (qk_ge) {
                    case 3: qk_ge = 22; break;  // CX
                    case 4: qk_ge = 23; break;  // CY
                    case 5: qk_ge = 24; break;  // CZ
                    case 1: qk_ge = 21; break;  // CH
                    case 8: qk_ge = 30; break;  // CRX
                    case 9: qk_ge = 31; break;  // CRY
                    case 10: qk_ge = 32; break; // CRZ
                    case 6: qk_ge = 29; break;  // CPhase
                    case 27: qk_ge = 47; break; // CSWAP
                    case 11: qk_ge = 33; break; // CS
                    case 12: qk_ge = 34; break; // CSdg
                    case 13: qk_ge = 35; break; // CSX
                    }
                } else if (n_controls == 2) {
                    switch (qk_ge) {
                    case 3: qk_ge = 45; break;  // CCX
                    case 5: qk_ge = 46; break;  // CCZ
                    }
                } else if (n_controls == 3) {
                    switch (qk_ge) {
                    case 3: qk_ge = 49; break;  // C3X
                    }
                }
                gname = gate_name(qk_ge);
                n_targets = gate_num_qubits(qk_ge);
                n_params = gate_num_params(qk_ge);
            } else if (gate.isCustom()) {
                auto cust = gate.getCustom();
                n_targets = cust.getNumQubits();
                n_params = cust.getNumParams();
                uint16_t name_idx = cust.getName();
                if (name_idx < strings.size()) {
                    gname = strings[name_idx].cStr();
                } else {
                    gname = "unknown";
                }
                qk_ge = gate_enum(gname);
            }

        if (!gname) gname = "unknown";
        if (qk_ge < 0) {
            fprintf(stderr, "warning: unknown gate '%s', skipping\n",
                    gname);
            // Still update SSA so subsequent ops don't break
            for (size_t i = 0; i < outputs.size(); i++) {
                val_to_qubit[outputs[i]] = next_qubit++;
            }
            continue;
        }

            size_t n_qi = inputs.size() - n_params;
            std::vector<uint32_t> qiskit_qubits;
            for (size_t i = 0; i < n_qi; i++) {
                auto it = val_to_qubit.find(inputs[i]);
                if (it != val_to_qubit.end()) {
                    qiskit_qubits.push_back(it->second);
                }
            }

            if (qiskit_qubits.empty()) {
                fprintf(stderr, "warning: no qubits for gate '%s'\n",
                        gname);
                continue;
            }

            std::vector<double> pv;
            for (size_t i = n_qi; i < inputs.size(); i++) {
                auto it = val_to_float.find(inputs[i]);
                pv.push_back(it != val_to_float.end() ? it->second : 0.0);
            }

            api.circuit_gate(circuit, (uint8_t)qk_ge,
                             qiskit_qubits.data(),
                             pv.empty() ? nullptr : pv.data());

            for (size_t i = 0; i < n_qi && i < outputs.size(); i++) {
                val_to_qubit[outputs[i]] = qiskit_qubits[i];
            }
        }
    }
    close(fd);

    size_t n_inst = api.circuit_num_instructions(circuit);
    uint32_t nq = api.circuit_num_qubits(circuit);
    uint32_t nc = api.circuit_num_clbits(circuit);
    printf("Qiskit circuit: %u qubits, %u clbits, %zu instructions\n", nq, nc,
           n_inst);

    if (output_path) {
        std::ofstream out(output_path);
        out << "Qiskit circuit with " << nq << " qubits, " << nc
            << " clbits, " << n_inst << " instructions" << std::endl;
        out.close();
        printf("Wrote summary to %s\n", output_path);
    }

    api.circuit_free(circuit);
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
           "Build test jeff file\n");
    printf("  jeff-qiskit-convert test                  "
           "Run round-trip verification\n");
}

static const char *find_qk_lib() {
    const char *env = getenv("QISKIT_LIB");
    if (env) return env;
    return "/private/tmp/braket-venv2/lib/python3.12/site-packages/qiskit/"
           "_accelerate.abi3.so";
}

int main(int argc, char **argv) {
    if (argc < 2) {
        usage();
        return 1;
    }

    QkApi api;
    if (load_qk_api(api, find_qk_lib()) < 0) {
        return 1;
    }

    std::string cmd = argv[1];

    if (cmd == "read") {
        if (argc < 3) {
            fprintf(stderr, "error: missing jeff file path\n");
            return 1;
        }
        const char *output_path = (argc > 3) ? argv[3] : nullptr;
        return jeff_to_qiskit(api, argv[2], output_path);
    }

    if (cmd == "write") {
        if (argc < 3) {
            fprintf(stderr, "error: missing output path\n");
            return 1;
        }
        uint32_t n_qubits = (argc > 3) ? (uint32_t)atoi(argv[3]) : 2;
        uint32_t n_clbits = (argc > 4) ? (uint32_t)atoi(argv[4]) : 2;

        void *circuit = api.circuit_new(n_qubits, n_clbits);
        uint32_t q0[] = {0};
        uint32_t q1[] = {1};
        uint32_t q01[] = {0, 1};

        api.circuit_gate(circuit, 3, q0, nullptr);
        api.circuit_gate(circuit, 3, q1, nullptr);
        api.circuit_gate(circuit, 1, q0, nullptr);
        api.circuit_gate(circuit, 22, q01, nullptr);
        double ry_p[] = {M_PI / 4.0};
        api.circuit_gate(circuit, 9, q1, ry_p);
        api.circuit_measure(circuit, 0, 0);
        api.circuit_measure(circuit, 1, 1);

        if (qiskit_to_jeff(api, circuit, argv[2]) < 0) {
            api.circuit_free(circuit);
            return 1;
        }
        printf("Wrote %s\n", argv[2]);
        api.circuit_free(circuit);
        return 0;
    }

    if (cmd == "test") {
        printf("Running round-trip verification...\n");

        void *circuit = api.circuit_new(2, 2);
        uint32_t q0[] = {0};
        uint32_t q1[] = {1};
        uint32_t q01[] = {0, 1};

        api.circuit_gate(circuit, 3, q0, nullptr);
        api.circuit_gate(circuit, 1, q1, nullptr);
        api.circuit_gate(circuit, 22, q01, nullptr);
        double ry_p[] = {-2.0 * M_PI / 3.0};
        api.circuit_gate(circuit, 9, q1, ry_p);
        api.circuit_measure(circuit, 0, 0);
        api.circuit_measure(circuit, 1, 1);

        size_t n_inst = api.circuit_num_instructions(circuit);
        printf("Original circuit: %zu instructions\n", n_inst);

        const char *tmp_path = "/tmp/jeff_test_output.jeff";
        if (qiskit_to_jeff(api, circuit, tmp_path) < 0) {
            api.circuit_free(circuit);
            return 1;
        }
        printf("Wrote jeff file, reading back...\n");

        if (jeff_to_qiskit(api, tmp_path, nullptr) < 0) {
            api.circuit_free(circuit);
            return 1;
        }

        unlink(tmp_path);
        api.circuit_free(circuit);
        printf("PASS\n");
        return 0;
    }

    fprintf(stderr, "error: unknown command '%s'\n", argv[1]);
    usage();
    return 1;
}
