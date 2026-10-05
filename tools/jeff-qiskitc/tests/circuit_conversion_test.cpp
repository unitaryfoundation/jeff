// Round-trip tests: QkCircuit -> jeff -> QkCircuit, checked
// instruction-by-instruction against the original. Unlike
// gate_conversion_test.cpp (one instruction at a time), these exercise
// the whole pipeline on multi-instruction circuits.
//
// Covers a Bell pair, a 10-qubit GHZ state, a 5-qubit QFT, and circuits
// whose clbits are measured out of order, never, or more than once -- all
// built only from operations this converter supports, so a lossless round
// trip is expected. Also checks how jeff_to_qiskitc maps returned int(1)
// values and unreturned measurement results to clbits.
//
//   cmake --build build --target jeff_qiskitc_tests
//   ./build/tests/jeff_qiskitc_tests --gtest_filter='*CircuitRoundTripTest*:*ClassicalBit*:*GlobalPhase*'

#include "capnp/jeff.capnp.h"
#include "jeff_qiskitc.h"
#include "test_utils.h"

#include <capnp/message.h>
#include <capnp/serialize.h>
#include <gtest/gtest.h>
#include <qiskit.h>

#include <cmath>
#include <cstdint>
#include <functional>
#include <numbers>
#include <string>
#include <vector>

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

//===--------------------------------------------------------------------===//
// Classical bits
//===--------------------------------------------------------------------===//

//===--------------------------------------------------------------------===//
// Global phase
//===--------------------------------------------------------------------===//

TEST(GlobalPhaseRoundTripTest, GlobalPhaseSurvivesRoundTrip) {
    CircuitPtr original(qk_circuit_new(1, 0));
    QkParam* phase = qk_param_from_double(0.37);
    qk_circuit_set_global_phase(original.get(), phase);
    qk_param_free(phase);

    auto data = qiskitc_to_jeff(original.get());
    capnp::FlatArrayMessageReader reader(data.asPtr());
    CircuitPtr rt(jeff_to_qiskitc(reader.getRoot<jeff::Module>()));

    phase = qk_circuit_global_phase(rt.get());
    double total_phase = qk_param_as_real(phase);
    qk_param_free(phase);

    // Also accept an equivalent global-phase instruction.
    for (size_t i = 0; i < qk_circuit_num_instructions(rt.get()); ++i) {
        ScopedInstruction inst(rt.get(), i);
        ASSERT_STREQ(inst->name, "global_phase");
        ASSERT_EQ(inst->num_params, 1u);
        total_phase += qk_param_as_real(inst->params[0]);
    }
    EXPECT_NEAR(std::remainder(total_phase - 0.37, 2 * std::numbers::pi), 0.0, 1e-12);
}

// qiskitc_to_jeff: a non-zero global phase becomes a float constant and an
// uncontrolled gphase on no qubits.
TEST(GlobalPhaseRoundTripTest, BecomesGphaseOp) {
    CircuitPtr original(qk_circuit_new(1, 0));
    QkParam* phase = qk_param_from_double(0.37);
    qk_circuit_set_global_phase(original.get(), phase);
    qk_param_free(phase);

    kj::Array<capnp::word> data = qiskitc_to_jeff(original.get());
    capnp::FlatArrayMessageReader reader(data.asPtr());
    auto operations =
        reader.getRoot<jeff::Module>().getFunctions()[0].getDefinition().getBody().getOperations();
    ASSERT_EQ(operations.size(), 3u) << "alloc + phase const + gphase";

    jeff::Op::Reader constant = operations[1];
    ASSERT_TRUE(constant.getInstruction().isFloat());
    EXPECT_DOUBLE_EQ(constant.getInstruction().getFloat().getConst64(), 0.37);

    jeff::Op::Reader gphase = operations[2];
    jeff::QubitGate::Reader gate = gphase.getInstruction().getQubit().getGate();
    ASSERT_TRUE(gate.isWellKnown());
    EXPECT_EQ(gate.getWellKnown(), jeff::WellKnownGate::GPHASE);
    EXPECT_EQ(gate.getControlQubits(), 0);
    ASSERT_EQ(gphase.getInputs().size(), 1u);
    EXPECT_EQ(gphase.getInputs()[0], constant.getOutputs()[0]);
    EXPECT_EQ(gphase.getOutputs().size(), 0u);
}

