OPENQASM 3.0;
include "qelib1.inc";

// n must be at least 2.

input int n;

qubit[n-1] q;
qubit anc;
bit[n-1] c;
reset q;
reset anc;

h q;
x anc;

// Iteratively apply gates
for int i in [0:n-2] {
    ctrl @ pow(2**i) @ p(3*pi/8) q[i], anc;
}

// Apply reverse QFT
for int i in [0:int(ceiling((n-2)/2))-1] {
    swap q[i], q[n - 2 - i];
}
for int i in [0:n-2] {
    for int j in [i+1:n-2] {
        ctrl @ p(-pi/2**(j-i)) q[j], q[i];
    }
    h q[i];
}

c = measure q;
