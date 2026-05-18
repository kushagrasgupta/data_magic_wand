from __future__ import annotations

import csv


def infer_delimiter(text: str, candidates: tuple[str, ...] = (",", "\t", "|", ";")) -> str:
    sample = text[:131_072]
    try:
        return csv.Sniffer().sniff(sample, delimiters="".join(candidates)).delimiter
    except csv.Error:
        lines = [line for line in sample.splitlines() if line.strip()]
        scores: dict[str, float] = {}
        for candidate in candidates:
            counts = [line.count(candidate) for line in lines[:25]]
            if not counts or max(counts) == 0:
                scores[candidate] = -1
                continue
            scores[candidate] = sum(counts) / (1 + len(set(counts)))
        return max(scores, key=lambda candidate: scores[candidate])
