//! Verification helpers for jeff programs.

use std::collections::{HashMap, HashSet};

use derive_more::derive::{Display, Error};

use crate::reader::optype::{ControlFlowOp, FloatOp, IntOp, OpType, QubitOp};
use crate::reader::value::ValueId;
use crate::reader::{Function, FunctionId, Module, Operation, ReadError, ReadJeff, Region};
use crate::types::Type;
use crate::SCHEMA_VERSION;

/// A structural verification error found in a jeff program.
#[derive(Debug, Display, Error)]
#[non_exhaustive]
pub enum VerificationError {
    /// The encoded jeff schema version is too old for this reader.
    #[display("Schema version {actual} is too old. Expected at least {expected}")]
    VersionTooOld {
        /// The encoded schema version.
        actual: semver::Version,
        /// The minimum supported schema version.
        expected: semver::Version,
    },
    /// The encoded jeff schema version is too new for this reader.
    #[display("Schema version {actual} is too new. Expected at most {expected}")]
    VersionTooNew {
        /// The encoded schema version.
        actual: semver::Version,
        /// The maximum supported schema version.
        expected: semver::Version,
    },
    /// The module entrypoint points outside the function table.
    #[display("Entrypoint function {entrypoint} is out of bounds for {function_count} functions")]
    InvalidEntrypoint {
        /// The encoded entrypoint function id.
        entrypoint: FunctionId,
        /// The number of functions in the module.
        function_count: usize,
    },
    /// A function call points outside the module function table.
    #[display("Function {function} calls missing function {callee}")]
    InvalidFunctionCall {
        /// The function being verified.
        function: FunctionId,
        /// The missing callee id.
        callee: FunctionId,
    },
    /// A value was consumed before being produced or listed as a region input.
    #[display("Function {function} uses value {value} before it is defined")]
    ValueUsedBeforeDefined {
        /// The function being verified.
        function: FunctionId,
        /// The value id that was used too early.
        value: ValueId,
    },
    /// A region output was not produced in the region.
    #[display("Function {function} returns value {value} before it is defined")]
    UndefinedRegionOutput {
        /// The function being verified.
        function: FunctionId,
        /// The region output value id.
        value: ValueId,
    },
    /// Reading an encoded value failed.
    #[display("Function {function}: {source}")]
    Read {
        /// The function being verified.
        function: FunctionId,
        /// The read error.
        source: ReadError,
    },
    /// A value has a type that is not accepted by the operation boundary.
    #[display(
        "Function {function}: {op} {direction} {index} has type {actual}, expected {expected}"
    )]
    TypeMismatch {
        /// The function being verified.
        function: FunctionId,
        /// Human-readable operation family.
        op: &'static str,
        /// Input or output boundary.
        direction: &'static str,
        /// Boundary index.
        index: usize,
        /// Actual type.
        actual: Type,
        /// Expected type description.
        expected: &'static str,
    },
    /// An operation boundary has the wrong number of values.
    #[display("Function {function}: {op} has {actual} {direction} values, expected {expected}")]
    ArityMismatch {
        /// The function being verified.
        function: FunctionId,
        /// Human-readable operation family.
        op: &'static str,
        /// Input or output boundary.
        direction: &'static str,
        /// Actual number of values.
        actual: usize,
        /// Expected number of values.
        expected: usize,
    },
    /// An operation requires matching operand/result types.
    #[display("Function {function}: {op} values must have matching {kind}")]
    InconsistentTypes {
        /// The function being verified.
        function: FunctionId,
        /// Human-readable operation family.
        op: &'static str,
        /// What must match.
        kind: &'static str,
    },
    /// A nested region captures a value that is not explicitly supplied to the operation.
    #[display("Function {function}: nested region captures value {value} from above")]
    RegionNotIsolated {
        /// The function being verified.
        function: FunctionId,
        /// The captured value.
        value: ValueId,
    },
    /// A linear value is not consumed exactly once.
    #[display("Function {function}: linear value {value} is used {uses} times")]
    LinearValueUse {
        /// The function being verified.
        function: FunctionId,
        /// The linear value.
        value: ValueId,
        /// Number of consuming uses.
        uses: usize,
    },
}

