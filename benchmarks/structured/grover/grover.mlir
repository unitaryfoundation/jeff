// Grover's Search Algorithm -- QC dialect.
//
// Hand-written counterpart of grover.qasm, on 7 qubits: 6 search qubits plus a
// flag qubit. The oracle marks the all-ones state.
//
// The iteration count is ceil(pi/4 * sqrt(2^6)) = 7. grover.qasm computes it
// with `int(ceiling(...))`, which the OpenQASM frontend does not accept; the
// value is constant here because the size is.
//
// The oracle takes all 6 search qubits as controls and the flag as target. The
// diffusion takes the first 5 as controls and the last as target.

module {
  func.func @main() -> memref<6xi1> attributes {passthrough = ["entry_point"]} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %c2 = arith.constant 2 : index
    %c3 = arith.constant 3 : index
    %c4 = arith.constant 4 : index
    %c5 = arith.constant 5 : index
    %size = arith.constant 6 : index
    %iterations = arith.constant 7 : index

    %q = memref.alloc() : memref<6x!qc.qubit>
    %flag = memref.alloc() : memref<1x!qc.qubit>
    %c = memref.alloc() : memref<6xi1>

    scf.for %i = %c0 to %size step %c1 {
      %qi = memref.load %q[%i] : memref<6x!qc.qubit>
      qc.reset %qi : !qc.qubit
    }
    %f = memref.load %flag[%c0] : memref<1x!qc.qubit>
    qc.reset %f : !qc.qubit

    scf.for %i = %c0 to %size step %c1 {
      %qi = memref.load %q[%i] : memref<6x!qc.qubit>
      qc.h %qi : !qc.qubit
    }
    qc.x %f : !qc.qubit

    scf.for %it = %c0 to %iterations step %c1 {
      %o0 = memref.load %q[%c0] : memref<6x!qc.qubit>
      %o1 = memref.load %q[%c1] : memref<6x!qc.qubit>
      %o2 = memref.load %q[%c2] : memref<6x!qc.qubit>
      %o3 = memref.load %q[%c3] : memref<6x!qc.qubit>
      %o4 = memref.load %q[%c4] : memref<6x!qc.qubit>
      %o5 = memref.load %q[%c5] : memref<6x!qc.qubit>
      %of = memref.load %flag[%c0] : memref<1x!qc.qubit>
      qc.ctrl(%o0, %o1, %o2, %o3, %o4, %o5) targets (%arg0 = %of) {
        qc.z %arg0 : !qc.qubit
        qc.yield
      } : {!qc.qubit, !qc.qubit, !qc.qubit, !qc.qubit, !qc.qubit, !qc.qubit}, {!qc.qubit}

      scf.for %i = %c0 to %size step %c1 {
        %qi = memref.load %q[%i] : memref<6x!qc.qubit>
        qc.h %qi : !qc.qubit
      }
      scf.for %i = %c0 to %size step %c1 {
        %qi = memref.load %q[%i] : memref<6x!qc.qubit>
        qc.x %qi : !qc.qubit
      }

      %d0 = memref.load %q[%c0] : memref<6x!qc.qubit>
      %d1 = memref.load %q[%c1] : memref<6x!qc.qubit>
      %d2 = memref.load %q[%c2] : memref<6x!qc.qubit>
      %d3 = memref.load %q[%c3] : memref<6x!qc.qubit>
      %d4 = memref.load %q[%c4] : memref<6x!qc.qubit>
      %d5 = memref.load %q[%c5] : memref<6x!qc.qubit>
      qc.ctrl(%d0, %d1, %d2, %d3, %d4) targets (%arg0 = %d5) {
        qc.z %arg0 : !qc.qubit
        qc.yield
      } : {!qc.qubit, !qc.qubit, !qc.qubit, !qc.qubit, !qc.qubit}, {!qc.qubit}

      scf.for %i = %c0 to %size step %c1 {
        %qi = memref.load %q[%i] : memref<6x!qc.qubit>
        qc.x %qi : !qc.qubit
      }
      scf.for %i = %c0 to %size step %c1 {
        %qi = memref.load %q[%i] : memref<6x!qc.qubit>
        qc.h %qi : !qc.qubit
      }
    }

    scf.for %i = %c0 to %size step %c1 {
      %qi = memref.load %q[%i] : memref<6x!qc.qubit>
      %m = qc.measure %qi : !qc.qubit -> i1
      memref.store %m, %c[%i] : memref<6xi1>
    }

    memref.dealloc %q : memref<6x!qc.qubit>
    memref.dealloc %flag : memref<1x!qc.qubit>
    return %c : memref<6xi1>
  }
}
