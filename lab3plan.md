# Lab 3 plan (draft) — greedy pair merge

**Module:** `learn_clustering` · 03 greedy pair merge  
**Starter graph:** [`examples/tiny_graph.json`](examples/tiny_graph.json)  
**Reference solver:** [`common/solvers.py`](common/solvers.py)  
**Slides:** [`slides/greedy-pair-merge.html`](slides/greedy-pair-merge.html)  
**Golden (unconstrained, K=2):** `ABC|DE`, cutsize `3`

This is a working draft for a 90-minute CAD coarsening lab. The engine is agglomerative clustering on a weighted undirected netlist: merge the current heaviest legal pair until you hit target `K`.

---

## 1. Why this engine

Greedy pair merge is the simplest coarsening step that still behaves like VLSI CAD:

- Heavy nets should stay **inside** a cluster (they stop contributing to cut).
- Weak bridges can stay **cut**.
- There is **no backtracking**. A locally best merge can lock in a worse global cut.
- Optional **capacity** (cluster size cap) is how floorplanning / bin constraints show up in the coarsener.

Students should leave able to run the walkthrough by hand, re-implement contraction with a **deterministic tie-break**, and explain why `capacity=2` diverges from the unconstrained golden.

---

## 2. Key content (compiled)

### 2.1 Input

Undirected weighted graph. Parallel edges **sum**. Self-loops are ignored.

`tiny_graph` (five cells):

| Edge | Weight |
| --- | ---: |
| A–B | 5 |
| B–C | 4 |
| C–D | 2 |
| D–E | 5 |
| A–C | 1 |
| C–E | 1 |
| **All separate cutsize** | **18** |

### 2.2 Ranking rule

At every step, among **current clusters**:

1. **Illegal** if `capacity` is set and `|A| + |B| > capacity`.
2. **Skip** if affinity `≤ 0` (no edge between the clusters).
3. **Affinity** = sum of original edge weights with one endpoint in A and one in B (parallel connections add).
4. **Pick** maximum affinity.
5. **Tie-break** = lexicographic pair of cluster labels. A label is the sorted member names concatenated (`AB`, `ABC`, …). Compare the two labels in sorted order so `AB-C` beats `D-E` when both affinities are 5.

After a merge, rebuild supernode edges (sum parallels) and **sort remaining clusters by label** so later ties stay stable.

### 2.3 Stop

Stop when `|clusters| ≤ K`, or when no legal positive-affinity pair remains (capacity can strand you above `K`).

### 2.4 Cutsize

Sum of weights whose endpoints sit in **different** clusters. Contracting a pair of affinity `w` drops cutsize by exactly `w`.

### 2.5 Unconstrained walkthrough (K=2)

| Step | Event | Affinity | Clusters | Cutsize |
| ---: | --- | ---: | --- | ---: |
| 0 | singletons | — | A \| B \| C \| D \| E | 18 |
| 1 | merge A–B | 5 | AB \| C \| D \| E | 13 |
| 2 | merge AB–C | 5 | ABC \| D \| E | 8 |
| 3 | merge D–E | 5 | ABC \| DE | 3 |

**Why step 2 is AB–C, not D–E:** both pairs have affinity 5. Labels `AB`/`C` vs `D`/`E`; `AB < D`, so AB–C wins. The slide caption “alphabetical order merges C next” is this tie-break, not “C is a better community.”

Final cut = C–D (2) + C–E (1) = **3**. Golden parts string: `ABC|DE`.

### 2.6 Capacity = 2 (same K=2)

Size-3 `{A,B,C}` is illegal. After A–B, the next legal 5-edge is D–E. Then no pair both fits in the cap **and** has a positive edge (C cannot join AB or DE). The coarsener **stops at three clusters**.

| Step | Event | Clusters | Cutsize |
| ---: | --- | --- | ---: |
| 0 | singletons | A \| B \| C \| D \| E | 18 |
| 1 | merge A–B | AB \| C \| D \| E | 13 |
| 2 | merge D–E | AB \| C \| DE | 8 |
| stop | no legal pair | **AB \| C \| DE** | **8** |

### 2.7 Other useful presets

| Preset | Result | Cutsize | Teaching point |
| --- | --- | ---: | --- |
| `--k 2` | `ABC\|DE` | 3 | unconstrained golden |
| `--k 3` | `ABC\|D\|E` | 8 | stop before D–E |
| `--k 2 --capacity 2` | `AB\|C\|DE` | 8 | cap blocks the golden community |
| `--k 2 --capacity 3` | `ABC\|DE` | 3 | cap equal to the largest cluster still allows the golden path |

### 2.8 Pitfalls (completed from truncated slides)

