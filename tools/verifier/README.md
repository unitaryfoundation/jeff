# jeff verifier

This tool validates encoded `.jeff` modules beyond the structural guarantees provided
by the Cap'n Proto schema.

Run it from the repository root:

```bash
uv run python -m tools.verifier examples/qubits/qubits.jeff
```

The command exits with status code `0` when every input file is valid. It prints all
validation errors and exits with status code `1` when any file is invalid.

The first version checks:

- module version and entrypoint structure
- value references against the function value table
- use-before-definition inside each region
- instruction input/output type signatures
- integer bitwidth and float precision consistency for numeric operations
- exactly-once use of `qubit` and `qureg` values
- isolation of nested regions from values defined above them