/// Verify a jeff program and return all structural errors found.
pub fn verify(program: &impl ReadJeff) -> Result<(), Vec<VerificationError>> {
    verify_module(program.module())
}

/// Verify a module view and return all structural errors found.
pub fn verify_module(module: Module<'_>) -> Result<(), Vec<VerificationError>> {
    let mut errors = Vec::new();

    verify_version(module, &mut errors);

    if module.try_function(module.entrypoint_id()).is_none() {
        errors.push(VerificationError::InvalidEntrypoint {
            entrypoint: module.entrypoint_id(),
            function_count: module.function_count(),
        });
    }

    for (function_id, function) in module.functions().enumerate() {
        let function_id = function_id as FunctionId;
        verify_function_signature(function_id, function, &mut errors);
        if let Function::Definition(definition) = function {
            verify_region(
                function_id,
                definition.body(),
                module.function_count(),
                &mut errors,
            );
        }
    }

    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors)
    }
}

fn verify_version(module: Module<'_>, errors: &mut Vec<VerificationError>) {
    let version = module.version();
    if version.major < SCHEMA_VERSION.major {
        errors.push(VerificationError::VersionTooOld {
            actual: version,
            expected: SCHEMA_VERSION,
        });
    } else if version.major > SCHEMA_VERSION.major {
        errors.push(VerificationError::VersionTooNew {
            actual: version,
            expected: SCHEMA_VERSION,
        });
    }
}

fn verify_function_signature(
    function_id: FunctionId,
    function: Function<'_>,
    errors: &mut Vec<VerificationError>,
) {
    for input in function.input_types() {
        if let Err(source) = input {
            errors.push(VerificationError::Read {
                function: function_id,
                source,
            });
        }
    }

    for output in function.output_types() {
        if let Err(source) = output {
            errors.push(VerificationError::Read {
                function: function_id,
                source,
            });
        }
    }
}

fn verify_region(
    function_id: FunctionId,
    region: Region<'_>,
    function_count: usize,
    errors: &mut Vec<VerificationError>,
) {
    let mut defined = HashSet::new();
    let mut linear_defined = HashSet::new();
    let mut linear_uses = HashMap::<ValueId, usize>::new();

    for source in region.sources() {
        match source {
            Ok(value) => {
                defined.insert(value.id());
                if is_linear(value.ty()) {
                    linear_defined.insert(value.id());
                }
            }
            Err(source) => errors.push(VerificationError::Read {
                function: function_id,
                source,
            }),
        }
    }

    for operation in region.operations() {
        for input in operation.inputs() {
            match input {
                Ok(value) if !defined.contains(&value.id()) => {
                    errors.push(VerificationError::ValueUsedBeforeDefined {
                        function: function_id,
                        value: value.id(),
                    });
                }
                Ok(value) => {
                    if is_linear(value.ty()) {
                        *linear_uses.entry(value.id()).or_default() += 1;
                    }
                }
                Err(source) => errors.push(VerificationError::Read {
                    function: function_id,
                    source,
                }),
            }
        }

        verify_operation(function_id, operation, function_count, errors);

        for output in operation.outputs() {
            match output {
                Ok(value) => {
                    defined.insert(value.id());
                    if is_linear(value.ty()) {
                        linear_defined.insert(value.id());
                    }
                }
                Err(source) => errors.push(VerificationError::Read {
                    function: function_id,
                    source,
                }),
            }
        }
    }

    for target in region.targets() {
        match target {
            Ok(value) if !defined.contains(&value.id()) => {
                errors.push(VerificationError::UndefinedRegionOutput {
                    function: function_id,
                    value: value.id(),
                });
            }
            Ok(value) => {
                if is_linear(value.ty()) {
                    *linear_uses.entry(value.id()).or_default() += 1;
                }
            }
            Err(source) => errors.push(VerificationError::Read {
                function: function_id,
                source,
            }),
        }
    }

    for value in linear_defined {
        let uses = *linear_uses.get(&value).unwrap_or(&0);
        if uses != 1 {
            errors.push(VerificationError::LinearValueUse {
                function: function_id,
                value,
                uses,
            });
        }
    }
}

