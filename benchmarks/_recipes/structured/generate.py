#!/usr/bin/env python3

"""Generate the structured benchmark programs with MQT Core."""

from argparse import ArgumentParser
from fractions import Fraction
from pathlib import Path

from mqt.core.bench import (
    ghz,
    grover,
    modular_multiplier,
    multiplexer,
    qft,
    qft_adder,
    qpe,
    repeat_until_success,
    teleportation,
)
from mqt.core.mlir import OutputFormat, QCProgram, compile_program

OUTPUT_DIRECTORY = Path(__file__).parents[2] / "structured"


def programs(n: int) -> dict[str, QCProgram]:
    """Create the scalable structured benchmarks for n."""
    one = f"{1:0{n}b}"
    return {
        "ghz-linear": ghz.GHZ(
            ghz.Options(qubits=n, topology=ghz.Topology.LINEAR)
        ).generate(),
        "ghz-star": ghz.GHZ(
            ghz.Options(qubits=n, topology=ghz.Topology.STAR)
        ).generate(),
        "grover": grover.Grover(
            grover.Options(marked_bitstring="1" * (n - 1))
        ).generate(),
        "qft": qft.QFT(
            qft.Options(
                qubits=n,
                period_exponent=n,
                method=qft.Method.STANDARD,
            )
        ).generate(),
        "qpe": qpe.QPE(
            qpe.Options(
                precision=n - 1,
                phase=Fraction(3, 16),
                method=qpe.Method.STANDARD,
            )
        ).generate(),
        "iqft": qft.QFT(
            qft.Options(
                qubits=n,
                period_exponent=n,
                method=qft.Method.SEMICLASSICAL,
            )
        ).generate(),
        "iqpe": qpe.QPE(
            qpe.Options(
                precision=n,
                phase=Fraction(3, 16),
                method=qpe.Method.ITERATIVE,
            )
        ).generate(),
        "multiplexer": multiplexer.Multiplexer(
            multiplexer.Options(qubits=n)
        ).generate(),
        "qft-adder-quantum": qft_adder.QFTAdder(
            qft_adder.Options(
                addend="+" * n,
                accumulator=one,
                method=qft_adder.Method.REGISTER,
                overflow=qft_adder.Overflow.WRAP,
            )
        ).generate(),
        "qft-adder-classical": qft_adder.QFTAdder(
            qft_adder.Options(
                addend=f"{5:0{n}b}",
                accumulator=one,
                method=qft_adder.Method.CONSTANT,
                overflow=qft_adder.Overflow.WRAP,
            )
        ).generate(),
        "controlled-multiplication-modulo-n": modular_multiplier.ModularMultiplier(
            modular_multiplier.Options(
                multiplier=f"{3:0{n}b}",
                modulus=f"{(1 << (n - 1)) + 1:0{n}b}",
                multiplicand="+" * n,
                control="+",
            )
        ).generate(),
        "repeat-until-success": repeat_until_success.RepeatUntilSuccess(
            repeat_until_success.Options(data_qubits=n)
        ).generate(),
    }


def write_program(slug: str, program: QCProgram, filename: str) -> None:
    """Write one QC program as jeff."""
    directory = OUTPUT_DIRECTORY / slug
    directory.mkdir(parents=True, exist_ok=True)
    compile_program(program, output=OutputFormat.JEFF).write(directory / filename)


def main() -> None:
    """Generate the requested values of n."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("n", metavar="N", nargs="*", type=int, default=[3, 5, 7])
    args = parser.parse_args()
    if any(n < 3 for n in args.n):
        parser.error("N must be at least 3")

    for n in args.n:
        for slug, program in programs(n).items():
            directory = OUTPUT_DIRECTORY / slug
            write_program(slug, program, f"{slug}_{n}.jeff")
            if n == 3:
                (directory / f"{slug}.qc.mlir").write_text(program.ir, encoding="utf-8")

    program = teleportation.Teleportation().generate()
    directory = OUTPUT_DIRECTORY / "teleportation"
    write_program("teleportation", program, "teleportation.jeff")
    (directory / "teleportation.qc.mlir").write_text(program.ir, encoding="utf-8")


if __name__ == "__main__":
    main()
