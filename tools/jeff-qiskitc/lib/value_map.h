#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

#include "capnp/jeff.capnp.h"

namespace JeffToQiskit {

class ValueMap {
public:
    explicit ValueMap(size_t num_values);

    uint32_t allocate_qubit();

    uint32_t allocate_clbit();

    uint32_t resolve_qubit(uint32_t value) const;

    void record_qubit(uint32_t value, uint32_t qubit);

    void record_float(uint32_t value, double f);

    double resolve_float(uint32_t value) const;

private:
    std::vector<uint32_t> value_to_qubit_;
    std::vector<double> value_to_float_;
    uint32_t next_qubit_index_ = 0;
    uint32_t next_clbit_index_ = 0;
};

}



namespace QiskitToJeff {

class ValueMap {
public:
    ValueMap(capnp::List<jeff::Value>::Builder values, uint32_t num_qubits, uint32_t num_clbits);

    uint32_t allocate_qubit_value();
    uint32_t allocate_bit_value();
    uint32_t allocate_float_value();

    uint32_t resolve_qubit(uint32_t qubit) const;

    void record_qubit(uint32_t qubit, uint32_t value);

    uint32_t resolve_clbit(uint32_t clbit) const;

    void record_clbit(uint32_t clbit, uint32_t value);

    std::vector<uint32_t> targets() const;

private:
    capnp::List<jeff::Value>::Builder values_;
    std::vector<uint32_t> qubit_to_value_;
    std::vector<uint32_t> clbit_to_value_;
    uint32_t next_value_ = 0;
};

}  // namespace QiskitToJeff