fn verify_operation(
    function_id: FunctionId,
    operation: Operation<'_>,
    function_count: usize,
    errors: &mut Vec<VerificationError>,
) {
    let op_type = operation.op_type();
    verify_op_signature(function_id, operation, &op_type, errors);
    verify_nested_regions(function_id, operation, op_type, function_count, errors);
}

fn verify_nested_regions(
    function_id: FunctionId,
    operation: Operation<'_>,
    op_type: OpType<'_>,
    function_count: usize,
    errors: &mut Vec<VerificationError>,
) {
    let supplied = operation
        .inputs()
        .filter_map(Result::ok)
        .map(|value| value.id())
        .collect::<HashSet<_>>();

    match op_type {
        OpType::ControlFlowOp(control_flow) => match *control_flow {
            ControlFlowOp::Switch(switch) => {
                for branch in switch.branches() {
                    verify_region_isolated(function_id, branch, &supplied, errors);
                    verify_region(function_id, branch, function_count, errors);
                }
                if let Some(default) = switch.default_branch() {
                    verify_region_isolated(function_id, default, &supplied, errors);
                    verify_region(function_id, default, function_count, errors);
                }
            }
            ControlFlowOp::For { region } => {
                verify_region_isolated(function_id, region, &supplied, errors);
                verify_region(function_id, region, function_count, errors);
            }
            ControlFlowOp::While { condition, body } => {
                verify_region_isolated(function_id, condition, &supplied, errors);
                verify_region(function_id, condition, function_count, errors);
                verify_region_isolated(function_id, body, &supplied, errors);
                verify_region(function_id, body, function_count, errors);
            }
            ControlFlowOp::DoWhile { body, condition } => {
                verify_region_isolated(function_id, body, &supplied, errors);
                verify_region(function_id, body, function_count, errors);
                verify_region_isolated(function_id, condition, &supplied, errors);
                verify_region(function_id, condition, function_count, errors);
            }
        },
        OpType::FuncOp(func) if usize::from(func.func_idx) >= function_count => {
            errors.push(VerificationError::InvalidFunctionCall {
                function: function_id,
                callee: FunctionId::from(func.func_idx),
            });
        }
        _ => {}
    }
}

fn verify_region_isolated(
    function_id: FunctionId,
    region: Region<'_>,
    supplied: &HashSet<ValueId>,
    errors: &mut Vec<VerificationError>,
) {
    for source in region.sources() {
        match source {
            Ok(value) if !supplied.contains(&value.id()) => {
                errors.push(VerificationError::RegionNotIsolated {
                    function: function_id,
                    value: value.id(),
                });
            }
            Ok(_) => {}
            Err(source) => errors.push(VerificationError::Read {
                function: function_id,
                source,
            }),
        }
    }
}

fn verify_op_signature(
    function_id: FunctionId,
    operation: Operation<'_>,
    op_type: &OpType<'_>,
    errors: &mut Vec<VerificationError>,
) {
    match op_type {
        OpType::IntOp(op) => verify_int_op(function_id, operation, *op, errors),
        OpType::FloatOp(op) => verify_float_op(function_id, operation, *op, errors),
        OpType::QubitOp(op) => verify_qubit_op(function_id, operation, op, errors),
        OpType::FuncOp(_) | OpType::ControlFlowOp(_) => {}
        OpType::QubitRegisterOp(_) | OpType::IntArrayOp(_) | OpType::FloatArrayOp(_) => {}
    }
}

