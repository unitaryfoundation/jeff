# Frequently asked questions

*Jeff* was designed to solve a few very specific problems the field is currently encountering:

- **We need to be able to compile large, complex, quantum algorithms, and this is an interdisclinary
  effort**. Compilation is an incredibly important component of quantum computing infrastructure.
  The inability to optimize large algorithms for future fault-tolerant hardware will extend
  (or block!) timelines for utility-scale quantum computation.

  However, there is still a lot of work to do, and a lot of uncertainty. We need to:

  - continue to make new theoretical compilation breakthroughs; 
  - identify the most-promising large scale algorithms; and finally,
  - figure out how to make this practical through quantum software.
  
  To do so, we need to bridge the gap between researchers doing fundamental compilation and
  algorithmic research, and quantum software developers.

  - **How can we share results and ideas faster, within a common framework?**
  - **How do we make sure we are speaking a common language, and aware of challenges and approaches
    on both sides?**

- **Quantum algorithms have structure that we need to preserve for scalability, but thinking
    in circuits is holding us back**. This is already recognized and built into common quantum
    software libraries(Qiskit, CUDA-Q, PennyLane, UCC, Guppy, TKET, etc.) and formats
    (QIR, OpenQASM3, etc.), but introduces complexity into the compilation pipeline.

  * While we are starting to see [exceptions](https://arxiv.org/abs/2410.23493), most theoretical
    compilation work is still assuming that compilation passes are applied to a straight line list
    of quantum instructions, and implemented using formats such as OpenQASM2. It can then be highly non-trivial to then map such passes to apply to structured quantum programs. How do we encourage the field as a whole to consider compiling structured programs *by default*?

  * There is tension between maximal optimization and compact program representation.
    There are still a lot of questions we need to consider and resolve when it comes to compiling
    dynamic, structured programs. For example, the more compact the program representation (which is great for compilation scalability!) the less information we potentially have up-front to
    maximally optimize programs at compile time. How do we deal with such scenarios?

## Is *Jeff* meant to be an intermediate format that quantum software packages to manipulate?

## Why design a non-human readable format?

## How did you decide what goes into the schema?

## Why do we need program structure?

## Why Cap'n Proto?

## Isn't this just *another* format standard?

## Why not format X?

### Why not OpenQASM2?

### Why not OpenQASM3?

### Why not QIR?

### Why not MLIR?
