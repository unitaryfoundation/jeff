// GHZ State Preparation (linear) -- QC dialect.
//
// Hand-written counterpart of ghz-linear.qasm. The register width comes from
// the `%n` parameter of `main`, so the program stays arbitrary-size.

module {
  func.func @main(%n: i32) -> memref<?xi1> attributes {passthrough = ["entry_point"]} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %size = arith.index_cast %n : i32 to index

    %q = memref.alloc(%size) : memref<?x!qc.qubit>
    %c = memref.alloc(%size) : memref<?xi1>

    scf.for %i = %c0 to %size step %c1 {
      %qi = memref.load %q[%i] : memref<?x!qc.qubit>
      qc.reset %qi : !qc.qubit
    }

    %q0 = memref.load %q[%c0] : memref<?x!qc.qubit>
    qc.h %q0 : !qc.qubit

    scf.for %i = %c1 to %size step %c1 {
      %prev = arith.subi %i, %c1 : index
      %ctrl = memref.load %q[%prev] : memref<?x!qc.qubit>
      %target = memref.load %q[%i] : memref<?x!qc.qubit>
      qc.ctrl(%ctrl) targets (%arg0 = %target) {
        qc.x %arg0 : !qc.qubit
        qc.yield
      } : {!qc.qubit}, {!qc.qubit}
    }

    scf.for %i = %c0 to %size step %c1 {
      %qi = memref.load %q[%i] : memref<?x!qc.qubit>
      %m = qc.measure %qi : !qc.qubit -> i1
      memref.store %m, %c[%i] : memref<?xi1>
    }

    memref.dealloc %q : memref<?x!qc.qubit>
    return %c : memref<?xi1>
  }
}
