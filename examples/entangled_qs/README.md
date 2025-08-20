# Fully entangled 5-qubit

An example of a very simple kernel, with no inputs and no outputs. It allocates 5 qubits and fully entangles them, performing a measurement into a classical int array.


### Pseudocode

```python
def main():
    q = [qubit() for _ in range(5)]
    h(q[0])
    for i in range(4):
        cx(q[i], q[i + 1])
    bits = measure_all(q)
```