fn verify_int_op(
    function_id: FunctionId,
    operation: Operation<'_>,
    op: IntOp,
    errors: &mut Vec<VerificationError>,
) {
    use IntOp::*;
    match op {
        Const1(_) => expect_exact(
            function_id,
            operation,
            "int.const1",
            0,
            1,
            errors,
            |_, ty| matches!(ty, Type::Int { bits: 1 }),
        ),
        Const8(_) => expect_exact(
            function_id,
            operation,
            "int.const8",
            0,
            1,
            errors,
            |_, ty| matches!(ty, Type::Int { bits: 8 }),
        ),
        Const16(_) => expect_exact(
            function_id,
            operation,
            "int.const16",
            0,
            1,
            errors,
            |_, ty| matches!(ty, Type::Int { bits: 16 }),
        ),
        Const32(_) => expect_exact(
            function_id,
            operation,
            "int.const32",
            0,
            1,
            errors,
            |_, ty| matches!(ty, Type::Int { bits: 32 }),
        ),
        Const64(_) => expect_exact(
            function_id,
            operation,
            "int.const64",
            0,
            1,
            errors,
            |_, ty| matches!(ty, Type::Int { bits: 64 }),
        ),
        Eq | LtS | LteS | LtU | LteU => {
            expect_int_boundary(function_id, operation, "int.compare", 2, 1, errors);
            expect_matching_ints(function_id, operation, "int.compare", false, errors);
            expect_output_type(
                function_id,
                operation,
                "int.compare",
                0,
                "Int1",
                errors,
                |ty| matches!(ty, Type::Int { bits: 1 }),
            );
        }
        Not | Abs => {
            expect_int_boundary(function_id, operation, "int.unary", 1, 1, errors);
            expect_matching_ints(function_id, operation, "int.unary", true, errors);
        }
        Add | Sub | Mul | DivS | DivU | Pow | And | Or | Xor | MinS | MinU | MaxS | MaxU | RemS
        | RemU | Shl | Shr => {
            expect_int_boundary(function_id, operation, "int.binary", 2, 1, errors);
            expect_matching_ints(function_id, operation, "int.binary", true, errors);
        }
    }
}

fn verify_float_op(
    function_id: FunctionId,
    operation: Operation<'_>,
    op: FloatOp,
    errors: &mut Vec<VerificationError>,
) {
    use FloatOp::*;
    match op {
        Const32(_) => expect_exact(
            function_id,
            operation,
            "float.const32",
            0,
            1,
            errors,
            |_, ty| {
                matches!(
                    ty,
                    Type::Float {
                        precision: crate::types::FloatPrecision::Float32
                    }
                )
            },
        ),
        Const64(_) => expect_exact(
            function_id,
            operation,
            "float.const64",
            0,
            1,
            errors,
            |_, ty| {
                matches!(
                    ty,
                    Type::Float {
                        precision: crate::types::FloatPrecision::Float64
                    }
                )
            },
        ),
        Eq | Lt | Lte => {
            expect_float_boundary(function_id, operation, "float.compare", 2, 1, errors);
            expect_matching_floats(function_id, operation, "float.compare", false, errors);
            expect_output_type(
                function_id,
                operation,
                "float.compare",
                0,
                "Int1",
                errors,
                |ty| matches!(ty, Type::Int { bits: 1 }),
            );
        }
        IsNan | IsInf => {
            expect_float_boundary(function_id, operation, "float.predicate", 1, 1, errors);
            expect_output_type(
                function_id,
                operation,
                "float.predicate",
                0,
                "Int1",
                errors,
                |ty| matches!(ty, Type::Int { bits: 1 }),
            );
        }
        Sqrt | Abs | Ceil | Floor | Exp | Log | Sin | Cos | Tan | Asin | Acos | Atan | Sinh
        | Cosh | Tanh | Asinh | Acosh | Atanh => {
            expect_float_boundary(function_id, operation, "float.unary", 1, 1, errors);
            expect_matching_floats(function_id, operation, "float.unary", true, errors);
        }
        Add | Sub | Mul | Pow | Max | Min | Atan2 => {
            expect_float_boundary(function_id, operation, "float.binary", 2, 1, errors);
            expect_matching_floats(function_id, operation, "float.binary", true, errors);
        }
    }
}

