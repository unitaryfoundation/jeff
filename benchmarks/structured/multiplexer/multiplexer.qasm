OPENQASM 3.0;

// Quantum Multiplexer (Uniformly Controlled RY Gates)
// Applies 2^(n-1) different RY rotations based on n-1 control qubits

const int n = 5;
const int num_controls = n - 1;
const int num_states = 2**num_controls;
const array[angle, num_states] angles = {
    0*pi/16, 1*pi/16, 2*pi/16, 3*pi/16,
    4*pi/16, 5*pi/16, 6*pi/16, 7*pi/16,
    8*pi/16, 9*pi/16, 10*pi/16, 11*pi/16,
    12*pi/16, 13*pi/16, 14*pi/16, 15*pi/16
};

qubit[num_controls] controls;
qubit target;
bit[num_controls] c;
bit outcome;
reset controls;
reset target;

for int state in [0:num_states-1] {
    // We want to apply angles[state] when controls equal 'state'
    // State is a binary number: e.g., state=5 = 0b110 for 3 controls
    // means control[0]=0, control[1]=1, control[2]=1

    // Extract each bit: if 0, we need to flip the corresponding qubit
    // Bit i is: (state >> i) & 1
    for int bit_pos in [0:num_controls-1] {
        int bit_value = (state >> bit_pos) & 1;
        if (bit_value == 0) {
            x controls[bit_pos];  // Flip this control
        }
    }

    // Apply fully-controlled gate (all controls must be |1⟩)
    ctrl(num_controls) @ ry(angles[state]) controls[0:num_controls-1], target;

    // Flip controls back
    for int bit_pos in [0:num_controls-1] {
        int bit_value = (state >> bit_pos) & 1;
        if (bit_value == 0) {
            x controls[bit_pos];  // Flip back
        }
    }
}

c = measure controls;
outcome = measure target;
