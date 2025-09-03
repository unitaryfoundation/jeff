
@0xcc0f7aa735ae288c;

using ValueIndex = UInt32;
using Length = UInt32;
using Bitwidth = UInt8;
using FuncIndex = UInt16;
using StringIndex = UInt16;

enum FloatPrecision {
    float32 @0;
    float64 @1;
}

enum Pauli {
    i @0;
    x @1;
    y @2;
    z @3;
}

enum WellKnownGate {
    # For each well-known gate, the inputs and outputs provided are when
    # uncontrolled. Controlled gates will follow the same convention as custom
    # gates:
    #
    # Inputs:
    # - ...inputs: The `qubit` inputs of the well-known gate.
    # - `qubit` x controlQubits: The control qubits for the operation.
    # - ...inputs: The `float` inputs of the well-known gate.
    #
    # Outputs:
    # - ...outputs: The outputs of the well-known gate.
    # - `qubit` x controlQubits: The control qubit outputs for the operation.

    gphase @13;
    # Global phase operation on the "vacuum" state (no qubits).
    # G = | exp(iθ) |
    #
    # Inputs:
    # * Rotation in radians (`float`)
    #
    # Outputs:
    #

    i @12;
    # Identity (no-op) gate. Pi radians X rotation.
    # I = | 1  0 |
    #     | 0  1 |
    #
    # Inputs:
    # * Qubit to act on (`qubit`)
    #
    # Outputs:
    # * Qubit acted on (`qubit`)

    x @0;
    # Pauli-X (NOT) gate. Pi radians X rotation.
    # X = | 0  1 |
    #     | 1  0 |
    #
    # Inputs:
    # * Qubit to act on (`qubit`)
    #
    # Outputs:
    # * Qubit acted on (`qubit`)

    y @1;
    # Pauli-Y gate. Pi radians Y rotation.
    # Y = | 0  -i |
    #     | i   0 |
    #
    # Inputs:
    # * Qubit to act on (`qubit`)
    #
    # Outputs:
    # * Qubit acted on (`qubit`)

    z @2;
    # Pauli-Z gate. Pi radians Z rotation.
    # Z = | 1   0 |
    #     | 0  -1 |
    #
    # Inputs:
    # * Qubit to act on (`qubit`)
    #
    # Outputs:
    # * Qubit acted on (`qubit`)

    s @3;
    # Root-Z gate. Pi/2 radians Z rotation.
    # S = | 1   0 |
    #     | 0   i |
    #
    # Inputs:
    # * Qubit to act on (`qubit`)
    #
    # Outputs:
    # * Qubit acted on (`qubit`)

    t @4;
    # T gate. Pi/4 radians Z rotation.
    # T = | 1   0        |
    #     | 0   exp(iπ/4)|
    #
    # Inputs:
    # * Qubit to act on (`qubit`)
    #
    # Outputs:
    # * Qubit acted on (`qubit`)

    r1 @5;
    # Rotation about the |1> state.
    # R1(θ) = | 1   0       |
    #         | 0   exp(iθ) |
    #
    # Inputs:
    # * Qubit to act on (`qubit`)
    # * Rotation in radians (`float`)
    #
    # Outputs:
    # * Qubit acted on (`qubit`)

    rx @6;
    # Rotation about the X axis.
    # Rx(θ) = |  cos(θ/2)  -isin(θ/2) |
    #         | -isin(θ/2)  cos(θ/2)  |
    #
    # Inputs:
    # * Qubit to act on (`qubit`)
    # * Rotation in radians (`float`)
    #
    # Outputs:
    # * Qubit acted on (`qubit`)

    ry @7;
    # Rotation about the Y axis.
    # Ry(θ) = |  cos(θ/2)  -sin(θ/2) |
    #         |  sin(θ/2)   cos(θ/2) |
    #
    # Inputs:
    # * Qubit to act on (`qubit`)
    # * Rotation in radians (`float`)
    #
    # Outputs:
    # * Qubit acted on (`qubit`)

    rz @8;
    # Rotation about the Z axis.
    # Rz(θ) = | exp(-iθ/2)   0         |
    #         | 0            exp(iθ/2) |
    #
    # Inputs:
    # * Qubit to act on (`qubit`)
    # * Rotation in radians (`float`)
    #
    # Outputs:
    # * Qubit acted on (`qubit`)

