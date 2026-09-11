module {
  func.func @main() -> !cbit.reg<3> attributes {mqt.entry_point} {
    %cst = arith.constant 5.000000e-01 : f64
    %cst_0 = arith.constant 1.5707963267948966 : f64
    %c1 = arith.constant 1 : index
    %c3 = arith.constant 3 : index
    %c0 = arith.constant 0 : index
    %0 = qc.alloc : !qc.qubit
    %1 = cbit.alloc(#cbit.init<zero>) {mqt.register_name = "result"} : !cbit.reg<3>
    scf.for %arg0 = %c0 to %c3 step %c1 {
      %2 = arith.subi %arg0, %c1 : index
      %3 = scf.for %arg1 = %c0 to %arg0 step %c1 iter_args(%arg2 = %cst_0) -> (f64) {
        %5 = arith.subi %2, %arg1 : index
        %6 = cbit.load %1[%5] : !cbit.reg<3>
        scf.if %6 {
          qc.p(%arg2) %0 : !qc.qubit
        }
        %7 = arith.mulf %arg2, %cst : f64
        scf.yield %7 : f64
      }
      qc.h %0 : !qc.qubit
      %4 = qc.measure %0 : !qc.qubit -> i1
      cbit.store %4, %1[%arg0] : !cbit.reg<3>
      qc.reset %0 : !qc.qubit
    }
    qc.dealloc %0 : !qc.qubit
    return %1 : !cbit.reg<3>
  }
}
