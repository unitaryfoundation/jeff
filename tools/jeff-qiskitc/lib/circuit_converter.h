#pragma once

#include "capnp/jeff.capnp.h"
#include "value_map.h"

#include <qiskit.h>

#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <variant>
#include <vector>

namespace JeffToQiskit {

struct ResourceCount {
    uint32_t qubits = 0;
};

inline void walk_jeff_ops(jeff::Region::Reader body,
                          const std::function<void(jeff::Op::Reader)>& fn) {
    for (jeff::Op::Reader op : body.getOperations())
        fn(op);
}

// Assigns a clbit to every measurement result in `def`'s body, records it in `values`, and
// returns the number of clbits the circuit needs.
//
// jeff has no classical bits: the circuit's clbits are the int(1) values in the body's targets,
// in order. A measurement whose result is not one of them goes into a clbit that a later
// measurement overwrites (preferring one on the same qubit), or into an extra scratch clbit
// after the target clbits if there is none.
uint32_t assign_clbits(jeff::Function::Definition::Reader def, ValueMap& values);

class GateOp {
  public:
    GateOp(jeff::Op::Reader jeff_op);

    void build(QkCircuit* circuit, ValueMap& values) const;

    ResourceCount resource_count() const { return {}; }

  private:
    jeff::Op::Reader jeff_op_;
};

class AllocOp {
  public:
    AllocOp(jeff::Op::Reader jeff_op);

    void build(QkCircuit* circuit, ValueMap& values) const;

    ResourceCount resource_count() const { return {1}; }

  private:
    jeff::Op::Reader jeff_op_;
};

class MeasureNdOp {
  public:
    MeasureNdOp(jeff::Op::Reader jeff_op);

    void build(QkCircuit* circuit, ValueMap& values) const;

    ResourceCount resource_count() const { return {}; }

  private:
    jeff::Op::Reader jeff_op_;
};

class QubitOp {
  public:
    QubitOp(jeff::Op::Reader jeff_op);

    void build(QkCircuit* circuit, ValueMap& values) const;

    ResourceCount resource_count() const;

  private:
    std::variant<AllocOp, MeasureNdOp, GateOp> qubit_op_;
};

class FloatOp {
  public:
    FloatOp(jeff::Op::Reader jeff_op);

    void build(QkCircuit* circuit, ValueMap& values) const;

    ResourceCount resource_count() const { return {}; }

  private:
    jeff::Op::Reader jeff_op_;
};

// Only int.const1 is supported, as the initial value of a clbit that is never measured. It
// emits nothing: Qiskit clbits start at 0, and assign_clbits rejects a constant 1 clbit.
class IntOp {
  public:
    IntOp(jeff::Op::Reader jeff_op);

    void build(QkCircuit* circuit, ValueMap& values) const;

    ResourceCount resource_count() const { return {}; }

  private:
    jeff::Op::Reader jeff_op_;
};

class Op {
  public:
    explicit Op(jeff::Op::Reader jeff_op);

    void build(QkCircuit* circuit, ValueMap& values) const;

    ResourceCount resource_count() const;

  private:
    std::variant<QubitOp, FloatOp, IntOp> op_;
};

} // namespace JeffToQiskit

namespace QiskitToJeff {

class FloatOp {
  public:
    explicit FloatOp(double value);

    uint32_t build(capnp::List<jeff::Op>::Builder operations, uint32_t op_index,
                   ValueMap& values) const;

  private:
    double value_;
};

class AllocOp {
  public:
    explicit AllocOp(uint32_t qubit);

    void build(jeff::Op::Builder op, ValueMap& values) const;

  private:
    uint32_t qubit_;
};

// The circuit's global phase, which Qiskit keeps as an attribute and jeff as a gphase op:
// a float constant followed by an uncontrolled gphase.
class GlobalPhaseOp {
  public:
    explicit GlobalPhaseOp(double phase);

    static constexpr uint32_t num_jeff_ops() { return 2; }
    static constexpr uint32_t num_jeff_values() { return 1; }
    void build(capnp::List<jeff::Op>::Builder operations, uint32_t op_start,
               ValueMap& values) const;

  private:
    double phase_;
};

// Gives a clbit that no measurement writes its initial value, an int.const1 false, so that it
// still has an int(1) value among the targets.
class ClbitInitOp {
  public:
    explicit ClbitInitOp(uint32_t clbit);

    void build(jeff::Op::Builder op, ValueMap& values) const;

  private:
    uint32_t clbit_;
};

class MeasureNdOp {
  public:
    explicit MeasureNdOp(const QkCircuitInstruction& inst);

    uint32_t num_jeff_ops() const;
    uint32_t num_jeff_values() const;
    void build(capnp::List<jeff::Op>::Builder operations, uint32_t op_start,
               ValueMap& values) const;

  private:
    const QkCircuitInstruction& inst_;
};

class WellKnownOp {
  public:
    explicit WellKnownOp(const QkCircuitInstruction& inst);

    uint32_t num_jeff_ops() const;
    uint32_t num_jeff_values() const;
    void build(capnp::List<jeff::Op>::Builder operations, uint32_t op_start,
               ValueMap& values) const;

  private:
    const QkCircuitInstruction& inst_;
    QkGate qk_gate_;
};

class PPROp {
  public:
    PPROp(const QkCircuit* circuit, size_t index, const QkCircuitInstruction& inst);

    uint32_t num_jeff_ops() const;
    uint32_t num_jeff_values() const;
    void build(capnp::List<jeff::Op>::Builder operations, uint32_t op_start,
               ValueMap& values) const;

  private:
    const QkCircuit* circuit_;
    size_t index_;
    const QkCircuitInstruction& inst_;
};

class Op {
  public:
    Op(const QkCircuit* circuit, size_t index);
    ~Op();
    Op(const Op&) = delete;
    Op& operator=(const Op&) = delete;

    uint32_t num_jeff_ops() const;
    uint32_t num_jeff_values() const;
    void build(capnp::List<jeff::Op>::Builder operations, uint32_t op_start,
               ValueMap& values) const;

    // The clbit this instruction writes, if it is a measurement.
    std::optional<uint32_t> measured_clbit() const;

  private:
    QkCircuitInstruction inst_;
    std::variant<WellKnownOp, PPROp, MeasureNdOp> op_;
};

} // namespace QiskitToJeff