    h @9;
    # Hadamard gate.
    # H = 1/√2 | 1   1 |
    #          | 1  -1 |
    #
    # Inputs:
    # * Qubit to act on (`qubit`)
    #
    # Outputs:
    # * Qubit acted on (`qubit`)

    u @10;
    # Euler gate.
    # U(θ,φ,λ) = | cos(θ/2)          -exp(iλ)sin(θ/2)    |
    #            | exp(iφ)sin(θ/2)   exp(i(λ+φ))cos(θ/2) |
    #
    # Inputs:
    # * Qubit to act on (`qubit`)
    # * Theta in radians (`float`)
    # * Phi in radians (`float`)
    # * Lambda in radians (`float`)
    #
    # Outputs:
    # * Qubit acted on (`qubit`)

    swap @11;
    # Swap gate. Swaps the state of two qubits.
    #
    # Inputs:
    # * First qubit (`qubit`)
    # * Second qubit (`qubit`)
    #
    # Outputs:
    # * First qubit after swap (`qubit`)
    # * Second qubit after swap (`qubit`)
}

struct Module {
    version @0 :UInt32;
    # The version of the format.

    tool @5 :Text;
    toolVersion @6 :Text;
    # Generating tool name and version.

    functions @1 :List(Function);
    # The functions in the module.

    strings @2 :List(Text);
    # String table.
    #
    # The strings in the table are referenced by `StringIndex`s in the module.

    metadata @3 :List(Meta);
    # Metadata attached to the module.

    entrypoint @4 :FuncIndex;
    # Index into the `functions` list of the entrypoint function.
}

struct Function {
    # A function declaration or definition.

    name @0 :StringIndex;
    # The name of the function.
    #
    # Function names must be unique within a module.

    metadata @3 :List(Meta);
    # Metadata attached to the function.

    union {
        definition :group {
            # A function definition, containing a dataflow region.

            body @1 :Region;
            # The body of a function definition.

            values @2 :List(Value);
            # The hyperedge values defined within the function.
            #
            # `ValueIndex`s in the function's body refer to the values in this list.
        }

        declaration :group {
            # A function declaration, containing only a signature.

            inputs @4 :List(Value);
            # The function input types.

            outputs @5 :List(Value);
            # The function output types.
        }
    }
}

struct Region {
    sources @0 :List(ValueIndex);
    # The source ports with the values that are to be supplied as arguments to the region.

    targets @1 :List(ValueIndex);
    # The target ports with the values that are returned from the region.

    operations @2 :List(Op);
    # The operations in the region.
    #
    # The order of operations in this list is not significant.

    metadata @3 :List(Meta);
    # Metadata attached to the region.
}

struct Op {
    # Operations.

    inputs @0 :List(ValueIndex);
    # The input ports with the values that are consumed by the operation.

    outputs @1 :List(ValueIndex);
    # The output ports with the values that are produced by the operation.

    metadata @2 :List(Meta);
    # Metadata attached to the operation.

    instruction :union {
        qubit @3 :QubitOp;
        qureg @4 :QuregOp;
        int @5 :IntOp;
        intArray @6 :IntArrayOp;
        float @7 :FloatOp;
        floatArray @8 :FloatArrayOp;
        scf @9 :ScfOp;
        func @10 :FuncOp;
    }
}

struct Value {
    type @0 :Type;
    # The type of the value.

    metadata @1 :List(Meta);
    # Metadata attached to the value.
}

struct Type {
    union {
        qubit @0 :Void;
        # Quantum bits.
        #
        # Qubits are linear types.

        qureg @1 :Void;
        # Quantum registers.
        #
        # A quantum register is an array of slots that can hold qubits.
        # Slots of a quantum register can either be empty or filled with a qubit.
        # Quantum registers are linear types.
        # The length of the register is not known at compile time.

        int @2 :Bitwidth;
        # Integers.
        #
        # The type does not distinguish between signed and unsigned integers.
        # Instead it is up to the operation to interpret the integer as signed or unsigned.
        # Signed integers are represented using two's complement.
        #
        # Integers of bitwidth 1 can be used as classical bits or boolean values.

