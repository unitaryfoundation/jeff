#include "jeff_qiskitc.h"
#include "jeff_qiskitc_version.h"

#include <cerrno>
#include <cstdio>
#include <cstring>
#include <deque>
#include <vector>

#include <fcntl.h>
#include <unistd.h>

#include <capnp/message.h>
#include <kj/io.h>

#include "circuit_converter.h"


QkCircuit* jeff_to_qiskitc(jeff::Module::Reader mod) {
    jeff::Function::Reader fn = mod.getFunctions()[mod.getEntrypoint()];
    jeff::Function::Definition::Reader def = fn.getDefinition();
    jeff::Region::Reader body = def.getBody();

    JeffToQiskit::ValueMap values(def.getValues().size());

    uint32_t num_qubits = 0, num_clbits = 0;
    JeffToQiskit::walk_jeff_ops(body, [&](jeff::Op::Reader op) {
        auto count = JeffToQiskit::Op(op).resource_count();
        num_qubits += count.qubits;
        num_clbits += count.clbits;
    });

    QkCircuit* circuit = qk_circuit_new(num_qubits, num_clbits);

    JeffToQiskit::walk_jeff_ops(
        body,
        [&](jeff::Op::Reader op){ JeffToQiskit::Op(op).build(circuit, values); }
    );

    return circuit;
}

namespace {
void build_qiskitc_to_jeff_message(const QkCircuit* circuit, capnp::MessageBuilder& message) {
    uint32_t num_qubits = qk_circuit_num_qubits(circuit);
    uint32_t num_clbits = qk_circuit_num_clbits(circuit);
    size_t num_instructions = qk_circuit_num_instructions(circuit);

    std::deque<QiskitToJeff::Op> ops;

    uint32_t num_values = num_qubits;  // one alloc-produced Value per qubit
    uint32_t num_ops = num_qubits;     // one alloc Op per qubit
    for (size_t i = 0; i < num_instructions; i++) {
        QiskitToJeff::Op& op = ops.emplace_back(circuit, i);
        num_values += op.num_jeff_values();
        num_ops += op.num_jeff_ops();
    }

    jeff::Module::Builder mod = message.initRoot<jeff::Module>();
    mod.setVersion(jeff::SCHEMA_VERSION_MAJOR);
    mod.setVersionMinor(jeff::SCHEMA_VERSION_MINOR);
    mod.setVersionPatch(jeff::SCHEMA_VERSION_PATCH);
    mod.setEntrypoint(0);
    mod.setTool(JEFF_QISKITC_TOOL_NAME);
    mod.setToolVersion(JEFF_QISKITC_VERSION);
    mod.initStrings(1).set(0, "from_qkcircuit");

    jeff::Function::Builder fn = mod.initFunctions(1)[0];
    fn.setName(0);
    jeff::Function::Definition::Builder def = fn.initDefinition();

    jeff::Region::Builder body = def.initBody();
    body.initSources(0);
    auto operations = body.initOperations(num_ops);

    auto values_list = def.initValues(num_values);
    QiskitToJeff::ValueMap value_map(values_list, num_qubits, num_clbits);

    for (uint32_t q = 0; q < num_qubits; q++)
        QiskitToJeff::AllocOp(q).build(operations[q], value_map);

    uint32_t op_idx = num_qubits;
    for (const QiskitToJeff::Op& op : ops) {
        op.build(operations, op_idx, value_map);
        op_idx += op.num_jeff_ops();
    }

    std::vector<uint32_t> targets = value_map.targets();
    body.initTargets(static_cast<unsigned int>(targets.size()));
    for (size_t i = 0; i < targets.size(); i++)
        body.getTargets().set(i, targets[i]);
}
} // namespace

kj::Array<capnp::word> qiskitc_to_jeff(const QkCircuit* circuit) {
    capnp::MallocMessageBuilder message;
    build_qiskitc_to_jeff_message(circuit, message);
    return capnp::messageToFlatArray(message);
}

QkCircuit* jeff_file_to_qiskitc(const std::string& path) {
    int fd = open(path.c_str(), O_RDONLY);
    if (fd < 0) {
        std::fprintf(
            stderr,
            "jeff_file_to_qiskitc: failed to open \"%s\": %s\n",
            path.c_str(), std::strerror(errno)
        );
        std::exit(1);
    }
    capnp::StreamFdMessageReader reader{kj::AutoCloseFd(fd)};
    jeff::Module::Reader mod = reader.getRoot<jeff::Module>();
    return jeff_to_qiskitc(mod);
}

void qiskitc_to_jeff_file(const QkCircuit* circuit, const std::string& path) {
    capnp::MallocMessageBuilder message;
    build_qiskitc_to_jeff_message(circuit, message);

    int fd = open(path.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) {
        std::fprintf(
            stderr,
            "qiskitc_to_jeff_file: failed to open \"%s\": %s\n",
            path.c_str(), std::strerror(errno)
        );
        std::exit(1);
    }
    const kj::AutoCloseFd auto_close_fd(fd);

    capnp::writeMessageToFd(auto_close_fd, message);
}