// qiskitc_to_jeff: a zero global phase adds no ops.
TEST(GlobalPhaseRoundTripTest, ZeroPhaseAddsNothing) {
    CircuitPtr original(qk_circuit_new(1, 0));

    kj::Array<capnp::word> data = qiskitc_to_jeff(original.get());
    capnp::FlatArrayMessageReader reader(data.asPtr());
    auto operations =
        reader.getRoot<jeff::Module>().getFunctions()[0].getDefinition().getBody().getOperations();
    EXPECT_EQ(operations.size(), 1u) << "just the alloc";
}

// A Qiskit global_phase instruction comes back as the global phase attribute.
TEST(GlobalPhaseRoundTripTest, InstructionBecomesAttribute) {
    CircuitPtr original(qk_circuit_new(1, 0));
    double angle = 0.37;
    qk_circuit_gate(original.get(), QkGate_GlobalPhase, nullptr, &angle);

    auto data = qiskitc_to_jeff(original.get());
    capnp::FlatArrayMessageReader reader(data.asPtr());
    CircuitPtr rt(jeff_to_qiskitc(reader.getRoot<jeff::Module>()));

    EXPECT_EQ(qk_circuit_num_instructions(rt.get()), 0u);
    expect_same_phase(global_phase_of(rt.get()), 0.37);
}

// qiskitc_to_jeff: a clbit no measurement writes is returned as an int(1) value,
// not as whatever value happens to have index 0.
TEST(ClassicalBitTest, UnmeasuredClassicalBitHasBitType) {
    const CircuitPtr original(qk_circuit_new(1, 2));
    qk_circuit_measure(original.get(), 0, 0); // Classical bit 1 stays unmeasured.

    kj::Array<capnp::word> data = qiskitc_to_jeff(original.get());
    capnp::FlatArrayMessageReader reader(data.asPtr());
    auto def = reader.getRoot<jeff::Module>().getFunctions()[0].getDefinition();
    auto targets = def.getBody().getTargets();

    ASSERT_EQ(targets.size(), 3u); // One qubit, then two classical bits.
    auto type = def.getValues()[targets[2]].getType();
    ASSERT_TRUE(type.isInt()) << "Classical bit 1 refers to value " << targets[2];
    EXPECT_EQ(type.getInt(), 1u);
}

// Builds a module with one function whose values have the given types; the
// caller fills in the body's operations and targets.
jeff::Region::Builder build_module(capnp::MessageBuilder& message,
                                   const std::vector<bool>& value_is_qubit) {
    jeff::Module::Builder mod = message.initRoot<jeff::Module>();
    mod.setVersion(jeff::SCHEMA_VERSION_MAJOR);
    mod.setVersionMinor(jeff::SCHEMA_VERSION_MINOR);
    mod.setVersionPatch(jeff::SCHEMA_VERSION_PATCH);
    mod.setEntrypoint(0);
    mod.initStrings(1).set(0, "classical_bit_test");

    jeff::Function::Builder fn = mod.initFunctions(1)[0];
    fn.setName(0);
    jeff::Function::Definition::Builder def = fn.initDefinition();

    auto values = def.initValues(static_cast<unsigned int>(value_is_qubit.size()));
    for (size_t i = 0; i < value_is_qubit.size(); i++) {
        if (value_is_qubit[i])
            values[i].initType().setQubit();
        else
            values[i].initType().setInt(1);
    }

    jeff::Region::Builder body = def.initBody();
    body.initSources(0);
    return body;
}

void set_alloc(jeff::Op::Builder op, uint32_t qubit) {
    op.initInputs(0);
    op.initOutputs(1).set(0, qubit);
    op.getInstruction().initQubit().setAlloc();
}