        intArray @3 :Bitwidth;
        # Integer arrays.
        #
        # The length of the array is not known at compile time.
        #
        # Arrays of integers of bitwidth 1 can be used as classical bit arrays.

        float @4 :FloatPrecision;
        # Floating point numbers.
        #
        # The length of the array is not known at compile time.

        floatArray @5 :FloatPrecision;
        # Floating point number arrays.
        #
        # The length of the array is not known at compile time.
    }
}

struct Meta {
    # Metadata.

    name @0 :StringIndex;
    # The name of the metadata.

    value @1 :AnyPointer;
    # The value of the metadata.
    #
    # The format of this field is determined by the metadata name.
    # For example, it may be a string, binary data, list or a capnp struct.
}

struct QubitOp {
    # Operations for qubits.

    union {
        alloc @0 :Void;
        # Allocates a new qubit in the |0> state.
        #
        # Outputs:
        # - `qubit`: The newly allocated qubit.

        free @1 :Void;
        # Frees a qubit.
        #
        # This operation makes no assumptions about the state of the qubit.
        #
        # Inputs:
        # - `qubit`: The qubit to free.

        freeZero @2 :Void;
        # Frees a qubit in the |0> state.
        #
        # This operation can be used to avoid performing resets when it is known
        # that the qubit has already been reset. It is undefined behavior to free
        # a qubit that is not in the |0> state.
        #
        # Inputs:
        # - `qubit`: The qubit to free.

        measure @3 :Void;
        # Perform a destructive measurement of a qubit in the computational basis.
        #
        # Inputs:
        # - `qubit`: The qubit to measure.
        #
        # Outputs:
        # - `int(1)`: The measurement result.

        measureNd @4 :Void;
        # Perform a non-destructive measurement of a qubit in the computational basis.
        #
        # Inputs:
        # - `qubit`: The qubit to measure.
        #
        # Outputs:
        # - `qubit`: The measured qubit.
        # - `int(1)`: The measurement result.

        reset @5 :Void;
        # Resets a qubit to the |0> state.
        #
        # Inputs:
        # - `qubit`: The qubit to reset.
        #
        # Outputs:
        # - `qubit`: The reset qubit.

        gate @6 :QubitGate;
        # Apply a qubit gate.
        #
        # Inputs & Outputs vary - check `QubitGate`
    }
}

struct QubitGate {
    # Unitary operations on qubits.

    union {
        wellKnown @0 :WellKnownGate;
        # Apply a well-known quantum gate.
        #
        # The signature of the gate is determined by the enum value. Refer to the documentation for each well-known value.
        #
        # Inputs:
        # - ...inputs: The input qubits to the operation.
        # - `qubit` x controlQubits: The control qubits for the operation.
        # - ...inputs: Additional floating point arguments.
        #
        # Outputs:
        # - ...outputs: The output qubits.
        # - `qubit` x controlQubits: The control qubit outputs for the operation.

        ppr :group {
            # Apply an arbitrary Pauli-product rotation gate.
            #
            # The operation is characterized by a rotation angle θ and a Pauli tensor product P:
            #  PPR(θ) = exp(iθP),  P = P_1 ⊗ P_2 ⊗ ... ⊗ P_n
            #
            # Inputs:
            # - `qubit` x len(pauliString): The input qubits to the operation.
            # - `qubit` x controlQubits: The control qubits for the operation.
            # - `float(N)`: Rotation angle in radians.
            #
            # Outputs:
            # - `qubit` x len(pauliString): The output qubits.
            # - `qubit` x controlQubits: The control qubit outputs for the operation.
            pauliString @7 : List(Pauli);
        }

        custom :group {
            # Apply an arbitrary quantum gate.
            #
            # The signature of the gate is determined by its parameters.
            #
            # Inputs:
            # - `qubit` x numQubits: The input qubits to the operation.
            # - `qubit` x controlQubits: The control qubits for the operation.
            # - `float(N)` x numParams: Additional floating point arguments.
            #
            # Outputs:
            # - `qubit` x numQubits: The output qubits.
            # - `qubit` x controlQubits: The control qubit outputs for the operation.

            name @1 :StringIndex;
            # The name of the gate.

            numQubits @2 :UInt8;
            # The number of qubits that the gate acts on.

            numParams @3 :UInt8;
            # The number of floating point parameters that the gate takes as
            # inputs, after the qubit values.
        }
    }

