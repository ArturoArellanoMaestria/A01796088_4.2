# pylint: disable=invalid-name
# pylint: disable=too-many-instance-attributes,too-many-locals

"""
computeStatistics.py

Compute basic descriptive statistics (mean, median, mode, standard deviation, variance)
from a text file containing one item per line (presumably numbers).

Requirements addressed:
- Run from command line receiving the input file as parameter.
- Compute using basic algorithms (no statistics libraries).
- Handle invalid data: report it and continue processing.
- Print results to screen and write them to "StatisticsResults.txt".
- Record elapsed time.
- PEP 8 compliance.

Note:
Some course materials show a mismatch between "variance" and "SD" formulas.
This implementation computes:
- SD as population standard deviation (divide by N)
- VARIANCE as sample variance (divide by N-1) to match the provided results file.
If you need population variance instead, set USE_SAMPLE_VARIANCE = False.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, getcontext
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Increase precision to better support very large numbers
getcontext().prec = 80

USE_SAMPLE_VARIANCE = True  # True -> divide by (N-1), False -> divide by N


@dataclass
class StatsReport:
    """Container for all values that will be written to the report."""
    input_path: Path
    total_items: int
    valid_items: int
    invalid_items: List[Tuple[int, str]]
    mean_value: Optional[Decimal]
    median_value: Optional[Decimal]
    mode_value: Optional[Decimal]
    sd_value: Optional[Decimal]
    variance_value: Optional[Decimal]
    elapsed_seconds: float
    use_sample_variance: bool


def print_usage() -> None:
    """Print minimal usage instructions."""
    script_name = Path(sys.argv[0]).name
    print(f"Usage: python {script_name} <fileWithData.txt>")


def try_parse_decimal(raw: str) -> Optional[Decimal]:
    """
    Try to parse a string as Decimal.

    Returns:
        Decimal if raw is a valid number, otherwise None.
    """
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return None


def read_numbers(file_path: Path) -> Tuple[List[Decimal], int, List[Tuple[int, str]]]:
    """
    Read items from file_path, line by line.

    Returns:
        values: list of valid numeric values (Decimal)
        total_items: count of non-empty lines (valid + invalid)
        invalid_items: list of (line_number, raw_value) for invalid non-empty lines
    """
    values: List[Decimal] = []
    invalid_items: List[Tuple[int, str]] = []
    total_items = 0

    with file_path.open("r", encoding="utf-8", errors="replace") as file:
        for line_number, line in enumerate(file, start=1):
            raw = line.strip()
            if raw == "":
                continue

            total_items += 1
            number = try_parse_decimal(raw)
            if number is None:
                invalid_items.append((line_number, raw))
                print(f"Invalid data at line {line_number}: '{raw}' (skipped)")
                continue

            values.append(number)

    return values, total_items, invalid_items


def merge_sort(values: List[Decimal]) -> List[Decimal]:
    """Sort a list of Decimals using merge sort (basic algorithm)."""
    if len(values) <= 1:
        return values[:]

    mid = len(values) // 2
    left = merge_sort(values[:mid])
    right = merge_sort(values[mid:])
    return merge(left, right)


def merge(left: List[Decimal], right: List[Decimal]) -> List[Decimal]:
    """Merge two sorted lists."""
    merged: List[Decimal] = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    while i < len(left):
        merged.append(left[i])
        i += 1

    while j < len(right):
        merged.append(right[j])
        j += 1

    return merged


def compute_mean(values: List[Decimal]) -> Decimal:
    """Compute arithmetic mean using a basic loop."""
    total = Decimal(0)
    for v in values:
        total += v
    return total / Decimal(len(values))


def compute_median(sorted_values: List[Decimal]) -> Decimal:
    """Compute median from a sorted list."""
    n = len(sorted_values)
    mid = n // 2
    if n % 2 == 1:
        return sorted_values[mid]
    return (sorted_values[mid - 1] + sorted_values[mid]) / Decimal(2)


def compute_mode(values: List[Decimal]) -> Optional[Decimal]:
    """
    Compute mode. If there are multiple modes, choose the one that appears first
    in the input order (tie-break).

    Returns:
        mode value, or None if no repetition exists.
    """
    counts: Dict[Decimal, int] = {}
    first_index: Dict[Decimal, int] = {}

    for idx, v in enumerate(values):
        counts[v] = counts.get(v, 0) + 1
        if v not in first_index:
            first_index[v] = idx

    max_count = 0
    mode_value: Optional[Decimal] = None
    mode_first_idx = len(values) + 1

    for v, c in counts.items():
        if c > max_count:
            max_count = c
            mode_value = v
            mode_first_idx = first_index[v]
        elif c == max_count and c > 1:
            if first_index[v] < mode_first_idx:
                mode_value = v
                mode_first_idx = first_index[v]

    if max_count <= 1:
        return None
    return mode_value


def sqrt_decimal(value: Decimal) -> Decimal:
    """Compute square root of a non-negative Decimal using Newton-Raphson."""
    if value < 0:
        raise ValueError("Square root is not defined for negative numbers.")
    if value == 0:
        return Decimal(0)

    adjusted = value.adjusted()  # scientific exponent for Decimal
    guess = Decimal(10) ** (adjusted // 2)

    two = Decimal(2)
    for _ in range(80):
        new_guess = (guess + (value / guess)) / two
        if new_guess == guess:
            break
        guess = new_guess

    return guess


def compute_variance(values: List[Decimal], mean_value: Decimal) -> Decimal:
    """
    Compute variance using a basic loop.

    If USE_SAMPLE_VARIANCE is True, divides by (N-1).
    Otherwise divides by N (population variance).
    """
    n = len(values)
    if n == 0:
        return Decimal(0)

    sum_sq = Decimal(0)
    for v in values:
        diff = v - mean_value
        sum_sq += diff * diff

    if USE_SAMPLE_VARIANCE and n > 1:
        return sum_sq / Decimal(n - 1)

    return sum_sq / Decimal(n)


def compute_sd_population(values: List[Decimal], mean_value: Decimal) -> Decimal:
    """
    Compute population standard deviation:
        sqrt( sum((x - mean)^2) / N )
    """
    n = len(values)
    if n == 0:
        return Decimal(0)

    sum_sq = Decimal(0)
    for v in values:
        diff = v - mean_value
        sum_sq += diff * diff

    variance_pop = sum_sq / Decimal(n)
    return sqrt_decimal(variance_pop)


def format_decimal(value: Optional[Decimal], decimals: int = 10) -> str:
    """Format Decimal for readable output, trimming trailing zeros."""
    if value is None:
        return "#N/A"

    quant = Decimal(1).scaleb(-decimals)  # 10^-decimals
    try:
        rounded = value.quantize(quant)
    except InvalidOperation:
        return str(value)

    text = format(rounded, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def choose_output_path() -> Path:
    """
    Write to ../results/StatisticsResults.txt if 'results' folder exists next to script,
    otherwise write to current working directory.
    """
    script_dir = Path(__file__).resolve().parent
    candidate_dir = script_dir.parent / "results"
    if candidate_dir.is_dir():
        return candidate_dir / "StatisticsResults.txt"
    return Path.cwd() / "StatisticsResults.txt"


def build_report(report_data: StatsReport) -> str:
    """Create a human-readable report."""
    lines: List[str] = []
    lines.append("=" * 70)
    lines.append(f"Input file: {report_data.input_path}")
    lines.append(f"COUNT (non-empty items): {report_data.total_items}")
    lines.append(f"VALID numeric items: {report_data.valid_items}")
    lines.append(f"INVALID items: {len(report_data.invalid_items)}")

    if report_data.invalid_items:
        lines.append("Invalid data details (line_number -> raw_value):")
        for line_number, raw in report_data.invalid_items[:25]:
            lines.append(f"  - {line_number} -> '{raw}'")
        if len(report_data.invalid_items) > 25:
            remaining = len(report_data.invalid_items) - 25
            lines.append(f"  ... ({remaining} more)")

    lines.append(f"MEAN: {format_decimal(report_data.mean_value)}")
    lines.append(f"MEDIAN: {format_decimal(report_data.median_value)}")
    lines.append(f"MODE: {format_decimal(report_data.mode_value)}")
    lines.append(f"SD (population): {format_decimal(report_data.sd_value)}")

    if report_data.use_sample_variance:
        lines.append(f"VARIANCE (sample): {format_decimal(report_data.variance_value)}")
    else:
        lines.append(f"VARIANCE (population): {format_decimal(report_data.variance_value)}")

    lines.append(f"Elapsed time (s): {report_data.elapsed_seconds:.6f}")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    """Entry point."""
    if len(sys.argv) != 2:
        print_usage()
        return 1

    input_path = Path(sys.argv[1]).expanduser()

    if not input_path.exists():
        print(f"Error: file not found -> {input_path}")
        return 1

    start_time = time.perf_counter()

    values, total_items, invalid_items = read_numbers(input_path)
    if not values:
        elapsed = time.perf_counter() - start_time
        report_data = StatsReport(
            input_path=input_path,
            total_items=total_items,
            valid_items=0,
            invalid_items=invalid_items,
            mean_value=None,
            median_value=None,
            mode_value=None,
            sd_value=None,
            variance_value=None,
            elapsed_seconds=elapsed,
            use_sample_variance=USE_SAMPLE_VARIANCE,
        )
        report = build_report(report_data)
        print(report)

        output_path = choose_output_path()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("a", encoding="utf-8") as out:
            out.write(report)
            out.write("\n")
        return 0

    sorted_values = merge_sort(values)
    mean_value = compute_mean(values)
    median_value = compute_median(sorted_values)
    mode_value = compute_mode(values)

    sd_value = compute_sd_population(values, mean_value)
    variance_value = compute_variance(values, mean_value)

    elapsed = time.perf_counter() - start_time

    report_data = StatsReport(
        input_path=input_path,
        total_items=total_items,
        valid_items=len(values),
        invalid_items=invalid_items,
        mean_value=mean_value,
        median_value=median_value,
        mode_value=mode_value,
        sd_value=sd_value,
        variance_value=variance_value,
        elapsed_seconds=elapsed,
        use_sample_variance=USE_SAMPLE_VARIANCE,
    )
    report = build_report(report_data)

    print(report)

    output_path = choose_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as out:
        out.write(report)
        out.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
