# pylint: disable=invalid-name
"""
P2 - Converter (Actividad 4.2)

Usage:
    python convertNumbers.py fileWithData.txt

Reads integers from a text file (one item per line), converts each one to:
- Binary (base 2)
- Hexadecimal (base 16)

All conversions are performed using basic algorithms (repeated division),
without using bin(), hex(), format(), or external libraries.

Results are printed on screen and written to "ConversionResults.txt"
inside the P2/results folder (created automatically if missing).

Invalid data is reported in the console and execution continues.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import TextIO


HEX_DIGITS = "0123456789ABCDEF"


def choose_output_path() -> Path:
    """
    Always write to: P2/results/ConvertionResults.txt (relative to this script),
    and create the folder if needed.
    """
    script_dir = Path(__file__).resolve().parent
    results_dir = script_dir.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir / "ConvertionResults.txt"


def to_base_string(value: int, base: int) -> str:
    """Convert a non-negative integer to base 2..16 using repeated division."""
    if value == 0:
        return "0"

    digits: list[str] = []
    current = value

    while current > 0:
        remainder = current % base
        digits.append(HEX_DIGITS[remainder])
        current //= base

    digits.reverse()
    return "".join(digits)


def int_to_binary(value: int) -> str:
    """
    Convert integer to binary.
    For negative numbers, use two's complement with minimum required bits.
    """
    if value >= 0:
        return to_base_string(value, 2)

    abs_val = abs(value)
    bits = abs_val.bit_length() + 1  # minimum bits for two's complement
    unsigned = (1 << bits) + value
    return to_base_string(unsigned, 2)


def int_to_hex(value: int) -> str:
    """
    Convert integer to hexadecimal.
    For negative numbers, use two's complement on 32 bits (8 hex digits).
    """
    if value >= 0:
        return to_base_string(value, 16)

    unsigned = (1 << 32) + value
    hex_str = to_base_string(unsigned, 16)

    while len(hex_str) < 8:
        hex_str = "0" + hex_str

    return hex_str


def safe_parse_int(raw: str) -> int | None:
    """Parse an integer; return None if invalid or empty."""
    text = raw.strip()
    if text == "":
        return None
    try:
        return int(text)
    except ValueError:
        return None


def write_line(stream: TextIO, line: str) -> None:
    """Write a line to a stream."""
    stream.write(line + "\n")


def write_run_header(outfile: TextIO, input_path: str) -> None:
    """Write a header to separate each test case execution."""
    separator = "=" * 70
    write_line(outfile, separator)
    write_line(outfile, f"Input file: {input_path}")
    write_line(outfile, separator)


def _run_conversion(infile: TextIO, outfile: TextIO) -> None:
    """Core loop: read, convert, and write results."""
    header = "ITEM\tDEC\tBIN\tHEX"
    print(header)
    write_line(outfile, header)

    item = 0
    for raw in infile:
        raw_stripped = raw.strip()
        if raw_stripped == "":
            continue

        item += 1
        number = safe_parse_int(raw_stripped)

        if number is None:
            msg = f"ITEM {item}: Invalid data -> {raw_stripped}"
            print(msg)
            write_line(outfile, msg)
            continue

        bin_str = int_to_binary(number)
        hex_str = int_to_hex(number)

        row = f"{item}\t{number}\t{bin_str}\t{hex_str}"
        print(row)
        write_line(outfile, row)


def process_file(input_path: str) -> int:
    """Process input file and append results."""
    output_path = choose_output_path()
    start = time.perf_counter()

    try:
        with open(input_path, "r", encoding="utf-8") as infile:
            file_has_content = output_path.exists() and output_path.stat().st_size > 0

            with open(output_path, "a", encoding="utf-8") as outfile:
                if file_has_content:
                    write_line(outfile, "")

                write_run_header(outfile, input_path)
                _run_conversion(infile, outfile)

                elapsed = time.perf_counter() - start
                elapsed_line = f"Elapsed time (s): {elapsed:.6f}"
                print(elapsed_line)
                write_line(outfile, elapsed_line)

    except FileNotFoundError:
        print(f"ERROR: File not found: {input_path}")
        return 2
    except OSError as exc:
        print(f"ERROR: Cannot open file: {input_path} ({exc})")
        return 2

    print(f"Output appended to: {output_path}")
    return 0


def main() -> int:
    """Entry point."""
    if len(sys.argv) != 2:
        program = os.path.basename(sys.argv[0])
        print("ERROR: Invalid arguments.")
        print(f"Usage: python {program} fileWithData.txt")
        return 2

    return process_file(sys.argv[1])


if __name__ == "__main__":
    raise SystemExit(main())
