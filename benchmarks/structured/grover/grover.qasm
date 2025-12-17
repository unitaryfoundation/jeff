OPENQASM 3.0;
include "qelib1.inc";

input int n;

qubit[n-1] q;
qubit flag;
bit[n-1] c;
reset q;
reset flag;

h q;
x flag;

int num_iterations = int(ceiling(pi / 4 * sqrt(2**(n-1))));

for int i in [1:num_iterations] {
    // oracle
    ctrl(n-1) @ z q[0:n-1], flag;

    // diffusion
    h q;
    x q;
    ctrl(n-2) @ z q[0:n-2], q[n-1];
    x q;
    h q;
}

c = measure q;
