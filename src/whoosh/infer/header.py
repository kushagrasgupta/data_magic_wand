from __future__ import annotations

import csv


def has_header(text: str) -> bool:
    try:
        return csv.Sniffer().has_header(text[:131_072])
    except csv.Error:
        first = next((line for line in text.splitlines() if line.strip()), "")
        cells = [cell.strip() for cell in first.split(",")]
        return bool(cells) and all(cell and not cell.isnumeric() for cell in cells)
