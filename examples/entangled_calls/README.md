# Fully entangled 5-qubit w/ Func Calls

An example of a more complex set of functions, directly translated from C++. The main function allocates 5 qubits and fully entangles them, performing a measurement into a classical int array. It then collects all the measurements into a single int by shl+adding them and returns the result. The wrapping function simply calls the main one.

### Pseudocode

```python
def main():
    sample()

def sample() -> int:
    qs = [qubit() for _ in range(5)]
    h(qs[0])
    for i in range(4):
        cx(qs[i], qs[i + 1])
    res = 0
    for q in qs:
        res += measure(q)
        res <<= 1
    return res
```
