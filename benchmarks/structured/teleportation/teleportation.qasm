OPENQASM 3.0;
include "qelib1.inc";

qubit msg;
qubit alice;
qubit bob;
reset msg;
reset alice;
reset bob;

// Alice has a qubit in an unknown state.
h msg;

// Alice and Bob share an entangled Bell pair.
h alice;
cx alice, bob;

// Alice prepares the teleport operation.
cx msg, alice;
h msg;

// Alice then measures her qubits.
bit a = measure msg;
bit b1 = measure alice;

// Bob applies corrections based on the measurement result.
if (b1) {
  x bob;
}
if (a) {
  z bob;
}

// Now bob is in the previous state of alice.

bit b2 = measure bob;
