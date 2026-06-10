#include <fcntl.h>
#include <unistd.h>
#include <iostream>
#include <fstream>
#include <string>
#include <capnp/message.h>
#include <capnp/serialize-packed.h>
#include <kj/io.h>
#include "qiskit_jeff.h"

using namespace jeff::qiskit_convert;

void usage() {
    std::cerr << "Usage:\n"
              << "  jeff-qiskit-convert to-qiskit <input.jeff>\n"
              << "  jeff-qiskit-convert from-qiskit <output.jeff>\n";
    exit(1);
}

int main(int argc, char** argv) {
    if (argc < 3) usage();

    std::string mode = argv[1];
    std::string file_path = argv[2];

    if (mode == "to-qiskit") {
        // Just for validation that we can read and parse it to QkCircuit
        int fd = open(file_path.c_str(), O_RDONLY);
        if (fd < 0) {
            std::cerr << "Failed to open input file" << std::endl;
            return 1;
        }
        
        ::capnp::PackedFdMessageReader message(fd);
        auto module = message.getRoot<Module>();
        
        QkCircuit* qc = jeff_to_qiskit(module);
        
        std::cout << "Successfully converted to QkCircuit with "
                  << qk_circuit_num_qubits(qc) << " qubits and "
                  << qk_circuit_num_instructions(qc) << " instructions." << std::endl;
                  
        qk_circuit_free(qc);
        close(fd);
    } else if (mode == "from-qiskit") {
        // Dummy creation for manual verification purposes. 
        // Real testing happens in python bindings testing the round-trip directly.
        QkCircuit* qc = qk_circuit_new(2, 2);
        uint32_t q0[1] = {0};
        uint32_t q01[2] = {0, 1};
        qk_circuit_gate(qc, QkGate_H, q0, nullptr);
        qk_circuit_gate(qc, QkGate_CX, q01, nullptr);
        qk_circuit_measure(qc, 0, 0);
        qk_circuit_measure(qc, 1, 1);
        
        ::capnp::MallocMessageBuilder message;
        qiskit_to_jeff(qc, message);
        
        int fd = open(file_path.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0666);
        if (fd < 0) {
            std::cerr << "Failed to open output file" << std::endl;
            return 1;
        }
        
        ::capnp::writePackedMessageToFd(fd, message);
        close(fd);
        qk_circuit_free(qc);
        
        std::cout << "Successfully wrote generated jeff file to " << file_path << std::endl;
    } else {
        usage();
    }

    return 0;
}
