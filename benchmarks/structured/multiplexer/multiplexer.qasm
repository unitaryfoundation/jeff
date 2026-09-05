OPENQASM 3.0;
include "qelib1.inc";

// Quantum Multiplexer
// Prepares the controls uniformly and rotates the target based on their state.
// n must be at least 2.

input int n;
int num_controls = n - 1;

qubit[num_controls] controls;
qubit target;
bit[num_controls] c;
bit outcome;
reset controls;
reset target;

h controls;
float[64] theta = pi / 2.0;
for int i in [0:num_controls - 1] {
    ctrl @ ry(theta) controls[num_controls - 1 - i], target;
    theta = theta * 0.5;
}

c = measure controls;
outcome = measure target;
