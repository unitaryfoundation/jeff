module {
  func.func @main() -> !cbit.reg<3> attributes {mqt.entry_point} {
    %cst = arith.constant -1.5707963267948966 : f64
    %cst_0 = arith.constant dense<[3.1415926535897931, 1.5707963267948966, 3.9269908169872414]> : tensor<3xf64>
    %c3 = arith.constant 3 : index
    %cst_1 = arith.constant 5.000000e-01 : f64
    %cst_2 = arith.constant 1.5707963267948966 : f64
    %c2 = arith.constant 2 : index
    %c1 = arith.constant 1 : index
    %c0 = arith.constant 0 : index
    %alloc = memref.alloc() {mqt.register_name = "sum"} : memref<3x!qc.qubit>
    %0 = memref.load %alloc[%c0] : memref<3x!qc.qubit>
    qc.x %0 : !qc.qubit
    %1 = cbit.alloc(#cbit.init<zero>) {mqt.register_name = "result"} : !cbit.reg<3>
    scf.for %arg0 = %c0 to %c3 step %c1 {
      %2 = arith.subi %c2, %arg0 : index
      %3 = memref.load %alloc[%2] : memref<3x!qc.qubit>
      qc.h %3 : !qc.qubit
      %4 = arith.subi %c1, %arg0 : index
      %5 = scf.for %arg1 = %c0 to %2 step %c1 iter_args(%arg2 = %cst_2) -> (f64) {
        %6 = arith.subi %4, %arg1 : index
        %7 = memref.load %alloc[%6] : memref<3x!qc.qubit>
        %8 = memref.load %alloc[%2] : memref<3x!qc.qubit>
        qc.ctrl(%7) targets (%arg3 = %8) {
          qc.p(%arg2) %arg3 : !qc.qubit
          qc.yield
        } : {!qc.qubit}, {!qc.qubit}
        %9 = arith.mulf %arg2, %cst_1 : f64
        scf.yield %9 : f64
      }
    }
    scf.for %arg0 = %c0 to %c3 step %c1 {
      %extracted = tensor.extract %cst_0[%arg0] : tensor<3xf64>
      %2 = memref.load %alloc[%arg0] : memref<3x!qc.qubit>
      qc.p(%extracted) %2 : !qc.qubit
    }
    scf.for %arg0 = %c0 to %c3 step %c1 {
      %2 = arith.subi %arg0, %c1 : index
      %3 = scf.for %arg1 = %c0 to %arg0 step %c1 iter_args(%arg2 = %cst) -> (f64) {
        %5 = arith.subi %2, %arg1 : index
        %6 = memref.load %alloc[%5] : memref<3x!qc.qubit>
        %7 = memref.load %alloc[%arg0] : memref<3x!qc.qubit>
        qc.ctrl(%6) targets (%arg3 = %7) {
          qc.p(%arg2) %arg3 : !qc.qubit
          qc.yield
        } : {!qc.qubit}, {!qc.qubit}
        %8 = arith.mulf %arg2, %cst_1 : f64
        scf.yield %8 : f64
      }
      %4 = memref.load %alloc[%arg0] : memref<3x!qc.qubit>
      qc.h %4 : !qc.qubit
    }
    scf.for %arg0 = %c0 to %c3 step %c1 {
      %2 = memref.load %alloc[%arg0] : memref<3x!qc.qubit>
      %3 = qc.measure %2 : !qc.qubit -> i1
      cbit.store %3, %1[%arg0] : !cbit.reg<3>
    }
    memref.dealloc %alloc : memref<3x!qc.qubit>
    return %1 : !cbit.reg<3>
  }
}
