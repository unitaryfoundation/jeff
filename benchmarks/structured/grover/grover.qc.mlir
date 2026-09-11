module {
  func.func @main() -> !cbit.reg<2> attributes {mqt.entry_point} {
    %c2 = arith.constant 2 : index
    %c1 = arith.constant 1 : index
    %c0 = arith.constant 0 : index
    %alloc = memref.alloc() {mqt.register_name = "q"} : memref<2x!qc.qubit>
    %0 = memref.load %alloc[%c0] : memref<2x!qc.qubit>
    %1 = memref.load %alloc[%c1] : memref<2x!qc.qubit>
    %2 = cbit.alloc(#cbit.init<zero>) {mqt.register_name = "result"} : !cbit.reg<2>
    scf.for %arg0 = %c0 to %c2 step %c1 {
      %3 = memref.load %alloc[%arg0] : memref<2x!qc.qubit>
      qc.h %3 : !qc.qubit
    }
    qc.ctrl(%0) targets (%arg0 = %1) {
      qc.z %arg0 : !qc.qubit
      qc.yield
    } : {!qc.qubit}, {!qc.qubit}
    scf.for %arg0 = %c0 to %c2 step %c1 {
      %3 = memref.load %alloc[%arg0] : memref<2x!qc.qubit>
      qc.h %3 : !qc.qubit
    }
    scf.for %arg0 = %c0 to %c2 step %c1 {
      %3 = memref.load %alloc[%arg0] : memref<2x!qc.qubit>
      qc.x %3 : !qc.qubit
    }
    qc.ctrl(%0) targets (%arg0 = %1) {
      qc.z %arg0 : !qc.qubit
      qc.yield
    } : {!qc.qubit}, {!qc.qubit}
    scf.for %arg0 = %c0 to %c2 step %c1 {
      %3 = memref.load %alloc[%arg0] : memref<2x!qc.qubit>
      qc.x %3 : !qc.qubit
    }
    scf.for %arg0 = %c0 to %c2 step %c1 {
      %3 = memref.load %alloc[%arg0] : memref<2x!qc.qubit>
      qc.h %3 : !qc.qubit
    }
    scf.for %arg0 = %c0 to %c2 step %c1 {
      %3 = memref.load %alloc[%arg0] : memref<2x!qc.qubit>
      %4 = qc.measure %3 : !qc.qubit -> i1
      cbit.store %4, %2[%arg0] : !cbit.reg<2>
    }
    memref.dealloc %alloc : memref<2x!qc.qubit>
    return %2 : !cbit.reg<2>
  }
}
