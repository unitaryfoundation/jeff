// Round-trip tests: QkCircuit -> jeff -> QkCircuit, checked
// instruction-by-instruction against the original. Unlike
// gate_conversion_test.cpp (one instruction at a time), these exercise
// the whole pipeline on multi-instruction circuits.
//
// Covers a Bell pair, a 10-qubit GHZ state, and a 5-qubit QFT -- all
// built only from gates this converter supports, so a lossless round
// trip is expected.
//
//   cmake --build build --target circuit_conversion_test
//   ./build/tests/circuit_conversion_test

#include "capnp/jeff.capnp.h"
#include "jeff_qiskitc.h"
#include "test_utils.h"

#include <capnp/serialize.h>
#include <gtest/gtest.h>
#include <qiskit.h>

#include <functional>
#include <string>

namespace jeff_qiskitc_test {

class CircuitRoundTripTest : public ::testing::TestWithParam<CircuitCase> {};

TEST_P(CircuitRoundTripTest, RoundTripsLosslessly) {
    const CircuitPtr original = GetParam().build();

    kj::Array<capnp::word> serialized = qiskitc_to_jeff(original.get());

    capnp::FlatArrayMessageReader reader(serialized.asPtr());
    jeff::Module::Reader mod = reader.getRoot<jeff::Module>();

    const CircuitPtr roundtripped(jeff_to_qiskitc(mod));

    expect_same_circuit(original.get(), roundtripped.get());
}

INSTANTIATE_TEST_SUITE_P(Circuits, CircuitRoundTripTest, ::testing::ValuesIn(circuit_cases()),
                         circuit_case_name);

} // namespace jeff_qiskitc_test
