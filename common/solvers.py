#!/usr/bin/env python3
"""Reference greedy pair-merge coarsener for EST8717 lab 3.

Affinity = current edge weight between two clusters (parallel edges sum).
Tie-break = lexicographic cluster labels (sorted member names joined).
Capacity, if set, forbids a merge whose combined node count exceeds the cap.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_graph(path: Path) -> tuple[list[str], dict[tuple[str, str], int]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    nodes = [str(n) for n in doc["nodes"]]
    weights: dict[tuple[str, str], int] = {}
    for e in doc["edges"]:
        u, v, w = str(e["u"]), str(e["v"]), int(e["w"])
        if u == v:
            continue
        a, b = (u, v) if u < v else (v, u)
        weights[a, b] = weights.get((a, b), 0) + w
    return nodes, weights


def _label(members: list[str]) -> str:
    return "".join(sorted(members))


def cutsize(parts: list[list[str]], weights: dict[tuple[str, str], int]) -> int:
    owner = {n: i for i, part in enumerate(parts) for n in part}
    total = 0
    for (u, v), w in weights.items():
        if owner[u] != owner[v]:
            total += w
    return total


def cluster_affinity(a: list[str], b: list[str], weights: dict[tuple[str, str], int]) -> int:
    s = 0
    for u in a:
        for v in b:
            p, q = (u, v) if u < v else (v, u)
            s += weights.get((p, q), 0)
    return s


def greedy_pair_merge(
    nodes: list[str],
    weights: dict[tuple[str, str], int],
    k: int = 2,
    capacity: int | None = None,
) -> dict:
    parts = [[n] for n in nodes]
    log: list[dict] = []
    log.append(
        {
            "step": 0,
            "event": "singletons",
            "clusters": [_label(p) for p in parts],
            "cutsize": cutsize(parts, weights),
        }
    )

    while len(parts) > k:
        best: tuple[int, str, str, int, int] | None = None
        # rank: highest affinity, then lexicographic (label_i, label_j)
        for i in range(len(parts)):
            for j in range(i + 1, len(parts)):
                if capacity is not None and len(parts[i]) + len(parts[j]) > capacity:
                    continue
                aff = cluster_affinity(parts[i], parts[j], weights)
                if aff <= 0:
                    continue
                li, lj = _label(parts[i]), _label(parts[j])
                if li > lj:
                    li, lj = lj, li
                cand = (-aff, li, lj, i, j)
                if best is None or cand < best:
                    best = cand
        if best is None:
            break
        _neg, _li, _lj, i, j = best
        a, b = parts[i], parts[j]
        aff = cluster_affinity(a, b, weights)
        merged = sorted(a + b)
        keep = [p for t, p in enumerate(parts) if t not in (i, j)]
        parts = keep + [merged]
        parts.sort(key=_label)
        log.append(
            {
                "step": len(log),
                "event": "merge",
                "pair": f"{_label(a)}-{_label(b)}",
                "weight": aff,
                "clusters": [_label(p) for p in parts],
                "cutsize": cutsize(parts, weights),
            }
        )

    return {
        "k": k,
        "capacity": capacity,
        "parts": [_label(p) for p in parts],
        "cutsize": cutsize(parts, weights),
        "log": log,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Greedy pair-merge coarsener")
    ap.add_argument("graph", type=Path)
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--capacity", type=int, default=None)
    args = ap.parse_args()
    nodes, weights = load_graph(args.graph)
    out = greedy_pair_merge(nodes, weights, k=args.k, capacity=args.capacity)
    print(json.dumps(out, indent=2))
    print(f"\nparts={'|'.join(out['parts'])}  cutsize={out['cutsize']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
