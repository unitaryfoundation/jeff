module {
  func.func @main() -> !cbit.reg<1> attributes {mqt.entry_point} {
    %c0 = arith.constant 0 : index
    %0 = qc.alloc : !qc.qubit
    %1 = qc.alloc : !qc.qubit
    %2 = qc.alloc : !qc.qubit
    %3 = cbit.alloc(#cbit.init<zero>) {mqt.register_name = "result"} : !cbit.reg<1>
    qc.h %0 : !qc.qubit
    qc.h %1 : !qc.qubit
    qc.ctrl(%1) targets (%arg0 = %2) {
      qc.x %arg0 : !qc.qubit
      qc.yield
    } : {!qc.qubit}, {!qc.qubit}
    qc.ctrl(%0) targets (%arg0 = %1) {
      qc.x %arg0 : !qc.qubit
      qc.yield
    } : {!qc.qubit}, {!qc.qubit}
    qc.h %0 : !qc.qubit
    %4 = qc.measure %0 : !qc.qubit -> i1
    %5 = qc.measure %1 : !qc.qubit -> i1
    scf.if %5 {
      qc.x %2 : !qc.qubit
    }
    scf.if %4 {
      qc.z %2 : !qc.qubit
    }
    qc.h %2 : !qc.qubit
    %6 = qc.measure %2 : !qc.qubit -> i1
    cbit.store %6, %3[%c0] : !cbit.reg<1>
    qc.dealloc %0 : !qc.qubit
    qc.dealloc %1 : !qc.qubit
    qc.dealloc %2 : !qc.qubit
    return %3 : !cbit.reg<1>
  }
}