    controlQubits @4 :UInt8;
    # The number of control qubits to the operation.

    adjoint @5 :Bool;
    # Whether to apply the adjoint of the named gate.

    power @6 :UInt8;
    # A number of times to apply this gate in sequence.
}

struct QuregOp {
    # Operations for quantum registers.

    union {
        alloc @0 :Void;
        # Allocates a new qubit register given a number of qubits in the |0> state.
        #
        # Inputs:
        # - `int(32)`: The number of qubits to allocate.
        #
        # Outputs:
        # - `qureg`: The newly allocated qubit register.

        free @10 :Void;
        # Frees a qubit register.
        #
        # This operation makes no assumptions about the state of the qubits.
        #
        # Inputs:
        # - `qureg`: The qubit register to free.

        freeZero @1 :Void;
        # Frees a qubit register, assuming that all qubits are in the |0> state.
        #
        # It is undefined behavior to free a qubit register containing qubits that are not in the |0> state.
        #
        # Inputs:
        # - `qureg`: The qubit register to free.

        extractIndex @2 :Void;
        # Extracts a single qubit from a qubit register.
        #
        # The slot must have been filled before and is marked as empty after the extraction.
        #
        # Inputs:
        # - `qureg`: The qubit register to extract from.
        # - `int(32)`: The index of the qubit to extract.
        #
        # Outputs:
        # - `qureg`: The modified qubit register.
        # - `qubit`: The extracted qubit.

        insertIndex @3 :Void;
        # Insert a single qubit from a qubit register.
        #
        # The slot must have been empty before and is marked as filled after the insertion.
        #
        # Inputs:
        # - `qureg`: The qubit register to insert into.
        # - `qubit`: The qubit to insert.
        # - `int(32)`: The index of the slot to insert into.
        #
        # Outputs:
        # - `qureg`: The modified qubit register.

        extractSlice @4 :Void;
        # Extract a slice of qubits from a qubit register given a range of indices.
        #
        # All slots in the range are marked as empty in the original register.
        #
        # Inputs:
        # - `qureg`: The qubit register to extract from.
        # - `int(32)`: The start index of the slice to extract.
        # - `int(32)`: The length of the slice to extract.
        #
        # Outputs:
        # - `qureg`: The modified qubit register.
        # - `qureg`: The extracted qubit register.

        insertSlice @5 :Void;
        # Insert a slice of qubits into a qubit register.
        #
        # All slots in the inserted range in the original register must have been empty.
        #
        # Inputs:
        # - `qureg`: The qubit register to insert into.
        # - `qureg`: The qubit register to insert.
        # - `int(32)`: The start index of the slice to insert into.
        #
        # Outputs:
        # - `qureg`: The modified qubit register.

        length @6 :Void;
        # Returns the length of the qubit register.
        #
        # Inputs:
        # - `qureg`: The qubit register.
        #
        # Outputs:
        # - `qureg`: The qubit register.
        # - `int(32)`: The length of the qubit register.

        split @7 :Void;
        # Splits a qubit register into two qubit registers at a given index.
        #
        # Inputs:
        # - `qureg`: The qubit register to split.
        # - `int(32)`: The index to split at.
        #
        # Outputs:
        # - `qureg`: The qubit register before the split.
        # - `qureg`: The qubit register after the split.

        join @8 :Void;
        # Joins together two qubit registers into a single qubit register.
        #
        # Inputs:
        # - `qureg`: The first qubit register.
        # - `qureg`: The second qubit register.
        #
        # Outputs:
        # - `qureg`: The joined qubit register.

        create @9 :Void;
        # Creates a qubit register from a variable number of input qubits.
        #
        # Inputs:
        # - `... qubit`: The qubits that the register should contain.
        #
        # Outputs:
        # - `qureg`: The qubit register containing the input qubits.
    }
}

struct IntOp {
    # Operations for integers.

    union {
        const1 @0 :Bool;
        # Create a constant 1 bit integer.
        #
        # Outputs:
        # - `int(1)`: The constant 1 bit integer.

        const8 @1 :UInt8;
        # Create a constant 8 bit integer.
        #
        # Outputs:
        # - `int(8)`: The constant 8 bit integer.

