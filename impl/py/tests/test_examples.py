"""Tests validating the files in the repo's `examples` directory."""

import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent
notebook_files = list((REPO_ROOT / "examples").glob("**/*.ipynb"))

print(notebook_files)


@pytest.mark.parametrize("notebook", notebook_files)
def test_example_notebooks(nb_regression, notebook: Path):
    print("Notebook:", notebook)
    nb_regression.diff_ignore += (
        "/metadata/language_info/version",
        "/cells/*/outputs/*/data/image/png",
        "/cells/*/execution_count",
    )
    nb_regression.check(notebook)
