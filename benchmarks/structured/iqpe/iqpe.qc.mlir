module {
  func.func @main() -> !cbit.reg<3> attributes {mqt.entry_point} {
    %cst = arith.constant 5.000000e-01 : f64
    %cst_0 = arith.constant -1.5707963267948966 : f64
    %cst_1 = arith.constant dense<[1.1780972450961724, 2.3561944901923448, 4.7123889803846897]> : tensor<3xf64>
    %c2 = arith.constant 2 : index
    %c1 = arith.constant 1 : index
    %c3 = arith.constant 3 : index
    %c0 = arith.constant 0 : index
    %0 = qc.alloc : !qc.qubit
    %1 = qc.alloc : !qc.qubit
    %2 = cbit.alloc(#cbit.init<zero>) {mqt.register_name = "result"} : !cbit.reg<3>
    qc.x %1 : !qc.qubit
    scf.for %arg0 = %c0 to %c3 step %c1 {
      %3 = arith.subi %c2, %arg0 : index
      %extracted = tensor.extract %cst_1[%3] : tensor<3xf64>
      qc.h %0 : !qc.qubit
      qc.ctrl(%0) targets (%arg1 = %1) {
        qc.p(%extracted) %arg1 : !qc.qubit
        qc.yield
      } : {!qc.qubit}, {!qc.qubit}
      %4 = arith.subi %arg0, %c1 : index
      %5 = scf.for %arg1 = %c0 to %arg0 step %c1 iter_args(%arg2 = %cst_0) -> (f64) {
        %7 = arith.subi %4, %arg1 : index
        %8 = cbit.load %2[%7] : !cbit.reg<3>
        scf.if %8 {
          qc.p(%arg2) %0 : !qc.qubit
        }
        %9 = arith.mulf %arg2, %cst : f64
        scf.yield %9 : f64
      }
      qc.h %0 : !qc.qubit
      %6 = qc.measure %0 : !qc.qubit -> i1
      cbit.store %6, %2[%arg0] : !cbit.reg<3>
      qc.reset %0 : !qc.qubit
    }
    qc.dealloc %0 : !qc.qubit
    qc.dealloc %1 : !qc.qubit
    return %2 : !cbit.reg<3>
  }
}