        const16 @2 :UInt16;
        # Create a constant 16 bit integer.
        #
        # Outputs:
        # - `int(16)`: The constant 16 bit integer.

        const32 @3 :UInt32;
        # Create a constant 32 bit integer.
        #
        # Outputs:
        # - `int(32)`: The constant 32 bit integer.

        const64 @4 :UInt64;
        # Create a constant 64 bit integer.
        #
        # Outputs:
        # - `int(64)`: The constant 64 bit integer.

        add @5 :Void;
        # Add two integers.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(N)`: Sum of the inputs.

        sub @6 :Void;
        # Subtract two integers.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(N)`: Difference of the inputs.
        mul @7 :Void;
        # Multiply two integers.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(N)`: Product of the inputs.

        divS @8 :Void;
        # Divide two signed integers.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(N)`: Quotient of the inputs.

        divU @9 :Void;
        # Divide two unsigned integers.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(N)`: Quotient of the inputs.

        pow @10 :Void;
        # Take the power of an integer
        #
        # Inputs:
        # - `int(N)`: Base integer.
        # - `int(N)`: Exponent integer.
        #
        # Outputs:
        # - `int(N)`: Base raised to exponent power.

        and @11 :Void;
        # Logical bitwise AND.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(N)`: Bitwise AND of inputs.

        or @12 :Void;
        # Logical bitwise OR.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(N)`: Bitwise OR of inputs.

        xor @13 :Void;
        # Logical bitwise XOR.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(N)`: Bitwise XOR of inputs.

        not @14 :Void;
        # Logical bitwise NOT.
        #
        # Inputs:
        # - `int(N)`: Integer operand.
        #
        # Outputs:
        # - `int(N)`: Bitwise NOT of input.

        minS @15 :Void;
        # Minimum of two signed integers.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(N)`: Minimum of inputs.

        minU @16 :Void;
        # Minimum of two unsigned integers.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(N)`: Minimum of inputs.

        maxS @17 :Void;
        # Maximum of two signed integers.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(N)`: Maximum of inputs.

        maxU @18 :Void;
        # Maximum of two unsigned integers.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(N)`: Maximum of inputs.

        eq @19 :Void;
        # Test two integers for equality.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(1)`: True if equal, false otherwise.

        ltS @20 :Void;
        # Check if one signed integer is strictly less than another.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(1)`: True if first less than second, false otherwise.

        lteS @21 :Void;
        # Check if one signed integer is less than or equal to another.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(1)`: True if first less than or equal to second, false otherwise.

        ltU @22 :Void;
        # Check if one signed integer is strictly less than another.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(1)`: True if first less than second, false otherwise.

        lteU @23 :Void;
        # Check if one unsigned integer is less than or equal to another.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(1)`: True if first less than or equal to second, false otherwise.

        abs @24 :Void;
        # Take the absolute value of a signed integer.
        #
        # Inputs:
        # - `int(N)`: Integer operand.
        #
        # Outputs:
        # - `int(N)`: Absolute value of input.

        remS @25 :Void;
        # Remainder of a division of two signed integers.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(N)`: Remainder of division.

        remU @26 :Void;
        # Remainder of a division of two unsigned integers.
        #
        # Inputs:
        # - `int(N)`: First integer operand.
        # - `int(N)`: Second integer operand.
        #
        # Outputs:
        # - `int(N)`: Remainder of division.

        shl @27 :Void;
        # Logical shift left.
        #
        # Inputs:
        # - `int(N)`: Value to shift.
        # - `int(N)`: Shift amount.
        #
        # Outputs:
        # - `int(N)`: Shifted value.

        shr @28 :Void;
        # Logical shift right.
        #
        # Inputs:
        # - `int(N)`: Value to shift.
        # - `int(N)`: Shift amount.
        #
        # Outputs:
        # - `int(N)`: Shifted value.
    }
}

struct IntArrayOp {
    # Operations for integer arrays.

    union {
        const1 @0 :List(Bool);
        # Create a constant 1 bit integer array.
        #
        # Outputs:
        # - `int_array(1)`: The constant 1 bit integer array.

