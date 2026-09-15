module {
  func.func @main() -> !cbit.reg<8> attributes {mqt.entry_point} {
    %c2 = arith.constant 2 : index
    %c7 = arith.constant 7 : index
    %cst = arith.constant -1.5707963267948966 : f64
    %cst_0 = arith.constant -1.000000e+00 : f64
    %c12 = arith.constant 12 : index
    %cst_1 = arith.constant dense<[3.1415926535897931, 4.7123889803846897, 2.3561944901923448, 1.1780972450961724, 3.1415926535897931, 1.5707963267948966, 0.78539816339744828, 0.39269908169872414, 0.000000e+00, 3.1415926535897931, 1.5707963267948966, 0.78539816339744828, 3.1415926535897931, 1.5707963267948966, 3.9269908169872414, 1.9634954084936207]> : tensor<16xf64>
    %c4 = arith.constant 4 : index
    %cst_2 = arith.constant 5.000000e-01 : f64
    %cst_3 = arith.constant 1.5707963267948966 : f64
    %c1 = arith.constant 1 : index
    %c3 = arith.constant 3 : index
    %c0 = arith.constant 0 : index
    %0 = qc.alloc : !qc.qubit
    %alloc = memref.alloc() {mqt.register_name = "multiplicand"} : memref<3x!qc.qubit>
    %alloc_4 = memref.alloc() {mqt.register_name = "accumulator"} : memref<4x!qc.qubit>
    %1 = qc.alloc : !qc.qubit
    %2 = cbit.alloc(#cbit.init<zero>) {mqt.register_name = "result"} : !cbit.reg<8>
    qc.h %0 : !qc.qubit
    scf.for %arg0 = %c0 to %c3 step %c1 {
      %4 = memref.load %alloc[%arg0] : memref<3x!qc.qubit>
      qc.h %4 : !qc.qubit
    }
    scf.for %arg0 = %c0 to %c4 step %c1 {
      %4 = arith.subi %c3, %arg0 : index
      %5 = memref.load %alloc_4[%4] : memref<4x!qc.qubit>
      qc.h %5 : !qc.qubit
      %6 = arith.subi %c2, %arg0 : index
      %7 = scf.for %arg1 = %c0 to %4 step %c1 iter_args(%arg2 = %cst_3) -> (f64) {
        %8 = arith.subi %6, %arg1 : index
        %9 = memref.load %alloc_4[%8] : memref<4x!qc.qubit>
        %10 = memref.load %alloc_4[%4] : memref<4x!qc.qubit>
        qc.ctrl(%9) targets (%arg3 = %10) {
          qc.p(%arg2) %arg3 : !qc.qubit
          qc.yield
        } : {!qc.qubit}, {!qc.qubit}
        %11 = arith.mulf %arg2, %cst_2 : f64
        scf.yield %11 : f64
      }
    }
    scf.for %arg0 = %c0 to %c3 step %c1 {
      %4 = arith.muli %arg0, %c4 : index
      %5 = memref.load %alloc[%arg0] : memref<3x!qc.qubit>
      scf.for %arg1 = %c0 to %c4 step %c1 {
        %10 = arith.addi %4, %arg1 : index
        %extracted = tensor.extract %cst_1[%10] : tensor<16xf64>
        %11 = memref.load %alloc_4[%arg1] : memref<4x!qc.qubit>
        qc.ctrl(%0, %5) targets (%arg2 = %11) {
          qc.p(%extracted) %arg2 : !qc.qubit
          qc.yield
        } : {!qc.qubit, !qc.qubit}, {!qc.qubit}
      }
      scf.for %arg1 = %c0 to %c4 step %c1 {
        %10 = arith.addi %arg1, %c12 : index
        %extracted = tensor.extract %cst_1[%10] : tensor<16xf64>
        %11 = arith.mulf %extracted, %cst_0 : f64
        %12 = memref.load %alloc_4[%arg1] : memref<4x!qc.qubit>
        qc.p(%11) %12 : !qc.qubit
      }
      scf.for %arg1 = %c0 to %c4 step %c1 {
        %10 = arith.subi %arg1, %c1 : index
        %11 = scf.for %arg2 = %c0 to %arg1 step %c1 iter_args(%arg3 = %cst) -> (f64) {
          %13 = arith.subi %10, %arg2 : index
          %14 = memref.load %alloc_4[%13] : memref<4x!qc.qubit>
          %15 = memref.load %alloc_4[%arg1] : memref<4x!qc.qubit>
          qc.ctrl(%14) targets (%arg4 = %15) {
            qc.p(%arg3) %arg4 : !qc.qubit
            qc.yield
          } : {!qc.qubit}, {!qc.qubit}
          %16 = arith.mulf %arg3, %cst_2 : f64
          scf.yield %16 : f64
        }
        %12 = memref.load %alloc_4[%arg1] : memref<4x!qc.qubit>
        qc.h %12 : !qc.qubit
      }
      %6 = memref.load %alloc_4[%c3] : memref<4x!qc.qubit>
      qc.ctrl(%6) targets (%arg1 = %1) {
        qc.x %arg1 : !qc.qubit
        qc.yield
      } : {!qc.qubit}, {!qc.qubit}
      scf.for %arg1 = %c0 to %c4 step %c1 {
        %10 = arith.subi %c3, %arg1 : index
        %11 = memref.load %alloc_4[%10] : memref<4x!qc.qubit>
        qc.h %11 : !qc.qubit
        %12 = arith.subi %c2, %arg1 : index
        %13 = scf.for %arg2 = %c0 to %10 step %c1 iter_args(%arg3 = %cst_3) -> (f64) {
          %14 = arith.subi %12, %arg2 : index
          %15 = memref.load %alloc_4[%14] : memref<4x!qc.qubit>
          %16 = memref.load %alloc_4[%10] : memref<4x!qc.qubit>
          qc.ctrl(%15) targets (%arg4 = %16) {
            qc.p(%arg3) %arg4 : !qc.qubit
            qc.yield
          } : {!qc.qubit}, {!qc.qubit}
          %17 = arith.mulf %arg3, %cst_2 : f64
          scf.yield %17 : f64
        }
      }
      scf.for %arg1 = %c0 to %c4 step %c1 {
        %10 = arith.addi %arg1, %c12 : index
        %extracted = tensor.extract %cst_1[%10] : tensor<16xf64>
        %11 = memref.load %alloc_4[%arg1] : memref<4x!qc.qubit>
        qc.ctrl(%1) targets (%arg2 = %11) {
          qc.p(%extracted) %arg2 : !qc.qubit
          qc.yield
        } : {!qc.qubit}, {!qc.qubit}
      }
      scf.for %arg1 = %c0 to %c4 step %c1 {
        %10 = arith.addi %4, %arg1 : index
        %extracted = tensor.extract %cst_1[%10] : tensor<16xf64>
        %11 = arith.mulf %extracted, %cst_0 : f64
        %12 = memref.load %alloc_4[%arg1] : memref<4x!qc.qubit>
        qc.ctrl(%0, %5) targets (%arg2 = %12) {
          qc.p(%11) %arg2 : !qc.qubit
          qc.yield
        } : {!qc.qubit, !qc.qubit}, {!qc.qubit}
      }
      scf.for %arg1 = %c0 to %c4 step %c1 {
        %10 = arith.subi %arg1, %c1 : index
        %11 = scf.for %arg2 = %c0 to %arg1 step %c1 iter_args(%arg3 = %cst) -> (f64) {
          %13 = arith.subi %10, %arg2 : index
          %14 = memref.load %alloc_4[%13] : memref<4x!qc.qubit>
          %15 = memref.load %alloc_4[%arg1] : memref<4x!qc.qubit>
          qc.ctrl(%14) targets (%arg4 = %15) {
            qc.p(%arg3) %arg4 : !qc.qubit
            qc.yield
          } : {!qc.qubit}, {!qc.qubit}
          %16 = arith.mulf %arg3, %cst_2 : f64
          scf.yield %16 : f64
        }
        %12 = memref.load %alloc_4[%arg1] : memref<4x!qc.qubit>
        qc.h %12 : !qc.qubit
      }
      %7 = memref.load %alloc_4[%c3] : memref<4x!qc.qubit>
      qc.x %7 : !qc.qubit
      %8 = memref.load %alloc_4[%c3] : memref<4x!qc.qubit>
      qc.ctrl(%8) targets (%arg1 = %1) {
        qc.x %arg1 : !qc.qubit
        qc.yield
      } : {!qc.qubit}, {!qc.qubit}
      %9 = memref.load %alloc_4[%c3] : memref<4x!qc.qubit>
      qc.x %9 : !qc.qubit
      scf.for %arg1 = %c0 to %c4 step %c1 {
        %10 = arith.subi %c3, %arg1 : index
        %11 = memref.load %alloc_4[%10] : memref<4x!qc.qubit>
        qc.h %11 : !qc.qubit
        %12 = arith.subi %c2, %arg1 : index
        %13 = scf.for %arg2 = %c0 to %10 step %c1 iter_args(%arg3 = %cst_3) -> (f64) {
          %14 = arith.subi %12, %arg2 : index
          %15 = memref.load %alloc_4[%14] : memref<4x!qc.qubit>
          %16 = memref.load %alloc_4[%10] : memref<4x!qc.qubit>
          qc.ctrl(%15) targets (%arg4 = %16) {
            qc.p(%arg3) %arg4 : !qc.qubit
            qc.yield
          } : {!qc.qubit}, {!qc.qubit}
          %17 = arith.mulf %arg3, %cst_2 : f64
          scf.yield %17 : f64
        }
      }
      scf.for %arg1 = %c0 to %c4 step %c1 {
        %10 = arith.addi %4, %arg1 : index
        %extracted = tensor.extract %cst_1[%10] : tensor<16xf64>
        %11 = memref.load %alloc_4[%arg1] : memref<4x!qc.qubit>
        qc.ctrl(%0, %5) targets (%arg2 = %11) {
          qc.p(%extracted) %arg2 : !qc.qubit
          qc.yield
        } : {!qc.qubit, !qc.qubit}, {!qc.qubit}
      }
    }
    scf.for %arg0 = %c0 to %c4 step %c1 {
      %4 = arith.subi %arg0, %c1 : index
      %5 = scf.for %arg1 = %c0 to %arg0 step %c1 iter_args(%arg2 = %cst) -> (f64) {
        %7 = arith.subi %4, %arg1 : index
        %8 = memref.load %alloc_4[%7] : memref<4x!qc.qubit>
        %9 = memref.load %alloc_4[%arg0] : memref<4x!qc.qubit>
        qc.ctrl(%8) targets (%arg3 = %9) {
          qc.p(%arg2) %arg3 : !qc.qubit
          qc.yield
        } : {!qc.qubit}, {!qc.qubit}
        %10 = arith.mulf %arg2, %cst_2 : f64
        scf.yield %10 : f64
      }
      %6 = memref.load %alloc_4[%arg0] : memref<4x!qc.qubit>
      qc.h %6 : !qc.qubit
    }
    scf.for %arg0 = %c0 to %c4 step %c1 {
      %4 = memref.load %alloc_4[%arg0] : memref<4x!qc.qubit>
      %5 = qc.measure %4 : !qc.qubit -> i1
      cbit.store %5, %2[%arg0] : !cbit.reg<8>
    }
    scf.for %arg0 = %c0 to %c3 step %c1 {
      %4 = arith.addi %arg0, %c4 : index
      %5 = memref.load %alloc[%arg0] : memref<3x!qc.qubit>
      %6 = qc.measure %5 : !qc.qubit -> i1
      cbit.store %6, %2[%4] : !cbit.reg<8>
    }
    %3 = qc.measure %0 : !qc.qubit -> i1
    cbit.store %3, %2[%c7] : !cbit.reg<8>
    qc.dealloc %0 : !qc.qubit
    qc.dealloc %1 : !qc.qubit
    memref.dealloc %alloc : memref<3x!qc.qubit>
    memref.dealloc %alloc_4 : memref<4x!qc.qubit>
    return %2 : !cbit.reg<8>
  }
}
