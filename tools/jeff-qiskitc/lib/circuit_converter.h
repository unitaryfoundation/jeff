#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>
#include <variant>
#include <functional>

#include <qiskit.h>

#include "capnp/jeff.capnp.h"
#include "value_map.h"

namespace JeffToQiskit {

struct ResourceCount { uint32_t qubits = 0; uint32_t clbits = 0; };

inline void walk_jeff_ops(
    jeff::Region::Reader body,
    const std::function<void(jeff::Op::Reader)>& fn
) { for (jeff::Op::Reader op : body.getOperations()) fn(op); }

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

    ResourceCount resource_count() const { return {1, 0}; }

private:
    jeff::Op::Reader jeff_op_;
};

class MeasureNdOp {
public:
    MeasureNdOp(jeff::Op::Reader jeff_op);

    void build(QkCircuit* circuit, ValueMap& values) const;

    ResourceCount resource_count() const { return {0, 1}; }

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


class Op {
public:
    explicit Op(jeff::Op::Reader jeff_op);

    void build(QkCircuit* circuit, ValueMap& values) const;

    ResourceCount resource_count() const;

private:
    std::variant<QubitOp, FloatOp> op_;
};

}



namespace QiskitToJeff {


class FloatOp {
public:
    explicit FloatOp(double value);

    uint32_t build(
        capnp::List<jeff::Op>::Builder operations,
        uint32_t op_index,
        ValueMap& values
    ) const;

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

class MeasureNdOp {
public:
    explicit MeasureNdOp(const QkCircuitInstruction& inst);

    uint32_t num_jeff_ops() const;
    uint32_t num_jeff_values() const;
    void build(
        capnp::List<jeff::Op>::Builder operations,
        uint32_t op_start,
        ValueMap& values
    ) const;

private:
    const QkCircuitInstruction& inst_;
};

class WellKnownOp {
public:
    explicit WellKnownOp(const QkCircuitInstruction& inst);

    uint32_t num_jeff_ops() const;
    uint32_t num_jeff_values() const;
    void build(
        capnp::List<jeff::Op>::Builder operations,
        uint32_t op_start,
        ValueMap& values
    ) const;

private:
    const QkCircuitInstruction& inst_;
};

class PPROp {
public:
    PPROp(
        const QkCircuit* circuit,
        size_t index,
        const QkCircuitInstruction& inst
    );

    uint32_t num_jeff_ops() const;
    uint32_t num_jeff_values() const;
    void build(
        capnp::List<jeff::Op>::Builder operations,
        uint32_t op_start,
        ValueMap& values
    ) const;

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
    void build(
        capnp::List<jeff::Op>::Builder operations,
        uint32_t op_start,
        ValueMap& values
    ) const;

private:
    QkCircuitInstruction inst_;
    std::variant<WellKnownOp, PPROp, MeasureNdOp> op_;
};

}  // namespace QiskitToJeff
