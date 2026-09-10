module {
  func.func @main() -> !cbit.reg<3> attributes {mqt.entry_point} {
    %cst = arith.constant 5.000000e-01 : f64
    %cst_0 = arith.constant 1.5707963267948966 : f64
    %c2 = arith.constant 2 : index
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %c3 = arith.constant 3 : index
    %alloc = memref.alloc() {mqt.register_name = "query"} : memref<3x!qc.qubit>
    %0 = cbit.alloc(#cbit.init<zero>) {mqt.register_name = "result"} : !cbit.reg<3>
    scf.for %arg0 = %c0 to %c3 step %c1 {
      %1 = arith.subi %c2, %arg0 : index
      %2 = memref.load %alloc[%1] : memref<3x!qc.qubit>
      qc.h %2 : !qc.qubit
      %3 = arith.subi %c1, %arg0 : index
      %4 = scf.for %arg1 = %c0 to %1 step %c1 iter_args(%arg2 = %cst_0) -> (f64) {
        %5 = arith.subi %3, %arg1 : index
        %6 = memref.load %alloc[%5] : memref<3x!qc.qubit>
        %7 = memref.load %alloc[%1] : memref<3x!qc.qubit>
        qc.ctrl(%6) targets (%arg3 = %7) {
          qc.p(%arg2) %arg3 : !qc.qubit
          qc.yield
        } : {!qc.qubit}, {!qc.qubit}
        %8 = arith.mulf %arg2, %cst : f64
        scf.yield %8 : f64
      }
    }
    scf.for %arg0 = %c0 to %c3 step %c1 {
      %1 = arith.subi %c2, %arg0 : index
      %2 = memref.load %alloc[%arg0] : memref<3x!qc.qubit>
      %3 = qc.measure %2 : !qc.qubit -> i1
      cbit.store %3, %0[%1] : !cbit.reg<3>
    }
    memref.dealloc %alloc : memref<3x!qc.qubit>
    return %0 : !cbit.reg<3>
  }
}
