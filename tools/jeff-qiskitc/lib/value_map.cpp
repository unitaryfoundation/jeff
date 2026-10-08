#include "value_map.h"

#include <cstdio>
#include <cstdlib>
#include <limits>

namespace {
// Marks a clbit or value that has not been recorded yet.
constexpr uint32_t kUnset = std::numeric_limits<uint32_t>::max();
} // namespace

namespace JeffToQiskit {

ValueMap::ValueMap(size_t num_values)
    : value_to_qubit_(num_values), value_to_clbit_(num_values, kUnset),
      value_to_float_(num_values) {}

uint32_t ValueMap::allocate_qubit() { return next_qubit_index_++; }

uint32_t ValueMap::resolve_qubit(uint32_t value) const { return value_to_qubit_.at(value); }

void ValueMap::record_qubit(uint32_t value, uint32_t qubit) { value_to_qubit_.at(value) = qubit; }

uint32_t ValueMap::resolve_clbit(uint32_t value) const {
    uint32_t clbit = value_to_clbit_.at(value);
    if (clbit == kUnset) {
        std::fprintf(stderr, "JeffToQiskit::ValueMap::resolve_clbit: no clbit for value %u\n",
                     value);
        std::exit(1);
    }
    return clbit;
}

void ValueMap::record_clbit(uint32_t value, uint32_t clbit) { value_to_clbit_.at(value) = clbit; }

void ValueMap::record_float(uint32_t value, double f) { value_to_float_.at(value) = f; }

double ValueMap::resolve_float(uint32_t value) const { return value_to_float_.at(value); }

} // namespace JeffToQiskit

namespace QiskitToJeff {

ValueMap::ValueMap(capnp::List<jeff::Value>::Builder values, uint32_t num_qubits,
                   uint32_t num_clbits)
    : values_(values), qubit_to_value_(num_qubits), clbit_to_value_(num_clbits, kUnset) {}

uint32_t ValueMap::allocate_qubit_value() {
    uint32_t v = next_value_++;
    values_[v].initType().setQubit();
    return v;
}

uint32_t ValueMap::allocate_bit_value() {
    uint32_t v = next_value_++;
    values_[v].initType().setInt(1);
    return v;
}

uint32_t ValueMap::allocate_float_value() {
    uint32_t v = next_value_++;
    values_[v].initType().setFloat(jeff::FloatPrecision::FLOAT64);
    return v;
}

uint32_t ValueMap::resolve_qubit(uint32_t qubit) const { return qubit_to_value_.at(qubit); }

void ValueMap::record_qubit(uint32_t qubit, uint32_t value) { qubit_to_value_.at(qubit) = value; }

uint32_t ValueMap::resolve_clbit(uint32_t clbit) const {
    uint32_t value = clbit_to_value_.at(clbit);
    if (value == kUnset) {
        std::fprintf(stderr, "QiskitToJeff::ValueMap::resolve_clbit: no value for clbit %u\n",
                     clbit);
        std::exit(1);
    }
    return value;
}

void ValueMap::record_clbit(uint32_t clbit, uint32_t value) { clbit_to_value_.at(clbit) = value; }

std::vector<uint32_t> ValueMap::targets() const {
    std::vector<uint32_t> result;
    for (size_t q = 0; q < qubit_to_value_.size(); q++)
        result.push_back(resolve_qubit(q));
    for (size_t c = 0; c < clbit_to_value_.size(); c++)
        result.push_back(resolve_clbit(c));
    return result;
}

} // namespace QiskitToJeff
