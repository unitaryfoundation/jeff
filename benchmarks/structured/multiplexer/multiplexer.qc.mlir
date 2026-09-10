module {
  func.func @main() -> !cbit.reg<3> attributes {mqt.entry_point} {
    %cst = arith.constant 5.000000e-01 : f64
    %cst_0 = arith.constant 1.5707963267948966 : f64
    %c2 = arith.constant 2 : index
    %c1 = arith.constant 1 : index
    %c0 = arith.constant 0 : index
    %alloc = memref.alloc() {mqt.register_name = "controls"} : memref<2x!qc.qubit>
    %0 = qc.alloc : !qc.qubit
    %1 = cbit.alloc(#cbit.init<zero>) {mqt.register_name = "result"} : !cbit.reg<3>
    scf.for %arg0 = %c0 to %c2 step %c1 {
      %4 = memref.load %alloc[%arg0] : memref<2x!qc.qubit>
      qc.h %4 : !qc.qubit
    }
    %2 = scf.for %arg0 = %c0 to %c2 step %c1 iter_args(%arg1 = %cst_0) -> (f64) {
      %4 = arith.subi %c1, %arg0 : index
      %5 = memref.load %alloc[%4] : memref<2x!qc.qubit>
      qc.ctrl(%5) targets (%arg2 = %0) {
        qc.ry(%arg1) %arg2 : !qc.qubit
        qc.yield
      } : {!qc.qubit}, {!qc.qubit}
      %6 = arith.mulf %arg1, %cst : f64
      scf.yield %6 : f64
    }
    %3 = qc.measure %0 : !qc.qubit -> i1
    cbit.store %3, %1[%c0] : !cbit.reg<3>
    scf.for %arg0 = %c0 to %c2 step %c1 {
      %4 = arith.addi %arg0, %c1 : index
      %5 = memref.load %alloc[%arg0] : memref<2x!qc.qubit>
      %6 = qc.measure %5 : !qc.qubit -> i1
      cbit.store %6, %1[%4] : !cbit.reg<3>
    }
    qc.dealloc %0 : !qc.qubit
    memref.dealloc %alloc : memref<2x!qc.qubit>
    return %1 : !cbit.reg<3>
  }
}
