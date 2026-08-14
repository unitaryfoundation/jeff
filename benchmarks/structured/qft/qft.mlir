// Quantum Fourier Transform -- QC dialect.
//
// Hand-written counterpart of qft.qasm. The register width comes from the `%n`
// parameter of `main`, so the program stays arbitrary-size.
//
// The controlled-phase angle pi/2^(j-i) is carried by the inner loop and halved
// each step. The QCO-to-`jeff` conversion has no integer-to-float cast and no
// float division, so an angle that depends on a loop index has to be built by
// accumulation rather than computed from the index.
//
// The bit-reversal swap count here is floor(n/2). qft.qasm writes
// `int(ceiling((n-1)/2))`, but `(n-1)/2` is integer division in OpenQASM 3, so
// the `ceiling` never rounds anything up and the source loses a swap for even
// `n`. This file implements the intended bit reversal.

module {
  func.func @main(%n: i32) -> memref<?xi1> attributes {passthrough = ["entry_point"]} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %c2 = arith.constant 2 : index
    %half_pi = arith.constant 1.5707963267948966 : f64
    %half = arith.constant 5.000000e-01 : f64

    %size = arith.index_cast %n : i32 to index
    %q = memref.alloc(%size) : memref<?x!qc.qubit>
    %c = memref.alloc(%size) : memref<?xi1>

    scf.for %i = %c0 to %size step %c1 {
      %qi = memref.load %q[%i] : memref<?x!qc.qubit>
      qc.reset %qi : !qc.qubit
    }

    scf.for %i = %c0 to %size step %c1 {
      %qi = memref.load %q[%i] : memref<?x!qc.qubit>
      qc.h %qi : !qc.qubit

      %first = arith.addi %i, %c1 : index
      %angle_end = scf.for %j = %first to %size step %c1
          iter_args(%angle = %half_pi) -> (f64) {
        %ctrl = memref.load %q[%j] : memref<?x!qc.qubit>
        %target = memref.load %q[%i] : memref<?x!qc.qubit>
        qc.ctrl(%ctrl) targets (%arg0 = %target) {
          qc.p(%angle) %arg0 : !qc.qubit
          qc.yield
        } : {!qc.qubit}, {!qc.qubit}
        %angle_next = arith.mulf %angle, %half : f64
        scf.yield %angle_next : f64
      }
    }

    %last = arith.subi %size, %c1 : index
    %swaps = arith.divui %size, %c2 : index
    scf.for %i = %c0 to %swaps step %c1 {
      %mirror = arith.subi %last, %i : index
      %a = memref.load %q[%i] : memref<?x!qc.qubit>
      %b = memref.load %q[%mirror] : memref<?x!qc.qubit>
      qc.swap %a, %b : !qc.qubit, !qc.qubit
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
