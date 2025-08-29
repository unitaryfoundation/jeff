# Motivation

*Jeff* was designed to solve a few very specific problems the field is currently encountering.

## Better interdisciplinary support.

**We need to be able to compile large, complex, quantum algorithms, and this is an interdisciplinary
effort.**

Compilation is an incredibly important component of quantum computing infrastructure. The inability
to optimize large algorithms for future fault-tolerant hardware will extend (or block!) timelines
for utility-scale quantum computation.

However, there is still a lot of work to do, and a lot of uncertainty. We need to:

- continue to make new theoretical compilation breakthroughs; 
- identify the most-promising large scale algorithms; and finally,
- figure out how to make this practical through quantum software.
  
To do so, we need to bridge the gap between researchers doing fundamental compilation and
algorithmic research, and quantum software developers.

- **How can we share results and ideas faster, within a common framework?**
- **How do we make sure we are speaking a common language, and aware of challenges and approaches
    on both sides?**

## Thinking beyond circuits.

**Quantum algorithms have structure that we need to preserve for scalability, but thinking in
circuits is holding us back**.

This is already recognized and built into common quantum software
libraries (Qiskit, CUDA-Q, PennyLane, UCC, Guppy, TKET, etc.) and formats (QIR, OpenQASM3, etc.),
but introduces complexity into the compilation pipeline.

- While we are starting to see [exceptions](https://arxiv.org/abs/2410.23493), most theoretical
  compilation work is still assuming that compilation passes are applied to a straight line list
  of quantum instructions, and implemented using formats such as OpenQASM2. It can then be highly
  non-trivial to then map such passes to apply to structured quantum programs. How do we
  encourage the field as a whole to consider compiling structured programs *by default*?

- There is tension between maximal optimization and compact program representation. There are
  still a lot of questions we need to consider and resolve when it comes to compiling dynamic,
  structured programs. For example, the more compact the program representation (which is great
  for compilation scalability!) the less information we potentially have up-front to maximally
  optimize programs at compile time. How do we deal with such scenarios?

## Bridging the software divide.

**To solve the above problems, we need better interoperability and visibility between compilers**.

There are a wealth of quantum software compilers currently available, but they are not
interoperable, and it is often hard to inspect/debug to see how your program changes. Furthermore,
when *implementing* your own compilation pass, you often need to choose which framework to support,
making it harder to share ideas and knowledge.

Note that some formats have become de-facto exchange formats for compilers (such as OpenQASM), but
were not designed to be exchange formats for compilers, and as such suffer from quantum
representations that are not ideal for high-level optimization, lacklustre tooling, and
inefficiencies.

Furthermore, as some compiler frameworks become more complex, making use of large classical
toolchains such as LLVM and MLIR, the [overhead to contributing novel compilation passes is growing
significantly](https://arxiv.org/abs/2411.18682). **We need to reduce this overhead while still
allowing use of such tooling**.

## Better visibility into software compilation.

**We need to be able to visualize and debug our programs as they are modified by software compilers**.

As compilers become more complex (using tooling such as LLVM, as well as producing
complicated program structures), it is becoming more and more difficult to debug compilation, or
even *visualize* how our programs are changing.

There is a huge need for improved visualization and debugging tooling for software compilers, but
this is a highly non-trivial matter! As such, an exchange format that allows compiler frameworks to
share (or dispatch to) visualization and debugging tools allows us to work together and build up
common abstractions and visualizations.

## There is still so much uncertainty.

**We need to move fast, without slowing down development of new ideas.**

The danger of introducing new exchange formats or standards is that they themselves may slow down
development — perhaps because of a governance structure with too much process and/or stakeholders,
or simply because the format is too rigid and doesn't permit extensibility for new ideas.

This is something we wish to avoid — Jeff is *not* a standard we need all stakeholders to adopt, but an exchange format localized to compilers, designed to
be easily extensible. Additional information for program representation and compilation can be added
directly, and will be taken into account by software frameworks that understand the direction.
Further, development will happen out in the open, on GitHub.
