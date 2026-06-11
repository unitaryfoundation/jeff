use std::fmt;

/// An error detected during verification of a jeff module.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum VerificationError {
    /// The module version is unset (0.0.0).
    MissingVersion,

    /// The module version is set but does not match the version supported by this verifier.
    IncompatibleVersion,

    /// The module's entrypoint does not refer to a function definition.
    InvalidEntrypoint,

    /// An operation references a value index that is out of bounds in the function's value table.
    ValueOutOfBounds {
        /// The out-of-bounds value index.
        value_id: u32,
        /// The number of values in the table.
        value_count: usize,
    },

    /// An operation consumes a value before any operation that produces it.
    UsedBeforeDefined {
        /// The value used out of order.
        value_id: u32,
    },

    /// A value is produced by more than one operation.
    /// In jeff's SSA value semantics, every value must have exactly one producer.
    ValueProducedMultipleTimes {
        /// The value produced multiple times.
        value_id: u32,
        /// The number of producing operations.
        producers: u32,
    },

    /// A linear value (qubit or qureg) is consumed by more than one operation.
    LinearValueConsumedMultipleTimes {
        /// The value consumed multiple times.
        value_id: u32,
        /// The number of consuming operations.
        consumers: u32,
    },

    /// A linear value (qubit or qureg) is produced but never consumed.
    LinearValueNeverConsumed {
        /// The value that is never consumed.
        value_id: u32,
    },

    /// The input and output types of an int or float operation are not all the same bitwidth or precision.
    TypeMismatch {
        /// The name of the operation with mismatched types.
        operation: &'static str,
    },

    /// An input value has a type that is not valid for the operation.
    InvalidInputType {
        /// The name of the operation with the invalid input.
        operation: &'static str,
    },

    /// An output value has a type that is not valid for the operation.
    InvalidOutputType {
        /// The name of the operation with the invalid output.
        operation: &'static str,
    },

    /// A gate operation has the wrong number of inputs or outputs for its declared arity.
    WrongArity {
        /// The name of the operation with the wrong arity.
        operation: &'static str,
    },

    /// An operation inside a nested region directly references a value from an outer scope
    /// without the value being explicitly passed in via the region's sources.
    IsolationViolation {
        /// The outer-scope value referenced directly.
        value_id: u32,
    },
}

impl fmt::Display for VerificationError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::MissingVersion => {
                write!(f, "module version is unset (0.0.0)")
            }
            Self::IncompatibleVersion => {
                write!(f, "module version is incompatible with the jeff program")
            }
            Self::InvalidEntrypoint => {
                write!(
                    f,
                    "module entrypoint does not refer to a function definition"
                )
            }
            Self::ValueOutOfBounds {
                value_id,
                value_count,
            } => {
                write!(
                    f,
                    "value {value_id} is out of bounds (function has {value_count} values)"
                )
            }
            Self::UsedBeforeDefined { value_id } => {
                write!(f, "value {value_id} is used before it is defined")
            }
            Self::ValueProducedMultipleTimes {
                value_id,
                producers,
            } => {
                write!(
                    f,
                    "value {value_id} is produced {producers} times (must be exactly once)"
                )
            }
            Self::LinearValueConsumedMultipleTimes {
                value_id,
                consumers,
            } => {
                write!(
                    f,
                    "linear value {value_id} is consumed {consumers} times (must be exactly once)"
                )
            }
            Self::LinearValueNeverConsumed { value_id } => {
                write!(f, "linear value {value_id} is produced but never consumed")
            }
            Self::TypeMismatch { operation } => {
                write!(
                    f,
                    "'{operation}' has inputs and outputs with mismatched types"
                )
            }
            Self::InvalidInputType { operation } => {
                write!(f, "'{operation}' has an input of an unexpected type")
            }
            Self::InvalidOutputType { operation } => {
                write!(f, "'{operation}' has an output of an unexpected type")
            }
            Self::WrongArity { operation } => {
                write!(f, "'{operation}' has the wrong number of inputs or outputs for its declared arity")
            }
            Self::IsolationViolation { value_id } => {
                write!(
                    f,
                    "value {value_id} from an outer scope is used inside a nested region without being passed in via sources"
                )
            }
        }
    }
}
