// GHZ State Preparation (star) -- QC dialect.
//
// Hand-written counterpart of ghz-star.qasm, on 7 qubits.

module {
  func.func @main() -> memref<7xi1> attributes {passthrough = ["entry_point"]} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %size = arith.constant 7 : index

    %q = memref.alloc() : memref<7x!qc.qubit>
    %c = memref.alloc() : memref<7xi1>

    scf.for %i = %c0 to %size step %c1 {
      %qi = memref.load %q[%i] : memref<7x!qc.qubit>
      qc.reset %qi : !qc.qubit
    }

    %q0 = memref.load %q[%c0] : memref<7x!qc.qubit>
    qc.h %q0 : !qc.qubit

    scf.for %i = %c1 to %size step %c1 {
      %ctrl = memref.load %q[%c0] : memref<7x!qc.qubit>
      %target = memref.load %q[%i] : memref<7x!qc.qubit>
      qc.ctrl(%ctrl) targets (%arg0 = %target) {
        qc.x %arg0 : !qc.qubit
        qc.yield
      } : {!qc.qubit}, {!qc.qubit}
    }

    scf.for %i = %c0 to %size step %c1 {
      %qi = memref.load %q[%i] : memref<7x!qc.qubit>
      %m = qc.measure %qi : !qc.qubit -> i1
      memref.store %m, %c[%i] : memref<7xi1>
    }

    memref.dealloc %q : memref<7x!qc.qubit>
    return %c : memref<7xi1>
  }
}
