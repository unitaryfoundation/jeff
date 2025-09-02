# Jeff Specification

This document describes the Jeff quantum program format—a binary exchange format for
quantum programs designed for efficiency and compiler interoperability. The format is
defined using [Cap'n Proto](capnproto.org), the schema for which can be found in
[jeff.capnp](../impl/capnp/jeff.capnp) - this document is best read alongside the schema.

Jeff aims to balance expressiveness and simplicity, enabling representation of a wide range of structured and dynamic quantum algorithms, while remaining easy for non-expert users to parse and manipulate.

Programs in Jeff are collections of functions, each containing a dataflow graph of operations. The format supports both quantum and classical data types, as well as structured control flow constructs. Jeff uses *value semantics*: values are immutable, and operations produce new values rather than modifying existing ones. This approach simplifies analysis and optimization. Individual regions can be viewed as directed acyclic graphs (DAGs) of operations, where edges represent typed data dependencies. Cycles in the dataflow graph are invalid.

## Module

The root of any Jeff program is the `Module` struct, which encapsulates the entire quantum program, including all functions, metadata, and configuration. Its fields are:

- `version`: Integer specifying the Jeff format version.
- `tool` / `toolVersion`: Text fields identifying the software and its version that generated the file.
- `functions`: List of all functions defined or declared in the module.
- `strings`: List of strings. To save space and improve lookup efficiency, strings (such as function names or metadata keys) are stored once and referenced by index (`StringIndex`).
- `metadata`: List of `Meta` objects for attaching arbitrary, extensible information to the module. Metadata is always optional and ignored by tools that do not recognize it.
- `entrypoint`: Index (`FuncIndex`) pointing to the function in `functions` that serves as the program's main entry point (analogous to `main` in C/C++).

## Functions

Functions are the primary building blocks of a Jeff program. A `Function` can be either a full `definition` with a body, or a `declaration` with only a type signature. Declarations are useful for describing functions defined elsewhere, such as in external libraries or runtime environments.

The `Function` struct includes:

- `definition`: Contains the implementation of the function.
    - `body`: A `Region` holding the function's operations. The region's inputs and outputs implicitly define the function's type signature. Jeff functions can have multiple outputs, and the function signature is determined by the region's sources and targets.
    - `values`: List of all data values (wires) used within the function's dataflow graph. Operations reference these values by their index (`ValueIndex`).
- **`declaration`**: Represents a function signature for functions defined externally. Specifies the `inputs` and `outputs` types.

## Dataflow Graph: `Region`, `Op`, `Value`

Jeff represents program logic as a dataflow graph within a `Region`. 

- `Region`: Container for a set of operations. Defines its inputs (`sources`) and outputs (`targets`) by referencing values from the parent function's `values` list. The `operations` list contains all operations in the region. Execution order is determined by data dependencies, not list order; only a partial order is defined. Cycles in the dataflow graph are invalid. Lower-level tools may choose a specific execution order as long as dependencies are respected. Regions used in control flow operations (such as `switch`, `for`, `while`, `doWhile`) are themselves dataflow graphs, and their inputs/outputs are wired according to the control flow operation's semantics.
- `Op`: A single operation in the dataflow graph. Consumes `inputs` and produces `outputs`, which are indices into the function's `values` list. The specific action is defined by the `instruction` field.
- `Value`: Represents a "wire" or "edge" in the dataflow graph, carrying data of a specific `Type`.

## Metadata

Jeff provides a flexible mechanism for attaching arbitrary metadata to various parts of the program structure. This is useful for tool-specific information, debugging, or any extended attributes not part of the core specification.

The `Meta` struct represents a key-value pair:

- `name`: String (via `StringIndex`) acting as the metadata key.
- `value`: An `AnyPointer` holding arbitrary Cap'n Proto data. The interpretation is determined by the `name`, allowing structured or unstructured data (e.g., strings, numbers, or nested objects).

Metadata can be attached as a list of `Meta` objects to:

- `Module`
- `Function`
- `Region`
- `Op`
- `Value`

This extensibility allows tools to communicate extra information without changing the core Jeff specification. Metadata is always optional, and tools that do not understand a particular metadata entry can ignore it and pass it through unmodified.

## Types

The `Type` struct defines the kind of data a `Value` can hold. Jeff includes simple classical types alongside quantum types, enabling representation of quantum-classical hybrid algorithms.

- `qubit`: A single quantum bit. Must be treated "linearly": it cannot be copied or deleted (satisfying the no-cloning and no-deleting theorems of quantum mechanics). Structurally, a `qubit` value must be used exactly once as an input after being produced as an output.
- `qureg`: A quantum register—a dynamically sized array of qubits. Also treated linearly: the entire register must be used exactly once. The length of a quantum register is not known at compile time, but can be queried at runtime.
- `int`: Classical integer with a specified `Bitwidth` (e.g., 8, 16, 32, 64). The
  integer is signed or unsigned based on the operation being performed. The size is a
  type-level parameter to allow for efficient storage and operations. Width-1 integers
  can be used to represent boolean values or bits (e.g. qubit measurement results).
- `intArray`: Dynamically sized array of integers of a common bitwidth.
- `float`: Classical IEEE754 floating-point number with a specified `FloatPrecision`
  (`float32` or `float64`). They are used for real-valued parameters, such as rotation angles in quantum gates.
- `floatArray`: Dynamically sized array of floating-point numbers.

## Operations

The `Op` struct's `instruction` field is a union holding one of several operation types, categorized by the data they act upon.


### QubitOp
Operations on individual qubits.
- Lifecycle: `alloc`, `free`, `reset`.
- Measurement: `measure` (destructive), `measureNd` (non-destructive).
- Gates: The `gate` operation applies a `QubitGate`:
    - `wellKnown`: Standard gate from the `WellKnownGate` enum.
    - `ppr`: Arbitrary Pauli-product rotation defined by a list of `Pauli` components, a rotation angle (in radians), and target qubits.
    - `custom`: User-defined gate specified by name and number of qubits/parameters. This is the key extension point of Jeff, allowing users to define and use gates beyond the standard set. As long as two tools agree on the semantics of a custom gate, they can interoperate via Jeff.
    - All gates can be modified with `controlQubits`, `adjoint`, and `power` to create controlled, adjoint (inverse), and repeated applications, respectively.

### QuregOp
Operations on quantum registers.
- Lifecycle: `alloc` (takes number of qubits to allocate as input), `free`, and `create` (creates a register from input qubits).
- Manipulation: `extractIndex`, `insertIndex`, `extractSlice`, `insertSlice`, `split`, `join`.
- Introspection: `length`.

### Pauli

The `Pauli` enum defines components of Pauli-product rotation gates (`ppr`):

- `i`: Identity
- `x`: Pauli-X
- `y`: Pauli-Y
- `z`: Pauli-Z

### WellKnownGate

The `WellKnownGate` enum provides a set of standard, commonly used quantum gates. This allows for compact, standardized representation. Inputs and outputs for controlled gates follow a standard convention: control qubits are provided as inputs after the target qubits and are returned as outputs after the target qubit outputs.

Gate parameters are provided as additional floating point inputs where applicable, representing angles in radians.

- `gphase`: Global phase gate.
    - Inputs: `float` (rotation in radians)
- `i`: Identity gate.
    - Inputs: `qubit`
    - Outputs: `qubit`
- `x`: Pauli-X gate.
    - Inputs: `qubit`
    - Outputs: `qubit`
- `y`: Pauli-Y gate.
    - Inputs: `qubit`
    - Outputs: `qubit`
- `z`: Pauli-Z gate.
    - Inputs: `qubit`
    - Outputs: `qubit`
- `s`: S gate (√Z).
    - Inputs: `qubit`
    - Outputs: `qubit`
- `t`: T gate (√S).
    - Inputs: `qubit`
    - Outputs: `qubit`
- `r1`: Rotation about the |1⟩ state.
    - Inputs: `qubit`, `float` (rotation in radians)
    - Outputs: `qubit`
- `rx`: Rotation about the X-axis.
    - Inputs: `qubit`, `float` (rotation in radians)
    - Outputs: `qubit`
- `ry`: Rotation about the Y-axis.
    - Inputs: `qubit`, `float` (rotation in radians)
    - Outputs: `qubit`
- `rz`: Rotation about the Z-axis.
    - Inputs: `qubit`, `float` (rotation in radians)
    - Outputs: `qubit`
- `h`: Hadamard gate.
    - Inputs: `qubit`
    - Outputs: `qubit`
- `u`: Euler gate (U3).
    - Inputs: `qubit`, `float` (theta), `float` (phi), `float` (lambda)
    - Outputs: `qubit`
- `swap`: Swap gate.
    - Inputs: `qubit`, `qubit`
    - Outputs: `qubit`, `qubit`

### Classical Operations (`IntOp`, `FloatOp`, etc.)

#### IntOp / IntArrayOp
Comprehensive set of operations for classical integers and integer arrays, including:
- Constants: `const1`, `const8`, `const16`, `const32`, `const64`.
- Arithmetic: `add`, `sub`, `mul`, `divS`, `divU`, `remS`, `remU`, `pow`, `abs`.
- Bitwise logic: `and`, `or`, `xor`, `not`, `shl`, `shr`.
- Comparisons: `eq`, `ltS`, `lteS`, `ltU`, `lteU`, `minS`, `minU`, `maxS`, `maxU`.
- Array manipulation: `const1`, `const8`, `const16`, `const32`, `const64`, `zero`, `getIndex`, `setIndex`, `length`, `create`.

#### FloatOp / FloatArrayOp

Comprehensive set of operations for floating-point numbers and arrays, including:

- Constants: `const32`, `const64`.
- Arithmetic: `add`, `sub`, `mul`, `pow`.
- Mathematical functions: `sqrt`, `abs`, `ceil`, `floor`, `isNan`, `isInf`, `exp`, `log`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`, `sinh`, `cosh`, `tanh`, `asinh`, `acosh`, `atanh`.
- Comparisons: `eq`, `lt`, `lte`, `max`, `min`.
- Array manipulation: `const32`, `const64`, `zero`, `getIndex`, `setIndex`, `length`, `create`.

### Structured Control Flow (`ScfOp`)

Structured control flow is a key feature of Jeff, allowing compact representation of complex algorithms. To represent control flow (branching, looping, etc.), Jeff uses a *structured* approach, similar to constructs in high-level programming languages, rather than a control-flow graph (CFG) approach (like LLVM or QIR). This choice simplifies analysis and optimization.

Jeff takes inspiration from the MLIR SCF dialect, adapting it to fit the format's needs. Structured control flow operations include:

- `switch`: Conditional branching based on an integer value. Consists of multiple `branches` (regions) and an optional `default` region. Each branch is a region (dataflow graph) whose inputs and outputs are determined by the control flow operation.
- `for`: Classic for-loop that iterates from a start to a stop value with a given step. Passes a loop state through its body `Region` (dataflow graph) on each iteration.
- `while` / `doWhile`: Looping constructs that execute a `body` region (dataflow graph) as long as a `condition` region evaluates to true.

### Function Calls (`FuncOp`)

- `funcCall`: Operation to call another function within the same module, identified by its `FuncIndex`. The inputs and outputs of the `funcCall` operation must match the signature of the called function.
