#!/usr/bin/env python3
"""Full Lund tree of a jet: every declustering is a node, edges join a
declustering to the two declusterings it gives rise to.

    python3 lund_tree.py  constituents_dir/  out.jsonl

Each node carries (ln kt, ln Delta, ln z), with the same definitions as the
LundCoordinates class:

    Delta = j1.delta_R(j2)          j1 = harder, j2 = softer
    kt    = j2.pt() * Delta
    z     = j2.pt() / (j1.pt() + j2.pt())

STRUCTURE
Node i is the splitting  P -> (j1, j2).  Its children are the splitting of j1
and the splitting of j2, if those subjets split further.  So the tree branches
at every node: following only j1 would give the primary Lund plane, which is
the single chain you had before.  Node 0 is the first declustering of the jet.

The recursion of the JetTree class is unrolled into an explicit stack here,
because a jet at 500 GeV can produce a few hundred declusterings and CPython's
recursion limit is not generous.

OUTPUT  one JSON object per line (JSON Lines), one line per jet:
    {"nodes": [[lnkt, lnDelta, lnz], ...],     # N x 3
     "edges": [[parent, child], ...],          # (N-1) x 2, parent < child
     "depth": [0, 1, 1, 2, ...],               # distance from the root node
     "primary": [1, 1, 0, ...]}                # 1 if on the harder-branch chain

`edges` is directed parent -> child.  For message passing you will usually want
both directions; add the reverse pairs when building the graph rather than
storing them twice.
"""

import json
import math
import os
import sys

EPS = 1e-6
R_JET = 0.8
KTMIN = 1.0        # drop splittings below this kt (0 = keep all)
DELTAMIN = 0.0     # stop descending below this angular scale


def lund_tree(pseudojets, R=R_JET, ktmin=KTMIN, deltamin=DELTAMIN):
    """Recluster with Cambridge/Aachen and walk every declustering."""
    import fastjet as fj

    cs = fj.ClusterSequence(pseudojets, fj.JetDefinition(fj.cambridge_algorithm, R))
    jets = fj.sorted_by_pt(cs.inclusive_jets())
    if not jets:
        return None

    nodes, edges, depth, primary = [], [], [], []
    # stack entries: (pseudojet, parent node index, depth, is on primary chain)
    stack = [(jets[0], -1, 0, True)]

    while stack:
        pj, parent, d, prim = stack.pop()

        j1, j2 = fj.PseudoJet(), fj.PseudoJet()
        if not pj.has_parents(j1, j2):
            continue
        if j2.pt() > j1.pt():
            j1, j2 = j2, j1

        delta = j1.delta_R(j2)
        kt = j2.pt() * delta

        if delta < deltamin:                 # below angular cut: stop this branch
            continue
        if kt < ktmin:                       # below kt cut: skip the node but
            stack.append((j1, parent, d, prim))   # keep following the harder
            continue                              # branch, as JetTree does

        z = j2.pt() / (j1.pt() + j2.pt())
        idx = len(nodes)
        nodes.append([math.log(max(kt, EPS)),
                      math.log(max(delta, EPS)),
                      math.log(max(z, EPS))])
        depth.append(d)
        primary.append(1 if prim else 0)
        if parent >= 0:
            edges.append([parent, idx])

        # harder branch continues the primary chain; softer branch starts a
        # secondary one
        stack.append((j2, idx, d + 1, False))
        stack.append((j1, idx, d + 1, prim))

    return {"nodes": nodes, "edges": edges, "depth": depth, "primary": primary}


# ---------------------------------------------------------------------------
def from_dat(path):
    """Read a px py pz E file (as written by dump_particles.py)."""
    import fastjet as fj
    out = []
    for line in open(path):
        w = line.split()
        if len(w) >= 4:
            out.append(fj.PseudoJet(float(w[0]), float(w[1]),
                                    float(w[2]), float(w[3])))
    return out


def main():
    src, dst = sys.argv[1], sys.argv[2]
    files = (sorted(os.path.join(src, f) for f in os.listdir(src)
                    if f.endswith(".dat")) if os.path.isdir(src) else [src])

    n_ok = n_nodes = 0
    with open(dst, "w") as out:
        for f in files:
            t = lund_tree(from_dat(f))
            if t is None or not t["nodes"]:
                continue
            out.write(json.dumps(t) + "\n")
            n_ok += 1
            n_nodes += len(t["nodes"])
    print(f"{n_ok} jets, {n_nodes} nodes "
          f"({n_nodes / max(n_ok, 1):.1f} per jet) -> {dst}")


if __name__ == "__main__":
    main()
