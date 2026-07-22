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
