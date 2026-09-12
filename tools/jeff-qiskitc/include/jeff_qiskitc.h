#pragma once

#include "capnp/jeff.capnp.h"

#include <capnp/serialize.h>
#include <kj/array.h>
#include <qiskit.h>

#include <string>

/**
 * @brief Convert the entrypoint function of a jeff module into a Qiskit circuit.
 * @param mod The jeff module to convert.
 * @return An owned circuit, which the caller must release with `qk_circuit_free`.
 *
 * @details
 * The function selected for conversion is the one named by the module's `entrypoint`; any
 * other functions in the module are ignored.
 *
 * Known limitations:
 *
 * - Only straight-line programs are supported: qubit allocations, non-destructive
 *   measurements, well-known gates and Pauli product rotations, and 32/64-bit float
 *   constants. Control flow, function calls, qubit frees and custom gates are not.
 * - Unsupported operations are reported on stderr and terminate the process.
 */
QkCircuit* jeff_to_qiskitc(jeff::Module::Reader mod);

/**
 * @brief Convert a Qiskit circuit into a serialized jeff module.
 * @param circuit The circuit to convert.
 * @return An owned memory buffer containing the serialized jeff module.
 *
 * @details
 * The resulting module holds a single function, whose body allocates one qubit per circuit
 * qubit and then mirrors the circuit's instructions in order.
 *
 * Known limitations:
 *
 * - Only gates, Pauli product rotations and measurements are supported, and each gate must
 *   have a jeff well-known equivalent.
 * - Unsupported instructions are reported on stderr and terminate the process.
 */
kj::Array<capnp::word> qiskitc_to_jeff(const QkCircuit* circuit);

/**
 * @brief Convert the entrypoint function of a .jeff file into a Qiskit circuit.
 * @param path The path to the .jeff file.
 * @return An owned circuit, which the caller must release with `qk_circuit_free`.
 *
 * @details
 * Shares the conversion limitations of `jeff_to_qiskitc`. A file that cannot be opened is
 * reported on stderr and terminates the process.
 */
QkCircuit* jeff_file_to_qiskitc(const std::string& path);

/**
 * @brief Convert a Qiskit circuit into a jeff module and write it to a .jeff file.
 * @param circuit The circuit to convert.
 * @param path The path to the .jeff file, which is created or truncated.
 *
 * @details
 * Shares the conversion limitations of `qiskitc_to_jeff`. A file that cannot be opened is
 * reported on stderr and terminates the process.
 */
void qiskitc_to_jeff_file(const QkCircuit* circuit, const std::string& path);