- **Myopia.** Heaviest-first is not min-cut. A great first merge can strand a worse global cut; later labs repair seeds with refinement (FM / KL), not by undoing greedy.
- **Illegal merges.** Always test `|A|+|B|` against capacity **before** ranking. Do not merge then reject.
- **Stale affinities.** After contraction, supernode edges must **sum** all original cut edges to the new cluster. Wrong updates look fine until goldens fail.
- **Non-deterministic ties.** Without the label tie-break, AB–C vs D–E is a coin flip and `tiny_graph` goldens flake.
- **Stopping above K.** Capacity can leave isolated cells. Report actual `|parts|` and cutsize; do not invent a merge to force K.

---

## 3. Session flow (90 min)

| Min | Block | What happens |
| ---: | --- | --- |
| 0–10 | Hook | Title + ranking rules. One board sentence: *protect heavy nets, cut weak bridges, never undo.* |
| 10–25 | Walkthrough | Slides 4–8 on `tiny_graph`. Students predict the AB–C / D–E tie **before** revealing step 2. |
| 25–35 | Capacity fork | Same graph, cap 2. Contrast `ABC\|DE` cut 3 vs `AB\|C\|DE` cut 8. |
| 35–55 | Browser track | Load starter, run K and capacity presets, work the three challenges below. |
| 55–80 | Implement track | Run reference solver, then re-implement contraction + tie-break. Match goldens. |
| 80–90 | Checklist + quiz | Exit ticket. Collect cutsize logs. |

---

## 4. Browser lab track

In the browser lab:

1. Load the `tiny_graph` starter.
2. Run unconstrained greedy to **K=2**. Confirm `ABC|DE` / cut 3.
3. Toggle presets: **K=3**, **capacity=2**, **capacity=3**.
4. Work the challenges:

**C1.** After merging A–B, two pairs sit at weight 5. Which merge fires, and which rule decides it?  
*Answer: AB–C, lexicographic labels.*

**C2.** Set `capacity=2` and `K=2`. Why does the run stop with three clusters?  
*Answer: `{A,B,C}` is illegal; C has no legal partner left.*

**C3.** Name the two cut edges in the unconstrained golden.  
*Answer: C–D (2) and C–E (1).*

---

## 5. Implement track

From the lab tree (directory that contains `examples/`):

```bash
pwd
ls examples
export PYTHONPATH=../common
python3 ../common/solvers.py examples/tiny_graph.json --k 2
python3 ../common/solvers.py examples/tiny_graph.json --k 3
python3 ../common/solvers.py examples/tiny_graph.json --k 2 --capacity 2
```

From this repo root:

```bash
python3 common/solvers.py examples/tiny_graph.json --k 2
```

Expected last line for the golden:

```text
parts=ABC|DE  cutsize=3
```

Students then re-implement:

- cluster affinity (sum of crossing weights),
- capacity filter,
- lexicographic tie-break on labels,
- contraction + cutsize logging.

Keep the tie-break **identical** to the reference so golden tests stay **reproducible**.

---

## 6. Your turn / exit ticket

- [ ] Implement greedy pair merge end to end.
- [ ] Hit a chosen `K` and record cutsize at every merge.
- [ ] Match unconstrained golden `ABC|DE` / 3.
- [ ] Report the `capacity=2` stranded result `AB|C|DE` / 8.
- [ ] Complete the checklist and quiz.

### Quiz (5 logic items from the PDF walkthrough)

Same widget as the live lab (check each answer, then score). Questions follow `tiny_graph` on the slides, not the generic “which algorithm / Track A” items.

1. Singletons: all edges still cut. Cutsize? **18**.
2. A–B and D–E both weigh 5. First merge? **A–B**, max affinity then lexicographic labels (`A < D`).
3. After A–B, affinity AB–C is **5** (`AC 1 + BC 4`), tying D–E. Next merge? **AB–C** (labels `AB`/`C` beat `D`/`E`).
4. Golden `ABC|DE`. Remaining cut edges? **C–D (2) and C–E (1)**; cutsize **3**.
5. `K=2` and `capacity=2` forbids `{A,B,C}`. Result? **`AB|C|DE`, cut 8**, stopped above K — no backtracking.

---

## 7. Files in this draft

| Path | Role |
| --- | --- |
| `examples/tiny_graph.json` | Five-node netlist used on every walkthrough slide |
| `common/solvers.py` | Reference coarsener (`--k`, `--capacity`) |
| `slides/greedy-pair-merge.html` | Completed deck (truncated Impress bullets finished; algorithm / capacity / goldens added) |

Open the slides in a browser. Arrow keys or click **Prev** / **Next**.
