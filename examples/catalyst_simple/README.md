# Simple test circuit from Catalyst

This example tests basic features in the Catalyst -> *jeff* conversion, including functions, numeric
constants, quantum registers, and basic and parametrized gates as well as measurement.

The Catalyst converter prototype can be found [here](https://github.com/PennyLaneAI/catalyst-jeff).


### Catalyst MLIR

```mlir
func.func @hello() -> i1 {
    %c0 = arith.constant 0 : i64
    %c5 = arith.constant 5 : i64
    %phi = arith.constant 0.1 : f64

    %r = quantum.alloc(%c5) : !quantum.reg
    %q = quantum.extract %r[%c0] : !quantum.reg -> !quantum.bit

    %q1 = quantum.custom "Hadamard"() %q : !quantum.bit
    %q2 = quantum.custom "RY"(%phi) %q1 : !quantum.bit
    %m, %q3 = quantum.measure %q2 : i1, !quantum.bit

    %r1 = quantum.insert %r[%c0], %q3 : !quantum.reg, !quantum.bit
    quantum.dealloc %r1 : !quantum.reg

    func.return %m : i1
}

func.func @world() {
    func.return
}
```

This input can be run through Catalyst's `opt` tool to generate the encoded IR:

```sh
quantum-opt catalyst_simple.mlir --load-pass-plugin=catalyst-jeff.so --pass-pipeline="builtin.module(jeff-export)"
```

To obtain the human-readable (.txt) form:

```sh
capnp decode jeff.capnp Module < catalyst_simple.jeff
```
