module {
  func.func @main() -> !cbit.reg<3> attributes {mqt.entry_point} {
    %c3 = arith.constant 3 : index
    %c1 = arith.constant 1 : index
    %c0 = arith.constant 0 : index
    %alloc = memref.alloc() {mqt.register_name = "q"} : memref<3x!qc.qubit>
    %0 = cbit.alloc(#cbit.init<zero>) {mqt.register_name = "result"} : !cbit.reg<3>
    %1 = memref.load %alloc[%c0] : memref<3x!qc.qubit>
    qc.h %1 : !qc.qubit
    scf.for %arg0 = %c1 to %c3 step %c1 {
      %2 = arith.subi %arg0, %c1 : index
      %3 = memref.load %alloc[%2] : memref<3x!qc.qubit>
      %4 = memref.load %alloc[%arg0] : memref<3x!qc.qubit>
      qc.ctrl(%3) targets (%arg1 = %4) {
        qc.x %arg1 : !qc.qubit
        qc.yield
      } : {!qc.qubit}, {!qc.qubit}
    }
    scf.for %arg0 = %c0 to %c3 step %c1 {
      %2 = memref.load %alloc[%arg0] : memref<3x!qc.qubit>
      %3 = qc.measure %2 : !qc.qubit -> i1
      cbit.store %3, %0[%arg0] : !cbit.reg<3>
    }
    memref.dealloc %alloc : memref<3x!qc.qubit>
    return %0 : !cbit.reg<3>
  }
}
