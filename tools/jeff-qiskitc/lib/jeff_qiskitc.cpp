#include "jeff_qiskitc.h"

#include <deque>
#include <vector>

#include <capnp/message.h>

#include "circuit_converter.h"


QkCircuit* jeff_to_qiskitc(jeff::Module::Reader module) {
    jeff::Function::Reader fn = module.getFunctions()[0];
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

kj::Array<capnp::word> qiskitc_to_jeff(const QkCircuit* circuit) {
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

    capnp::MallocMessageBuilder message;
    jeff::Module::Builder module = message.initRoot<jeff::Module>();
    module.setVersion(0);
    module.setVersionMinor(3);
    module.setVersionPatch(0);
    module.setEntrypoint(0);
    module.initStrings(1).set(0, "from_qkcircuit");

    jeff::Function::Builder fn = module.initFunctions(1)[0];
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

    return capnp::messageToFlatArray(message);
}
