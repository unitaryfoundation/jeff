#pragma once

#include <capnp/message.h>
#include <qiskit.h>
#include "jeff.capnp.h"

namespace jeff {
namespace qiskit_convert {

// Convert a jeff Module to a Qiskit QkCircuit.
// Only supports straight-line quantum circuits without classical control flow.
QkCircuit* jeff_to_qiskit(const Module::Reader& module);

// Convert a Qiskit QkCircuit to a jeff Module.
// The module will contain a single function with the circuit operations.
void qiskit_to_jeff(const QkCircuit* circuit, ::capnp::MallocMessageBuilder& message);

} // namespace qiskit_convert
} // namespace jeff
