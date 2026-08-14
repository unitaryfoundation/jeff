OPENQASM 3.0;
include "qelib1.inc";

const int n = 7;

qubit[n] q;
bit[n] c;
reset q;

h q[0];
for int i in [1:n-1] {
  cx q[i - 1], q[i];
}

c = measure q;
