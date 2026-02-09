# pylint: disable=invalid-name
# pylint: disable=too-many-instance-attributes,too-many-locals

"""
P3 - Count Words (Actividad 4.2)

Usage:
    python wordCount.py fileWithData.txt

Reads words from a text file (words are presumably separated by whitespace),
counts distinct valid words and their frequency, prints results to the screen,
and appends them to "WordCountResults.txt" inside the P3/results folder.

All computation is performed using basic algorithms (loops and manual parsing),
without using split(), Counter, sorted(), or specialized libraries.

Invalid tokens are reported in the console and execution continues.
At the end of each run (each TC), totals are printed and written to the results
file, and the elapsed time is included in both outputs.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Dict, Generator, List, TextIO, Tuple


RESULTS_FILENAME = "WordCountResults.txt"
SEPARATOR = "=" * 70
CHUNK_SIZE = 4096


def choose_output_path() -> Path:
    """
    Always write to: P3/results/WordCountResults.txt (relative to this script),
    and create the folder if needed.
    """
    script_dir = Path(__file__).resolve().parent  # .../P3/source
    results_dir = script_dir.parent / "results"   # .../P3/results
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir / RESULTS_FILENAME


def write_line(stream: TextIO, line: str) -> None:
    """Write one line to a text stream."""
    stream.write(line + "\n")


def echo(outfile: TextIO, line: str) -> None:
    """Print to console and write to output file."""
    print(line)
    write_line(outfile, line)


def write_run_header(outfile: TextIO, input_path: str) -> None:
    """Write a header so each run is clearly separated in the results file."""
    write_line(outfile, SEPARATOR)
    write_line(outfile, f"Input file: {input_path}")
    write_line(outfile, SEPARATOR)


def iter_tokens(stream: TextIO) -> Generator[str, None, None]:
    """
    Yield raw tokens separated by any whitespace, using manual parsing.
    This avoids using split() and supports large files efficiently.
    """
    buffer: List[str] = []

    while True:
        chunk = stream.read(CHUNK_SIZE)
        if chunk == "":
            break

        for ch in chunk:
            if ch.isspace():
                if buffer:
                    yield "".join(buffer)
                    buffer = []
            else:
                buffer.append(ch)

    if buffer:
        yield "".join(buffer)


def normalize_word(token: str) -> Tuple[bool, str]:
    """
    Normalize a token to a valid word.
    A valid word contains only alphabetic characters.
    Returns (is_valid, normalized_word).
    """
    if token == "":
        return False, ""

    for ch in token:
        if not ch.isalpha():
            return False, token

    return True, token.lower()


def insertion_sort_by_count_desc(items: List[Tuple[str, int]]) -> None:
    """
    Sort (word, count) pairs in-place by:
      1) count descending (higher first)
      2) word ascending (A..Z) as tie-breaker
    Implemented to avoid using sorted() or list.sort().
    """
    index = 1
    while index < len(items):
        key_word, key_count = items[index]
        position = index - 1

        while position >= 0:
            cur_word, cur_count = items[position]
            should_move = (cur_count < key_count) or (
                cur_count == key_count and cur_word > key_word
            )
            if not should_move:
                break
            items[position + 1] = items[position]
            position -= 1

        items[position + 1] = (key_word, key_count)
        index += 1


def build_items_from_frequencies(
    frequencies: Dict[str, int],
) -> List[Tuple[str, int]]:
    """Build a list of (word, count) pairs from the frequency dictionary."""
    items: List[Tuple[str, int]] = []
    for word, count in frequencies.items():
        items.append((word, count))
    return items


def count_frequencies(
    infile: TextIO,
    outfile: TextIO,
) -> Tuple[Dict[str, int], int, int, int]:
    """
    Count word frequencies from infile.
    Returns: (frequencies, total_tokens, valid_words, invalid_tokens).
    Invalid tokens are reported to console and written to output.
    """
    frequencies: Dict[str, int] = {}
    total_tokens = 0
    valid_words = 0
    invalid_tokens = 0

    for token in iter_tokens(infile):
        total_tokens += 1
        is_valid, word = normalize_word(token)

        if not is_valid:
            invalid_tokens += 1
            echo(outfile, f"Invalid token ignored: {token}")
            continue

        valid_words += 1
        if word in frequencies:
            frequencies[word] += 1
        else:
            frequencies[word] = 1

    return frequencies, total_tokens, valid_words, invalid_tokens


def write_frequency_table(
    outfile: TextIO,
    items: List[Tuple[str, int]],
) -> None:
    """Write and print the frequency table."""
    echo(outfile, "WORD\tCOUNT")
    for word, count in items:
        echo(outfile, f"{word}\t{count}")


def write_summary(outfile: TextIO, summary: Dict[str, object]) -> None:
    """Write and print run totals and elapsed time (grouped in one object)."""
    echo(outfile, SEPARATOR)
    echo(outfile, f"TOTAL_TOKENS\t{summary['total_tokens']}")
    echo(outfile, f"VALID_WORDS\t{summary['valid_words']}")
    echo(outfile, f"INVALID_TOKENS\t{summary['invalid_tokens']}")
    echo(outfile, f"DISTINCT_WORDS\t{summary['distinct_words']}")
    echo(outfile, f"Elapsed time (s): {summary['elapsed_seconds']:.6f}")


def append_blank_line_if_needed(output_path: Path, outfile: TextIO) -> None:
    """Add a blank line between runs if the results file already has content."""
    if output_path.exists() and output_path.stat().st_size > 0:
        write_line(outfile, "")


def process_file(input_path: str) -> int:
    """Process input file and append results to P3/results/WordCountResults.txt."""
    output_path = choose_output_path()
    start = time.perf_counter()

    try:
        with open(input_path, "r", encoding="utf-8") as infile:
            with open(output_path, "a", encoding="utf-8") as outfile:
                append_blank_line_if_needed(output_path, outfile)
                write_run_header(outfile, input_path)

                frequencies, total_tokens, valid_words, invalid_tokens = (
                    count_frequencies(infile, outfile)
                )

                items = build_items_from_frequencies(frequencies)
                insertion_sort_by_count_desc(items)
                write_frequency_table(outfile, items)

                elapsed = time.perf_counter() - start
                summary = {
                    "total_tokens": total_tokens,
                    "valid_words": valid_words,
                    "invalid_tokens": invalid_tokens,
                    "distinct_words": len(frequencies),
                    "elapsed_seconds": elapsed,
                }
                write_summary(outfile, summary)

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