        const8 @1 :List(UInt8);
        # Create a constant 8 bit integer array.
        #
        # Outputs:
        # - `int_array(8)`: The constant 8 bit integer array.

        const16 @2 :List(UInt16);
        # Create a constant 16 bit integer array.
        #
        # Outputs:
        # - `int_array(16)`: The constant 16 bit integer array.

        const32 @3 :List(UInt32);
        # Create a constant 32 bit integer array.
        #
        # Outputs:
        # - `int_array(32)`: The constant 32 bit integer array.

        const64 @4 :List(UInt64);
        # Create a constant 64 bit integer array.
        #
        # Outputs:
        # - `int_array(64)`: The constant 64 bit integer array.

        zero @5 :Bitwidth;
        # Create a zeroed integer array of a given bitwidth with dynamic length.
        #
        # Inputs:
        # - `int(32)`: The length of the integer array.
        #
        # Outputs:
        # - `int_array(N)`: The zeroed integer array.

        getIndex @6 :Void;
        # Get the value of an integer array at a given index.
        #
        # Inputs:
        # - `int_array(N)`: The integer array.
        # - `int(32)`: The index of the value to get.
        #
        # Outputs:
        # - `int(N)`: The value at the given index.

        setIndex @7 :Void;
        # Set the value of an integer array at a given index.
        #
        # Inputs:
        # - `int_array(N)`: The integer array.
        # - `int(32)`: The index of the value to set.
        # - `int(N)`: The new value to set.
        #
        # Outputs:
        # - `int_array(N)`: The modified integer array.

        length @8 :Void;
        # Get the length of an integer array.
        #
        # Inputs:
        # - `int_array(N)`: The integer array.
        #
        # Outputs:
        # - `int(32)`: The length of the integer array.

        create @9 :Void;
        # Creates an integer array from a variable number of input values.
        #
        # Inputs:
        # - `... int(N)`: The integer values that the array should contain.
        #
        # Outputs:
        # - `int_array(N)`: The integer array containing the input values.
    }
}

struct FloatOp {
    # Operations for floats.

    union {
        const32 @0 :Float32;
        # Create a constant 32 bit float.
        #
        # Outputs:
        # - `float(32)`: The constant 32 bit float.

        const64 @1 :Float64;
        # Create a constant 64 bit float.
        #
        # Outputs:
        # - `float(64)`: The constant 64 bit float.

        add @2 :Void;
        # Add two floats.
        #
        # Inputs:
        # - `float(N)`: First float operand.
        # - `float(N)`: Second float operand.
        #
        # Outputs:
        # - `float(N)`: Sum of the inputs.

        sub @3 :Void;
        # Subtract two floats.
        #
        # Inputs:
        # - `float(N)`: First float operand.
        # - `float(N)`: Second float operand.
        #
        # Outputs:
        # - `float(N)`: Difference of the inputs.

        mul @4 :Void;
        # Multiply two floats.
        #
        # Inputs:
        # - `float(N)`: First float operand.
        # - `float(N)`: Second float operand.
        #
        # Outputs:
        # - `float(N)`: Product of the inputs.

        pow @5 :Void;
        # Calculate one float raised to the power of another.
        #
        # Inputs:
        # - `float(N)`: The base.
        # - `float(N)`: The exponent.
        #
        # Outputs:
        # - `float(N)`: The base raised to the power of the exponent.

        eq @6 :Void;
        # Test two floats for equality.
        #
        # Inputs:
        # - `float(N)`: First float operand.
        # - `float(N)`: Second float operand.
        #
        # Outputs:
        # - `int(1)`: True if equal, false otherwise.

        lt @7 :Void;
        # Check if one float is strictly less than another.
        #
        # Inputs:
        # - `float(N)`: First float operand.
        # - `float(N)`: Second float operand.
        #
        # Outputs:
        # - `int(1)`: True if first is less than second, false otherwise.

        lte @8 :Void;
        # Check if one float is less than or equal to another.
        #
        # Inputs:
        # - `float(N)`: First float operand.
        # - `float(N)`: Second float operand.
        #
        # Outputs:
        # - `int(1)`: True if first is less than or equal to second, false otherwise.

        sqrt @9 :Void;
        # Calculate the square root of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `float(N)`: The square root of the input.

        abs @10 :Void;
        # Calculate the absolute value of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `float(N)`: The absolute value of the input.

