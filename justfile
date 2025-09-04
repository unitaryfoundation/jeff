# List the available commands
help:
    @just --list --justfile {{justfile()}}

# Prepare the environment for development, installing all the dependencies and
# setting up the pre-commit hooks.
setup:
    uv run pre-commit install -t pre-commit

# Run the pre-commit checks.
check:
    uv run pre-commit run --all-files

# Run the tests for all the bindings.
test: test-rs test-py
# Run the tests for the rust code.
test-rs *TEST_ARGS:
    cargo test {{TEST_ARGS}}
# Run the tests for the python code.
test-py *TEST_ARGS:
    uv run pytest {{TEST_ARGS}}

# Auto-fix all lints.
fix: fix-rs fix-py
# Auto-fix all the lints in the rust code.
fix-rs:
    cargo clippy --all-targets --all-features --workspace --fix --allow-staged --allow-dirty
# Auto-fix all the lints in the python code.
fix-py:
    uv run ruff check --fix impl/py

# Format all the code in the repository.
format: format-rs format-py
# Format the rust code.
format-rs:
    cargo fmt --all
# Format the python code.
format-py:
    uv run ruff format impl/py

# Generate a test coverage report.
coverage: coverage-rs coverage-py
# Generate a test coverage report for the rust code.
coverage-rs:
    cargo llvm-cov --lcov > lcov.info
# Generate a test coverage report for the python code.
coverage-py:
    uv run pytest --cov=./ --cov-report=html

# Update the capnproto definitions.
update-capnp:
    # Always use the latest version of capnproto-rust
    cargo binstall capnpc || cargo install capnpc
    # Copy the definition to the python package
    cp impl/capnp/jeff.capnp impl/py/src/jeff/data/jeff.capnp
    # Re-generate rust capnp files
    capnp compile -orust:impl/rs/src --src-prefix=impl impl/capnp/jeff.capnp
    # Re-generate c++ capnp files
    patch -p0 < impl/capnp/cpp_namespace.patch
    capnp compile -oc++:impl/cpp/src --src-prefix=impl impl/capnp/jeff.capnp
    patch -p0 -R < impl/capnp/cpp_namespace.patch
    # Re-encode the test examples
    ./examples/encode_examples.sh
