// Quantum Phase Estimation -- QC dialect.
//
// Hand-written counterpart of qpe.qasm, on 7 qubits: 6 counting qubits plus one
// eigenstate ancilla.
//
// `ctrl @ pow(2**i) @ p(3*pi/8)` is applied here as a single controlled phase
// of 2^i * 3*pi/8. Repeating a phase gate 2^i times multiplies its angle by
// 2^i, so this is the same operation without needing a repeat modifier.
//
// The angles are carried by their loops and scaled each step. The QCO-to-`jeff`
// conversion has no integer-to-float cast and no float division, so an angle
// that depends on a loop index has to be built by accumulation.

module {
  func.func @main() -> memref<6xi1> attributes {passthrough = ["entry_point"]} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %size = arith.constant 6 : index
    %last = arith.constant 5 : index
    %swaps = arith.constant 3 : index
    %two = arith.constant 2.000000e+00 : f64
    %half = arith.constant 5.000000e-01 : f64
    %phase = arith.constant 1.1780972450961724 : f64
    %minus_half_pi = arith.constant -1.5707963267948966 : f64

    %q = memref.alloc() : memref<6x!qc.qubit>
    %anc = memref.alloc() : memref<1x!qc.qubit>
    %c = memref.alloc() : memref<6xi1>

    scf.for %i = %c0 to %size step %c1 {
      %qi = memref.load %q[%i] : memref<6x!qc.qubit>
      qc.reset %qi : !qc.qubit
    }
    %a0 = memref.load %anc[%c0] : memref<1x!qc.qubit>
    qc.reset %a0 : !qc.qubit

    scf.for %i = %c0 to %size step %c1 {
      %qi = memref.load %q[%i] : memref<6x!qc.qubit>
      qc.h %qi : !qc.qubit
    }
    qc.x %a0 : !qc.qubit

    %phase_end = scf.for %i = %c0 to %size step %c1
        iter_args(%angle = %phase) -> (f64) {
      %ctrl = memref.load %q[%i] : memref<6x!qc.qubit>
      %target = memref.load %anc[%c0] : memref<1x!qc.qubit>
      qc.ctrl(%ctrl) targets (%arg0 = %target) {
        qc.p(%angle) %arg0 : !qc.qubit
        qc.yield
      } : {!qc.qubit}, {!qc.qubit}
      %angle_next = arith.mulf %angle, %two : f64
      scf.yield %angle_next : f64
    }

    scf.for %i = %c0 to %swaps step %c1 {
      %mirror = arith.subi %last, %i : index
      %a = memref.load %q[%i] : memref<6x!qc.qubit>
      %b = memref.load %q[%mirror] : memref<6x!qc.qubit>
      qc.swap %a, %b : !qc.qubit, !qc.qubit
    }

    scf.for %i = %c0 to %size step %c1 {
      %first = arith.addi %i, %c1 : index
      %angle_end = scf.for %j = %first to %size step %c1
          iter_args(%angle = %minus_half_pi) -> (f64) {
        %ctrl = memref.load %q[%j] : memref<6x!qc.qubit>
        %target = memref.load %q[%i] : memref<6x!qc.qubit>
        qc.ctrl(%ctrl) targets (%arg0 = %target) {
          qc.p(%angle) %arg0 : !qc.qubit
          qc.yield
        } : {!qc.qubit}, {!qc.qubit}
        %angle_next = arith.mulf %angle, %half : f64
        scf.yield %angle_next : f64
      }
      %qi = memref.load %q[%i] : memref<6x!qc.qubit>
      qc.h %qi : !qc.qubit
    }

    scf.for %i = %c0 to %size step %c1 {
      %qi = memref.load %q[%i] : memref<6x!qc.qubit>
      %m = qc.measure %qi : !qc.qubit -> i1
      memref.store %m, %c[%i] : memref<6xi1>
    }

    memref.dealloc %q : memref<6x!qc.qubit>
    memref.dealloc %anc : memref<1x!qc.qubit>
    return %c : memref<6xi1>
  }
}