        ceil @11 :Void;
        # Round a float up to the nearest integer.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `float(N)`: The ceiling of the input.

        floor @12 :Void;
        # Round a float down to the nearest integer.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `float(N)`: The floor of the input.

        isNan @13 :Void;
        # Check if a float is NaN.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `int(1)`: True if NaN, false otherwise.

        isInf @14 :Void;
        # Check if a float is infinite.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `int(1)`: True if infinite, false otherwise.

        exp @15 :Void;
        # Calculate e raised to the power of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `float(N)`: e raised to the input power.

        log @16 :Void;
        # Calculate the natural logarithm of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `float(N)`: The natural logarithm of the input.

        sin @17 :Void;
        # Calculate the sine of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand in radians.
        #
        # Outputs:
        # - `float(N)`: The sine of the input.

        cos @18 :Void;
        # Calculate the cosine of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand in radians.
        #
        # Outputs:
        # - `float(N)`: The cosine of the input.

        tan @19 :Void;
        # Calculate the tangent of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand in radians.
        #
        # Outputs:
        # - `float(N)`: The tangent of the input.

        asin @20 :Void;
        # Calculate the arcsine of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `float(N)`: The arcsine of the input in radians.

        acos @21 :Void;
        # Calculate the arccosine of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `float(N)`: The arccosine of the input in radians.

        atan @22 :Void;
        # Calculate the arctangent of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `float(N)`: The arctangent of the input in radians.

        atan2 @23 :Void;
        # Calculate the 2-argument arctangent.
        #
        # Inputs:
        # - `float(N)`: y coordinate
        # - `float(N)`: x coordinate
        #
        # Outputs:
        # - `float(N)`: The arctangent of y/x in radians.

        sinh @24 :Void;
        # Calculate the hyperbolic sine of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `float(N)`: The hyperbolic sine of the input.

        cosh @25 :Void;
        # Calculate the hyperbolic cosine of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `float(N)`: The hyperbolic cosine of the input.

        tanh @26 :Void;
        # Calculate the hyperbolic tangent of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `float(N)`: The hyperbolic tangent of the input.

        asinh @27 :Void;
        # Calculate the inverse hyperbolic sine of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `float(N)`: The inverse hyperbolic sine of the input.

        acosh @28 :Void;
        # Calculate the inverse hyperbolic cosine of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `float(N)`: The inverse hyperbolic cosine of the input.

        atanh @29 :Void;
        # Calculate the inverse hyperbolic tangent of a float.
        #
        # Inputs:
        # - `float(N)`: The float operand.
        #
        # Outputs:
        # - `float(N)`: The inverse hyperbolic tangent of the input.

        max @30 :Void;
        # Maximum of two floats.
        #
        # Inputs:
        # - `float(N)`: First float operand.
        # - `float(N)`: Second float operand.
        #
        # Outputs:
        # - `float(N)`: Maximum of the inputs.

        min @31 :Void;
        # Minimum of two floats.
        #
        # Inputs:
        # - `float(N)`: First float operand.
        # - `float(N)`: Second float operand.
        #
        # Outputs:
        # - `float(N)`: Minimum of the inputs.
    }
}

struct FloatArrayOp {
    # Operations for float arrays.

    union {
        const32 @0 :List(Float32);
        # Create a constant 32 bit float array.
        #
        # Outputs:
        # - `float_array(32)`: The constant 32 bit float array.

        const64 @1 :List(Float64);
        # Create a constant 64 bit float array.
        #
        # Outputs:
        # - `float_array(64)`: The constant 64 bit float array.

        zero @2 :FloatPrecision;
        # Create a zeroed float array of a given precision with dynamic length.
        #
        # Inputs:
        # - `int(32)`: The length of the float array.
        #
        # Outputs:
        # - `float_array(N)`: The zeroed float array.

        getIndex @3 :Void;
        # Get the value of a float array at a given index.
        #
        # Inputs:
        # - `float_array(N)`: The float array.
        # - `int(32)`: The index of the value to get.
        #
        # Outputs:
        # - `float(N)`: The value at the given index.