void set_measure_nd(jeff::Op::Builder op, uint32_t qubit_in, uint32_t qubit_out, uint32_t bit) {
    op.initInputs(1).set(0, qubit_in);
    op.initOutputs(2);
    op.getOutputs().set(0, qubit_out);
    op.getOutputs().set(1, bit);
    op.getInstruction().initQubit().setMeasureNd();
}

void set_const1(jeff::Op::Builder op, uint32_t bit, bool value) {
    op.initInputs(0);
    op.initOutputs(1).set(0, bit);
    op.getInstruction().initInt().setConst1(value);
}

void set_targets(jeff::Region::Builder body, const std::vector<uint32_t>& targets) {
    auto list = body.initTargets(static_cast<unsigned int>(targets.size()));
    for (size_t i = 0; i < targets.size(); i++)
        list.set(i, targets[i]);
}

// jeff_to_qiskitc: a measurement whose result is not returned, and whose clbit
// no later measurement overwrites, gets a scratch clbit.
TEST(ClassicalBitTest, DiscardedMeasurementGetsScratchClbit) {
    capnp::MallocMessageBuilder message;
    // v0 = alloc; (v1, v2) = measureNd(v0); return v1
    jeff::Region::Builder body = build_module(message, {true, true, false});
    auto operations = body.initOperations(2);
    set_alloc(operations[0], 0);
    set_measure_nd(operations[1], 0, 1, 2);
    set_targets(body, {1});

    const CircuitPtr circuit(jeff_to_qiskitc(message.getRoot<jeff::Module>().asReader()));

    EXPECT_EQ(qk_circuit_num_qubits(circuit.get()), 1u);
    EXPECT_EQ(qk_circuit_num_clbits(circuit.get()), 1u);
    ASSERT_EQ(qk_circuit_num_instructions(circuit.get()), 1u);
    const ScopedInstruction inst(circuit.get(), 0);
    EXPECT_STREQ(inst->name, "measure");
    EXPECT_EQ(inst->clbits[0], 0u);
}

// jeff_to_qiskitc: a clbit returned as the constant 0 is a clbit no instruction writes.
TEST(ClassicalBitTest, ConstantZeroIsUnwrittenClbit) {
    capnp::MallocMessageBuilder message;
    // v0 = const1 false; return v0
    jeff::Region::Builder body = build_module(message, {false});
    auto operations = body.initOperations(1);
    set_const1(operations[0], 0, false);
    set_targets(body, {0});

    const CircuitPtr circuit(jeff_to_qiskitc(message.getRoot<jeff::Module>().asReader()));

    EXPECT_EQ(qk_circuit_num_clbits(circuit.get()), 1u);
    EXPECT_EQ(qk_circuit_num_instructions(circuit.get()), 0u);
}

TEST(ClassicalBitDeathTest, RejectsConstantOneClbit) {
    GTEST_FLAG_SET(death_test_style, "threadsafe");
    capnp::MallocMessageBuilder message;
    // v0 = const1 true; return v0
    jeff::Region::Builder body = build_module(message, {false});
    auto operations = body.initOperations(1);
    set_const1(operations[0], 0, true);
    set_targets(body, {0});

    EXPECT_EXIT({ jeff_to_qiskitc(message.getRoot<jeff::Module>().asReader()); },
                ::testing::ExitedWithCode(1), "constant 1");
}

TEST(ClassicalBitDeathTest, RejectsClbitReturnedTwice) {
    GTEST_FLAG_SET(death_test_style, "threadsafe");
    capnp::MallocMessageBuilder message;
    // v0 = alloc; (v1, v2) = measureNd(v0); return v1, v2, v2
    jeff::Region::Builder body = build_module(message, {true, true, false});
    auto operations = body.initOperations(2);
    set_alloc(operations[0], 0);
    set_measure_nd(operations[1], 0, 1, 2);
    set_targets(body, {1, 2, 2});

    EXPECT_EXIT({ jeff_to_qiskitc(message.getRoot<jeff::Module>().asReader()); },
                ::testing::ExitedWithCode(1), "more than once");
}

} // namespace jeff_qiskitc_test
