# Welcome to the *jeff* development guide <!-- omit in toc -->

This guide is intended to help you get started with developing *jeff*.

If you find any errors or omissions in this document, please
[open an issue](https://github.com/unitaryfoundation/jeff/issues/new)!

## #️⃣ Setting up the development environment

You can setup the development environment in two ways:

### The Nix way

This repository defines a Nix flake which will allow you to quickly bootstrap a
development environment on any Linux system, including WSL & Mac OS X. Unlike
manually managing dependencies, Nix will (mostly) hermetically manage all the
dependencies for you. All you **need** to install, ever, is Nix itself.

To setup using nix flakes, you will first have to install
[Nix multi-user](https://nixos.org/download/), if you haven't done so already:

```bash
sh <(curl -L https://nixos.org/nix/install) --daemon
```

You can now trigger `nix develop` from the root of the repository and use the
development shell. You will have to
[enable flakes](https://wiki.nixos.org/wiki/Flakes) if you stop here. However,
installing `direnv` will enable nix development shell drop-in as soon as you
`cd` into the repository. This should be available with your favorite package
manager, e.g.

```bash
sudo apt-get install direnv
```

You will also have to add a `direnv` hook to your shell configuration, e.g.
`~/.bashrc`

```bash
eval "$(direnv hook bash)"
```

Refer to `direnv` install instructions for more help:

- [Installation](https://direnv.net/docs/installation.html)
- [Hook](https://direnv.net/docs/hook.html)

Alternatively, if you already use `nix-darwin`, `home-manager`, etc. you can
enable direnv in your config, e.g.:

```
{
  ...
  outputs = inputs@{ self, nix-darwin, nixpkgs }:
    let
        configuration = { pkgs, ... }: {
            programs.direnv.enable = true;
        }
    ...
}
```

Once you have both nix and `direnv` installed, you will have to `direnv allow`
in the repository root as a one-time step to allow `direnv` to trigger
`nix develop` for you. Nix will now manage the toolchain and dev environment for
you.

> [!NOTE]
>
> Unfortunately, Mac OS X also requires XCode tooling to be installed and
> configured externally. While `darwin.xcode_XX` packages exist, they require
> manual download and provide little to no benefit over managing externally.

### Manual setup

To setup the environment manually you will need:

- Just: https://just.systems/
- Rust `>=1.85.0`: https://www.rust-lang.org/tools/install
- uv `>=1`: https://docs.astral.sh/uv/getting-started/installation
- capnproto `1.1.0`: https://capnproto.org/install.html

Once you have these installed, you can install the required python dependencies
and setup pre-commit hooks with:

```bash
just setup
```

## 🏃 Running the tests

To compile and test the code, run:

```bash
just test
# or, to run only the tests for a specific language
just test-rs
just test-py
```

Run the rust benchmarks with:

```bash
cargo bench
```

Run `just` to see all available commands.

### 💥 API-breaking changes

The package mayor versions follow the versioning of the serialization schema.
Packages with the same major version are guaranteed to be inter-compatible.

#### Rust `semver-checks`

For the rust package we use `cargo semver-checks` to alert you of any
problematic changes that would require a mayor version bump. You can run the
check locally with:

```bash
# Ensure you have cargo-semver-checks installed
cargo install cargo-semver-checks --locked
# Check for breaking changes against the main branch
cargo semver-checks --baseline-rev origin/main
```

These checks are also run on the CI. You will see a warning comment on your PR
if you introduce a breaking change.

## 💅 Coding Style

Code format is enforced via `rustfmt` and `ruff` to ensure a consistent coding
style through the project. The CI will fail if the code is not formatted
correctly.

To format your code, run:

```bash
just format
```

We also use various linters to catch common mistakes and enforce best practices.
To run these, use:

```bash
just check
```

To quickly fix common issues, run:

```bash
just fix
# or, to fix only the rust code or the python code
just fix-rs
just fix-py
```

## 🌐 Contributing to *jeff*

We welcome contributions to *jeff*! Please open
[an issue](https://github.com/unitaryfoundation/jeff/new) or
[pull request](https://github.com/unitaryfoundation/jeff/compare) if you have any questions
or suggestions.

PRs should be made against the `main` branch, and should pass all CI checks
before being merged. This includes using the
[conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) format
for the PR title.

The general format of a contribution title should be:

```
<type>(<scope>)!: <description>
```

Where the scope is optional, and the `!` is only included if this is a semver
breaking change that requires a major version bump.

We accept the following contribution types:

- feat: New features.
- fix: Bug fixes.
- docs: Improvements to the documentation.
- style: Formatting, missing semi colons, etc; no code change.
- refactor: Refactoring code without changing behaviour.
- perf: Code refactoring focused on improving performance.
- test: Adding missing tests, refactoring tests; no production code change.
- ci: CI related changes. These changes are not published in the changelog.
- chore: Updating build tasks, package manager configs, etc. These changes are
  not published in the changelog.
- revert: Reverting previous commits.

## :shipit: Releasing new versions

We use automation to bump the version number and generate changelog entries
based on the
[conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) labels.
Release PRs are created automatically for each package when new changes are
merged into the `main` branch. Once the PR is approved by someone in the
[release team](.github/CODEOWNERS) and is merged, the new package is published
on PyPI or crates.io as appropriate.

The changelog can be manually edited before merging the release PR. Note however
that modifying the diff before other changes are merged will cause the
automation to close the release PR and create a new one to avoid conflicts.

### Rust crate release

Rust releases are managed by `release-plz`. This tool will automatically detect
breaking changes even when they are not marked as such in the commit message,
and bump the version accordingly.

To modify the version being released, update the `Cargo.toml`, CHANGELOG.md, PR
name, and PR description in the release PR with the desired version. You may
also have to update the dates. Rust pre-release versions should be formatted as
`0.1.0-alpha.1` (or `-beta`, or `-rc`).

### Python package release

Python releases are managed by `release-please`. This tool always bumps the
minor version (or the pre-release version if the previous version was a
pre-release).

To override the version getting released, you must merge a PR to `main`
containing `Release-As: 0.1.0` in the description. Python pre-release versions
should be formatted as `0.1.0a1` (or `b1`, `rc1`).

### Patch releases

Sometimes we need to release a patch version to fix a critical bug, but we don't
want to include all the changes that have been merged into the main branch. In
this case, you can create a new branch from the latest release tag and
cherry-pick the commits you want to include in the patch release.

#### Rust patch releases

You can use [`release-plz`](https://release-plz.ieni.dev/) to automatically
generate the changelogs and bump the package versions.

```bash
# If you have cargo-semver-checks installed,
# release-plz will ensure your changes don't break the semver rules.
cargo install cargo-semver-checks --locked
# Analyze the new comments to generate the changelogs / bump the versions
release-plz update
```

Once the branch is ready, create a draft PR so that the release team can review
it.

Now someone from the release team can run `release-plz` on the **unmerged**
branch to create the github releases and publish to crates.io.

```bash
# Make sure you are logged in to `crates.io`
cargo login <your_crates_io_token>
# Get a github token with permissions to create releases
GITHUB_TOKEN=<your_github_token>
# Run release-plz
release-plz release --git-token $GITHUB_TOKEN
```

#### Python patch releases

You will need to modify the version and changelog manually in this case. Check
the existing release PRs for examples on how to do this. Once the branch is
ready, create a draft PR so that the release team can review it.

The wheel building process and publication to PyPI is handled by the CI. Just
create a [github release](https://github.com/unitaryfoundation/jeff/releases/new) from the
**unmerged** branch. The release tag should follow the format used in the
previous releases, e.g. `jeff-py-v0.1.1`.
