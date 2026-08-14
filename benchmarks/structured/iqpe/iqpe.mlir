// Iterative Quantum Phase Estimation -- QC dialect.
//
// Hand-written counterpart of iqpe.qasm. The result-register width comes from
// the `%precision` parameter of `main`, so the program stays arbitrary-size.
// One qubit is measured and reset once per iteration; the ancilla holds the
// eigenstate throughout. `%precision` must be at least 1.
//
// `ctrl @ pow(2**i) @ p(3*pi/8)` is applied here as a single controlled phase
// of 2^i * 3*pi/8. Repeating a phase gate 2^i times multiplies its angle by
// 2^i, so this is the same operation without needing a repeat modifier.
//
// The source loop runs i from precision-1 down to 0. `scf.for` counts up, so
// this file iterates k upward and uses i = precision-1-k. The controlled-phase
// angle starts at 2^(precision-1) * 3*pi/8 and halves each iteration, which is
// the same sequence. The starting value is built by the leading loop, because
// the QCO-to-`jeff` conversion has no integer-to-float cast and no float
// division.

module {
  func.func @main(%precision: i32) -> memref<?xi1> attributes {passthrough = ["entry_point"]} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %two = arith.constant 2.000000e+00 : f64
    %half = arith.constant 5.000000e-01 : f64
    %half_pi = arith.constant 1.5707963267948966 : f64
    %phase = arith.constant 1.1780972450961724 : f64

    %size = arith.index_cast %precision : i32 to index
    %last = arith.subi %size, %c1 : index

    %qreg = memref.alloc() : memref<1x!qc.qubit>
    %anc = memref.alloc() : memref<1x!qc.qubit>
    %res = memref.alloc(%size) : memref<?xi1>

    %q = memref.load %qreg[%c0] : memref<1x!qc.qubit>
    %a = memref.load %anc[%c0] : memref<1x!qc.qubit>
    qc.reset %q : !qc.qubit
    qc.reset %a : !qc.qubit
    qc.x %a : !qc.qubit

    %scaled = scf.for %k = %c0 to %last step %c1
        iter_args(%acc = %phase) -> (f64) {
      %doubled = arith.mulf %acc, %two : f64
      scf.yield %doubled : f64
    }

    %phase_end = scf.for %k = %c0 to %size step %c1
        iter_args(%angle = %scaled) -> (f64) {
      %i = arith.subi %last, %k : index

      %qi = memref.load %qreg[%c0] : memref<1x!qc.qubit>
      qc.h %qi : !qc.qubit

      %target = memref.load %anc[%c0] : memref<1x!qc.qubit>
      qc.ctrl(%qi) targets (%arg0 = %target) {
        qc.p(%angle) %arg0 : !qc.qubit
        qc.yield
      } : {!qc.qubit}, {!qc.qubit}

      %first = arith.addi %i, %c1 : index
      %corr_end = scf.for %j = %first to %size step %c1
          iter_args(%corr = %half_pi) -> (f64) {
        %bit = memref.load %res[%j] : memref<?xi1>
        scf.if %bit {
          %qb = memref.load %qreg[%c0] : memref<1x!qc.qubit>
          qc.p(%corr) %qb : !qc.qubit
        }
        %corr_next = arith.mulf %corr, %half : f64
        scf.yield %corr_next : f64
      }

      qc.h %qi : !qc.qubit
      %m = qc.measure %qi : !qc.qubit -> i1
      memref.store %m, %res[%i] : memref<?xi1>
      qc.reset %qi : !qc.qubit

      %angle_next = arith.mulf %angle, %half : f64
      scf.yield %angle_next : f64
    }

    memref.dealloc %qreg : memref<1x!qc.qubit>
    memref.dealloc %anc : memref<1x!qc.qubit>
    return %res : memref<?xi1>
  }
}
