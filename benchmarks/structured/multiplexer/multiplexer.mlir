// Quantum Multiplexer (Uniformly Controlled RY Gates) -- QC dialect.
//
// Hand-written counterpart of multiplexer.qasm, on 5 qubits: 4 control qubits
// plus one target. Each of the 16 control states selects its own RY angle.
//
// The angle table is a `tensor<16xf64>` built with `tensor.from_elements`,
// which the conversion lowers to a `jeff` float array. multiplexer.qasm needs
// `array[angle, 16]` for the same purpose, which the OpenQASM frontend rejects.
//
// multiplexer.qasm writes the gate operands as `controls[0:num_controls-1],
// target`. This file takes all 4 control qubits as controls and the target as
// target, which is the reading consistent with `ctrl(num_controls)`.

module {
  func.func @main() -> (memref<4xi1>, memref<1xi1>) attributes {passthrough = ["entry_point"]} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %c2 = arith.constant 2 : index
    %c3 = arith.constant 3 : index
    %num_controls = arith.constant 4 : index
    %num_states = arith.constant 16 : index

    %a0 = arith.constant 0.0 : f64
    %a1 = arith.constant 0.19634954084936207 : f64
    %a2 = arith.constant 0.39269908169872414 : f64
    %a3 = arith.constant 0.5890486225480862 : f64
    %a4 = arith.constant 0.7853981633974483 : f64
    %a5 = arith.constant 0.9817477042468103 : f64
    %a6 = arith.constant 1.1780972450961724 : f64
    %a7 = arith.constant 1.3744467859455345 : f64
    %a8 = arith.constant 1.5707963267948966 : f64
    %a9 = arith.constant 1.7671458676442586 : f64
    %a10 = arith.constant 1.9634954084936207 : f64
    %a11 = arith.constant 2.1598449493429825 : f64
    %a12 = arith.constant 2.356194490192345 : f64
    %a13 = arith.constant 2.552544031041707 : f64
    %a14 = arith.constant 2.748893571891069 : f64
    %a15 = arith.constant 2.945243112740431 : f64
    %angles = tensor.from_elements %a0, %a1, %a2, %a3, %a4, %a5, %a6, %a7, %a8, %a9, %a10, %a11, %a12, %a13, %a14, %a15 : tensor<16xf64>

    %controls = memref.alloc() : memref<4x!qc.qubit>
    %target = memref.alloc() : memref<1x!qc.qubit>
    %c = memref.alloc() : memref<4xi1>
    %outcome = memref.alloc() : memref<1xi1>

    scf.for %i = %c0 to %num_controls step %c1 {
      %qi = memref.load %controls[%i] : memref<4x!qc.qubit>
      qc.reset %qi : !qc.qubit
    }
    %t0 = memref.load %target[%c0] : memref<1x!qc.qubit>
    qc.reset %t0 : !qc.qubit

    scf.for %state = %c0 to %num_states step %c1 {
      scf.for %bit_pos = %c0 to %num_controls step %c1 {
        %shifted = arith.shrsi %state, %bit_pos : index
        %bit = arith.andi %shifted, %c1 : index
        %is_zero = arith.cmpi eq, %bit, %c0 : index
        scf.if %is_zero {
          %qb = memref.load %controls[%bit_pos] : memref<4x!qc.qubit>
          qc.x %qb : !qc.qubit
        }
      }

      %angle = tensor.extract %angles[%state] : tensor<16xf64>
      %k0 = memref.load %controls[%c0] : memref<4x!qc.qubit>
      %k1 = memref.load %controls[%c1] : memref<4x!qc.qubit>
      %k2 = memref.load %controls[%c2] : memref<4x!qc.qubit>
      %k3 = memref.load %controls[%c3] : memref<4x!qc.qubit>
      %tq = memref.load %target[%c0] : memref<1x!qc.qubit>
      qc.ctrl(%k0, %k1, %k2, %k3) targets (%arg0 = %tq) {
        qc.ry(%angle) %arg0 : !qc.qubit
        qc.yield
      } : {!qc.qubit, !qc.qubit, !qc.qubit, !qc.qubit}, {!qc.qubit}

      scf.for %bit_pos = %c0 to %num_controls step %c1 {
        %shifted = arith.shrsi %state, %bit_pos : index
        %bit = arith.andi %shifted, %c1 : index
        %is_zero = arith.cmpi eq, %bit, %c0 : index
        scf.if %is_zero {
          %qb = memref.load %controls[%bit_pos] : memref<4x!qc.qubit>
          qc.x %qb : !qc.qubit
        }
      }
    }

    scf.for %i = %c0 to %num_controls step %c1 {
      %qi = memref.load %controls[%i] : memref<4x!qc.qubit>
      %m = qc.measure %qi : !qc.qubit -> i1
      memref.store %m, %c[%i] : memref<4xi1>
    }
    %tm = memref.load %target[%c0] : memref<1x!qc.qubit>
    %mo = qc.measure %tm : !qc.qubit -> i1
    memref.store %mo, %outcome[%c0] : memref<1xi1>

    memref.dealloc %controls : memref<4x!qc.qubit>
    memref.dealloc %target : memref<1x!qc.qubit>
    return %c, %outcome : memref<4xi1>, memref<1xi1>
  }
}
