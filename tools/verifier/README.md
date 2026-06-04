# jeff verifier

This tool verifies encoded `jeff` modules against structural constraints that are not guaranteed by the Cap'n Proto schema alone.

Run it from the repository root with:

```bash
uv run python -m tools.verifier.jeff_verifier path/to/module.jeff
```

The command exits with status `0` when all files pass verification and `1` when any verifier diagnostic is emitted.
