#include "jeff_qiskitc.h"

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
