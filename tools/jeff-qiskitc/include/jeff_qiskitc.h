#pragma once

#include <functional>

#include <qiskit.h>

#include <capnp/serialize.h>
#include <kj/array.h>

#include "capnp/jeff.capnp.h"


QkCircuit* jeff_to_qiskitc(jeff::Module::Reader module);
