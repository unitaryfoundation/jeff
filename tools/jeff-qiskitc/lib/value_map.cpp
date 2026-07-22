#include "value_map.h"

namespace JeffToQiskit {

ValueMap::ValueMap(size_t num_values) : value_to_qubit_(num_values), value_to_float_(num_values) {}

uint32_t ValueMap::allocate_qubit() { return next_qubit_index_++; }

uint32_t ValueMap::allocate_clbit() { return next_clbit_index_++; }

uint32_t ValueMap::resolve_qubit(uint32_t value) const { return value_to_qubit_.at(value); }

void ValueMap::record_qubit(uint32_t value, uint32_t qubit) { value_to_qubit_.at(value) = qubit; }

void ValueMap::record_float(uint32_t value, double f) { value_to_float_.at(value) = f; }

double ValueMap::resolve_float(uint32_t value) const { return value_to_float_.at(value); }

}
