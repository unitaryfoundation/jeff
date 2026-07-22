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
