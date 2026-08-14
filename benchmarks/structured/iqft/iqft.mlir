// Iterative Quantum Fourier Transform -- QC dialect.
//
// Hand-written counterpart of iqft.qasm. The result-register width comes from
// the `%n` parameter of `main`, so the program stays arbitrary-size. A single
// qubit is measured and reset once per iteration.
//
// The phase angle pi/2^(i-j) is built by accumulation: the outer loop carries
// pi/2^i, halving it each iteration, and the inner loop doubles from there.
// The QCO-to-`jeff` conversion has no integer-to-float cast and no float
// division, so an angle that depends on a loop index has to be built this way.

module {
  func.func @main(%n: i32) -> memref<?xi1> attributes {passthrough = ["entry_point"]} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %pi = arith.constant 3.1415926535897931 : f64
    %two = arith.constant 2.000000e+00 : f64
    %half = arith.constant 5.000000e-01 : f64

    %size = arith.index_cast %n : i32 to index
    %qreg = memref.alloc() : memref<1x!qc.qubit>
    %res = memref.alloc(%size) : memref<?xi1>

    %q = memref.load %qreg[%c0] : memref<1x!qc.qubit>
    qc.reset %q : !qc.qubit

    %last = arith.subi %size, %c1 : index

    %base_end = scf.for %i = %c0 to %size step %c1
        iter_args(%base = %pi) -> (f64) {
      %angle_end = scf.for %j = %c0 to %i step %c1
          iter_args(%angle = %base) -> (f64) {
        %slot = arith.subi %last, %j : index
        %bit = memref.load %res[%slot] : memref<?xi1>
        scf.if %bit {
          %qb = memref.load %qreg[%c0] : memref<1x!qc.qubit>
          qc.p(%angle) %qb : !qc.qubit
        }
        %angle_next = arith.mulf %angle, %two : f64
        scf.yield %angle_next : f64
      }

      %qi = memref.load %qreg[%c0] : memref<1x!qc.qubit>
      qc.h %qi : !qc.qubit
      %target = arith.subi %last, %i : index
      %m = qc.measure %qi : !qc.qubit -> i1
      memref.store %m, %res[%target] : memref<?xi1>
      qc.reset %qi : !qc.qubit

      %base_next = arith.mulf %base, %half : f64
      scf.yield %base_next : f64
    }

    memref.dealloc %qreg : memref<1x!qc.qubit>
    return %res : memref<?xi1>
  }
}