fn verify_qubit_op(
    function_id: FunctionId,
    operation: Operation<'_>,
    op: &QubitOp<'_>,
    errors: &mut Vec<VerificationError>,
) {
    match op {
        QubitOp::Alloc => expect_exact(
            function_id,
            operation,
            "qubit.alloc",
            0,
            1,
            errors,
            |_, ty| matches!(ty, Type::Qubit),
        ),
        QubitOp::Free | QubitOp::FreeZero => expect_exact(
            function_id,
            operation,
            "qubit.free",
            1,
            0,
            errors,
            |_, ty| matches!(ty, Type::Qubit),
        ),
        QubitOp::Measure => expect_exact(
            function_id,
            operation,
            "qubit.measure",
            1,
            1,
            errors,
            |direction, ty| {
                if direction == "input" {
                    matches!(ty, Type::Qubit)
                } else {
                    matches!(ty, Type::Int { bits: 1 })
                }
            },
        ),
        QubitOp::MeasureNd => {
            expect_arity(function_id, operation, "qubit.measure_nd", 1, 2, errors);
            expect_input_type(
                function_id,
                operation,
                "qubit.measure_nd",
                0,
                "Qubit",
                errors,
                |ty| matches!(ty, Type::Qubit),
            );
            expect_output_type(
                function_id,
                operation,
                "qubit.measure_nd",
                0,
                "Qubit",
                errors,
                |ty| matches!(ty, Type::Qubit),
            );
            expect_output_type(
                function_id,
                operation,
                "qubit.measure_nd",
                1,
                "Int1",
                errors,
                |ty| matches!(ty, Type::Int { bits: 1 }),
            );
        }
        QubitOp::Reset => expect_exact(
            function_id,
            operation,
            "qubit.reset",
            1,
            1,
            errors,
            |_, ty| matches!(ty, Type::Qubit),
        ),
        QubitOp::Gate(gate) => {
            expect_arity(
                function_id,
                operation,
                "qubit.gate",
                gate.num_qubits() + gate.num_params(),
                gate.num_qubits(),
                errors,
            );
            for index in 0..gate.num_qubits() {
                expect_input_type(
                    function_id,
                    operation,
                    "qubit.gate",
                    index,
                    "Qubit",
                    errors,
                    |ty| matches!(ty, Type::Qubit),
                );
                expect_output_type(
                    function_id,
                    operation,
                    "qubit.gate",
                    index,
                    "Qubit",
                    errors,
                    |ty| matches!(ty, Type::Qubit),
                );
            }
            for index in gate.num_qubits()..(gate.num_qubits() + gate.num_params()) {
                expect_input_type(
                    function_id,
                    operation,
                    "qubit.gate",
                    index,
                    "Float",
                    errors,
                    |ty| matches!(ty, Type::Float { .. }),
                );
            }
        }
    }
}