        setIndex @4 :Void;
        # Set the value of a float array at a given index.
        #
        # Inputs:
        # - `float_array(N)`: The float array.
        # - `int(32)`: The index to set.
        # - `float(N)`: The value to set.
        #
        # Outputs:
        # - `float_array(N)`: The modified float array.

        length @5 :Void;
        # Get the length of a float array.
        #
        # Inputs:
        # - `float_array(N)`: The float array.
        #
        # Outputs:
        # - `int(32)`: The length of the float array.

        create @6 :Void;
        # Creates a float array from a variable number of input values.
        #
        # Inputs:
        # - `... float(N)`: The float values that the array should contain.
        #
        # Outputs:
        # - `float_array(N)`: The float array containing the input values.
    }
}

struct ScfOp {
    # Operations for structured control flow.

    union {
        switch :group {
            # Switch statement.
            #
            # The first input to the switch is an integer that selects the branch by index.
            # The operation has a region for every branch, together with an optional default region.
            # If there is no default region, it is an error if the index does not match any branch.
            #
            # Inputs:
            # - `int(N)`: The value to switch on.
            # - `... inputs`: Any number of input values that are passed to the chosen branch.
            #
            # Outputs:
            # - `... outputs`: Any number of output values that are returned from the chosen branch.
            #
            # Each region must have the signature `(...inputs) -> (... outputs)`.

            branches @0 :List(Region);
            # The branches of the switch.

            default @1 :Region;
            # The optional default branch of the switch.
        }

        for @2 :Region;
        # For loop.
        #
        # The loop iterates from start to stop (exclusive) by step.
        # The region is the loop body that is executed once for each iteration.
        # The loop maintains a state consisting of any number of values.
        # Each iteration receives the state from the previous iteration,
        # or the initial state for the first iteration.
        # When the loop finishes, the final state is returned.
        # Iterations also have access to the current iteration value.
        #
        # Inputs:
        # - `int(N)`: The (signed) start value.
        # - `int(N)`: The (signed) stop value (exclusive).
        # - `int(N)`: The (signed) step value.
        # - `... state`: Any number of values that are passed to the loop body.
        #
        # Outputs:
        # - `... state`: Any number of values that are returned from the loop body.
        #
        # The region must have the signature `(int(N), ... state) -> (... state)`.
        # The first parameter is the current iteration value.
        # It is undefined behavior if step is zero.

        while :group {
            # While loop.
            #
            # The condition is checked before each iteration.
            # If the condition is true, the loop body is executed.
            # The loop maintains a state consisting of any number of values.
            # Each iteration receives the state from the previous iteration,
            # or the initial state for the first iteration.
            # When the loop finishes, the final state is returned.
            #
            # Inputs:
            # - `... state`: Any number of values that are passed to the condition and body.
            #
            # Outputs:
            # - `... state`: Any number of values that are returned from the body.

            condition @3 :Region;
            # The condition region that determines whether to continue looping.
            #
            # The region must have the signature `(... state) -> (int(1))`.
            # The output is the condition result - true to continue, false to stop.
            # The condition can only evaluate the state, not modify it.

            body @4 :Region;
            # The body region that is executed on each iteration.
            #
            # The region must have the signature `(... state) -> (... state)`.
            # The outputs are passed as inputs to the condition region for the next iteration.
        }

        doWhile :group {
            # Do-while loop.
            #
            # The loop body is executed once, then the condition is checked.
            # If the condition is true, the loop body is executed again.
            # The loop maintains a state consisting of any number of values.
            # Each iteration receives the state from the previous iteration,
            # or the initial state for the first iteration.
            # When the loop finishes, the final state is returned.
            #
            # Inputs:
            # - `... state`: Any number of values that are passed to the condition and body.
            #
            # Outputs:
            # - `... state`: Any number of values that are returned from the body.

            body @5 :Region;
            # The body region that is executed on each iteration.
            #
            # The region must have the signature `(... state) -> (... state)`.
            # The outputs are passed as inputs to the condition region for the current iteration.

            condition @6 :Region;
            # The condition region that determines whether to continue looping.
            #
            # The region must have the signature `(... state) -> (int(1))`.
            # The output is the condition result - true to continue, false to stop.
            # The condition can only evaluate the state, not modify it.
        }
    }
}

struct FuncOp {
    funcCall @0 :FuncIndex;
    # Call a function.
}
