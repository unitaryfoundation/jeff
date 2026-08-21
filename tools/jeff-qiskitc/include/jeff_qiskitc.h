#pragma once

#include <functional>

#include <qiskit.h>

#include <capnp/serialize.h>
#include <kj/array.h>

#include "capnp/jeff.capnp.h"
#include <string>


QkCircuit* jeff_to_qiskitc(jeff::Module::Reader mod);

kj::Array<capnp::word> qiskitc_to_jeff(const QkCircuit* circuit);

QkCircuit* jeff_file_to_qiskitc(const std::string& path);

void qiskitc_to_jeff_file(const QkCircuit* circuit, const std::string& path);