fn expect_exact(
    function_id: FunctionId,
    operation: Operation<'_>,
    op: &'static str,
    inputs: usize,
    outputs: usize,
    errors: &mut Vec<VerificationError>,
    type_ok: impl Fn(&'static str, Type) -> bool,
) {
    expect_arity(function_id, operation, op, inputs, outputs, errors);
    for (index, input) in operation.inputs().filter_map(Result::ok).enumerate() {
        if !type_ok("input", input.ty()) {
            errors.push(VerificationError::TypeMismatch {
                function: function_id,
                op,
                direction: "input",
                index,
                actual: input.ty(),
                expected: "operation-specific type",
            });
        }
    }
    for (index, output) in operation.outputs().filter_map(Result::ok).enumerate() {
        if !type_ok("output", output.ty()) {
            errors.push(VerificationError::TypeMismatch {
                function: function_id,
                op,
                direction: "output",
                index,
                actual: output.ty(),
                expected: "operation-specific type",
            });
        }
    }
}

fn expect_arity(
    function_id: FunctionId,
    operation: Operation<'_>,
    op: &'static str,
    inputs: usize,
    outputs: usize,
    errors: &mut Vec<VerificationError>,
) {
    let actual_inputs = operation.input_count();
    if actual_inputs != inputs {
        errors.push(VerificationError::ArityMismatch {
            function: function_id,
            op,
            direction: "input",
            actual: actual_inputs,
            expected: inputs,
        });
    }

    let actual_outputs = operation.output_count();
    if actual_outputs != outputs {
        errors.push(VerificationError::ArityMismatch {
            function: function_id,
            op,
            direction: "output",
            actual: actual_outputs,
            expected: outputs,
        });
    }
}

fn expect_input_type(
    function_id: FunctionId,
    operation: Operation<'_>,
    op: &'static str,
    index: usize,
    expected: &'static str,
    errors: &mut Vec<VerificationError>,
    type_ok: impl Fn(Type) -> bool,
) {
    if let Some(Ok(value)) = operation.input(index) {
        if !type_ok(value.ty()) {
            errors.push(VerificationError::TypeMismatch {
                function: function_id,
                op,
                direction: "input",
                index,
                actual: value.ty(),
                expected,
            });
        }
    }
}

fn expect_output_type(
    function_id: FunctionId,
    operation: Operation<'_>,
    op: &'static str,
    index: usize,
    expected: &'static str,
    errors: &mut Vec<VerificationError>,
    type_ok: impl Fn(Type) -> bool,
) {
    if let Some(Ok(value)) = operation.output(index) {
        if !type_ok(value.ty()) {
            errors.push(VerificationError::TypeMismatch {
                function: function_id,
                op,
                direction: "output",
                index,
                actual: value.ty(),
                expected,
            });
        }
    }
}

fn expect_int_boundary(
    function_id: FunctionId,
    operation: Operation<'_>,
    op: &'static str,
    inputs: usize,
    outputs: usize,
    errors: &mut Vec<VerificationError>,
) {
    expect_arity(function_id, operation, op, inputs, outputs, errors);
    for (index, input) in operation.inputs().filter_map(Result::ok).enumerate() {
        if !matches!(input.ty(), Type::Int { .. }) {
            errors.push(VerificationError::TypeMismatch {
                function: function_id,
                op,
                direction: "input",
                index,
                actual: input.ty(),
                expected: "Int",
            });
        }
    }
    for (index, output) in operation.outputs().filter_map(Result::ok).enumerate() {
        if !matches!(output.ty(), Type::Int { .. }) {
            errors.push(VerificationError::TypeMismatch {
                function: function_id,
                op,
                direction: "output",
                index,
                actual: output.ty(),
                expected: "Int",
            });
        }
    }
}

fn expect_float_boundary(
    function_id: FunctionId,
    operation: Operation<'_>,
    op: &'static str,
    inputs: usize,
    outputs: usize,
    errors: &mut Vec<VerificationError>,
) {
    expect_arity(function_id, operation, op, inputs, outputs, errors);
    for (index, input) in operation.inputs().filter_map(Result::ok).enumerate() {
        if !matches!(input.ty(), Type::Float { .. }) {
            errors.push(VerificationError::TypeMismatch {
                function: function_id,
                op,
                direction: "input",
                index,
                actual: input.ty(),
                expected: "Float",
            });
        }
    }
    for (index, output) in operation.outputs().filter_map(Result::ok).enumerate() {
        if !matches!(output.ty(), Type::Float { .. }) {
            errors.push(VerificationError::TypeMismatch {
                function: function_id,
                op,
                direction: "output",
                index,
                actual: output.ty(),
                expected: "Float",
            });
        }
    }
}

fn expect_matching_ints(
    function_id: FunctionId,
    operation: Operation<'_>,
    op: &'static str,
    include_outputs: bool,
    errors: &mut Vec<VerificationError>,
) {
    let mut types = operation
        .inputs()
        .filter_map(Result::ok)
        .filter_map(|value| match value.ty() {
            Type::Int { bits } => Some(bits),
            _ => None,
        })
        .collect::<Vec<_>>();
    if include_outputs {
        types.extend(operation.outputs().filter_map(Result::ok).filter_map(
            |value| match value.ty() {
                Type::Int { bits } => Some(bits),
                _ => None,
            },
        ));
    }
    if let Some(first) = types.first() {
        if types.iter().any(|bits| bits != first) {
            errors.push(VerificationError::InconsistentTypes {
                function: function_id,
                op,
                kind: "integer bitwidths",
            });
        }
    }
}

fn expect_matching_floats(
    function_id: FunctionId,
    operation: Operation<'_>,
    op: &'static str,
    include_outputs: bool,
    errors: &mut Vec<VerificationError>,
) {
    let mut types = operation
        .inputs()
        .filter_map(Result::ok)
        .filter_map(|value| match value.ty() {
            Type::Float { precision } => Some(precision),
            _ => None,
        })
        .collect::<Vec<_>>();
    if include_outputs {
        types.extend(operation.outputs().filter_map(Result::ok).filter_map(
            |value| match value.ty() {
                Type::Float { precision } => Some(precision),
                _ => None,
            },
        ));
    }
    if let Some(first) = types.first() {
        if types.iter().any(|precision| precision != first) {
            errors.push(VerificationError::InconsistentTypes {
                function: function_id,
                op,
                kind: "float precisions",
            });
        }
    }
}

fn is_linear(ty: Type) -> bool {
    matches!(ty, Type::Qubit | Type::QubitRegister { .. })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::jeff_capnp;
    use crate::types::FloatPrecision;

    #[rstest::rstest]
    fn verifies_examples(
        #[values(
            crate::test::qubits(),
            crate::test::entangled_qs(),
            crate::test::entangled_calls()
        )]
        program: crate::Jeff<'static>,
    ) {
        verify(&program).unwrap();
    }

    #[test]
    fn reports_invalid_entrypoint() {
        let mut message = capnp::message::Builder::new_default();
        let mut module_builder = message.init_root::<jeff_capnp::module::Builder>();
        module_builder.set_version(SCHEMA_VERSION.major as u32);
        module_builder.set_version_minor(SCHEMA_VERSION.minor as u32);
        module_builder.set_version_patch(SCHEMA_VERSION.patch as u32);
        module_builder.reborrow().init_functions(0);
        module_builder.reborrow().init_strings(0);
        module_builder.reborrow().init_metadata(0);
        module_builder.set_entrypoint(1);
        let module = Module::read_capnp(module_builder.reborrow_as_reader());

        let errors = verify_module(module).unwrap_err();

        assert!(errors
            .iter()
            .any(|error| matches!(error, VerificationError::InvalidEntrypoint { .. })));
    }

    #[test]
    fn reports_value_used_before_defined() {
        let errors = invalid_single_op(
            &[Type::int(32), Type::int(32)],
            &[],
            &[1],
            &[0],
            &[1],
            |instruction| instruction.init_int().set_const32(1),
        );

        assert_has(&errors, |error| {
            matches!(error, VerificationError::ValueUsedBeforeDefined { .. })
        });
    }

    #[test]
    fn reports_body_value_out_of_bounds() {
        let errors = invalid_single_op(&[Type::int(32)], &[], &[], &[1], &[], |instruction| {
            instruction.init_int().set_const32(1)
        });

        assert_has(&errors, |error| {
            matches!(
                error,
                VerificationError::Read {
                    source: ReadError::ValueOutOfBounds { .. },
                    ..
                }
            )
        });
    }

    #[test]
    fn reports_int_operand_type_mismatch() {
        let errors = invalid_single_op(
            &[
                Type::int(32),
                Type::float(FloatPrecision::Float32),
                Type::int(32),
            ],
            &[0, 1],
            &[2],
            &[0, 1],
            &[2],
            |instruction| instruction.init_int().set_add(()),
        );

        assert_has(&errors, |error| {
            matches!(error, VerificationError::TypeMismatch { .. })
        });
    }

    #[test]
    fn reports_int_bitwidth_mismatch() {
        let errors = invalid_single_op(
            &[Type::int(32), Type::int(64), Type::int(32)],
            &[0, 1],
            &[2],
            &[0, 1],
            &[2],
            |instruction| instruction.init_int().set_add(()),
        );

        assert_has(&errors, |error| {
            matches!(error, VerificationError::InconsistentTypes { .. })
        });
    }

    #[test]
    fn reports_float_precision_mismatch() {
        let errors = invalid_single_op(
            &[
                Type::float(FloatPrecision::Float32),
                Type::float(FloatPrecision::Float64),
                Type::float(FloatPrecision::Float32),
            ],
            &[0, 1],
            &[2],
            &[0, 1],
            &[2],
            |instruction| instruction.init_float().set_add(()),
        );

        assert_has(&errors, |error| {
            matches!(error, VerificationError::InconsistentTypes { .. })
        });
    }

    #[test]
    fn reports_linear_value_reused() {
        let errors = invalid_single_op(&[Type::Qubit], &[0], &[], &[0, 0], &[], |instruction| {
            instruction.init_qubit().set_free(())
        });

        assert_has(&errors, |error| {
            matches!(error, VerificationError::LinearValueUse { uses: 2, .. })
        });
    }

    #[test]
    fn reports_nested_region_capture() {
        let mut message = capnp::message::Builder::new_default();
        let mut module_builder = message.init_root::<jeff_capnp::module::Builder>();
        init_module_header(module_builder.reborrow());
        let mut functions = module_builder.reborrow().init_functions(1);
        let mut function = functions.reborrow().get(0);
        function.set_name(0);
        function.reborrow().init_metadata(0);
        let mut definition = function.init_definition();
        let mut values = definition.reborrow().init_values(1);
        init_value(values.reborrow().get(0), Type::int(1));
        let mut body = definition.reborrow().init_body();
        set_indices(body.reborrow().init_sources(0), &[]);
        set_indices(body.reborrow().init_targets(0), &[]);
        body.reborrow().init_metadata(0);
        let mut ops = body.reborrow().init_operations(1);
        let mut op = ops.reborrow().get(0);
        set_indices(op.reborrow().init_inputs(0), &[]);
        set_indices(op.reborrow().init_outputs(0), &[]);
        op.reborrow().init_metadata(0);
        let mut for_region = op.reborrow().init_instruction().init_scf().init_for();
        set_indices(for_region.reborrow().init_sources(1), &[0]);
        set_indices(for_region.reborrow().init_targets(0), &[]);
        for_region.reborrow().init_operations(0);
        for_region.reborrow().init_metadata(0);

        let module = Module::read_capnp(module_builder.reborrow_as_reader());
        let errors = verify_module(module).unwrap_err();

        assert_has(&errors, |error| {
            matches!(error, VerificationError::RegionNotIsolated { .. })
        });
    }

    fn invalid_single_op(
        types: &[Type],
        sources: &[ValueId],
        targets: &[ValueId],
        inputs: &[ValueId],
        outputs: &[ValueId],
        set_instruction: impl FnOnce(jeff_capnp::op::instruction::Builder<'_>),
    ) -> Vec<VerificationError> {
        let mut message = capnp::message::Builder::new_default();
        let mut module_builder = message.init_root::<jeff_capnp::module::Builder>();
        init_module_header(module_builder.reborrow());
        let mut functions = module_builder.reborrow().init_functions(1);
        let mut function = functions.reborrow().get(0);
        function.set_name(0);
        function.reborrow().init_metadata(0);
        let mut definition = function.init_definition();
        let mut values = definition.reborrow().init_values(types.len() as u32);
        for (idx, ty) in types.iter().copied().enumerate() {
            init_value(values.reborrow().get(idx as u32), ty);
        }
        let mut body = definition.reborrow().init_body();
        set_indices(body.reborrow().init_sources(sources.len() as u32), sources);
        set_indices(body.reborrow().init_targets(targets.len() as u32), targets);
        body.reborrow().init_metadata(0);
        let mut ops = body.reborrow().init_operations(1);
        let mut op = ops.reborrow().get(0);
        set_indices(op.reborrow().init_inputs(inputs.len() as u32), inputs);
        set_indices(op.reborrow().init_outputs(outputs.len() as u32), outputs);
        op.reborrow().init_metadata(0);
        set_instruction(op.init_instruction());

        let module = Module::read_capnp(module_builder.reborrow_as_reader());
        verify_module(module).unwrap_err()
    }

    fn init_module_header(mut module: jeff_capnp::module::Builder<'_>) {
        module.set_version(SCHEMA_VERSION.major as u32);
        module.set_version_minor(SCHEMA_VERSION.minor as u32);
        module.set_version_patch(SCHEMA_VERSION.patch as u32);
        module.set_entrypoint(0);
        module.reborrow().init_strings(0);
        module.reborrow().init_metadata(0);
    }

    fn init_value(mut value: jeff_capnp::value::Builder<'_>, ty: Type) {
        ty.build_capnp(value.reborrow().init_type());
        value.init_metadata(0);
    }

    fn set_indices(mut builder: capnp::primitive_list::Builder<'_, u32>, values: &[ValueId]) {
        for (idx, value) in values.iter().copied().enumerate() {
            builder.set(idx as u32, value);
        }
    }

    fn assert_has(errors: &[VerificationError], pred: impl Fn(&VerificationError) -> bool) {
        assert!(
            errors.iter().any(pred),
            "expected error not found in: {errors:#?}"
        );
    }
}
