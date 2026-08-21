#!/usr/bin/env python3

"""
Extract constituents of the leading anti-kT R=0.8 jet
from a HepMC3 ASCII file.

HepMC format:
    HepMC::Version 3.02.05

Usage:
    python3 cluster_hepmc3.py input.hepmc output_directory

Example:
    python3 cluster_hepmc3.py qcd.hepmc out_qcd
"""

import os
import sys
import fastjet as fj


# ============================================================
# Configuration
# ============================================================

R = 0.8
MIN_JET_PT = 20.0

# Invisible particles
INVISIBLE = {
    12,    # electron neutrino
    14,    # muon neutrino
    16,    # tau neutrino
}


# ============================================================
# Command-line arguments
# ============================================================

if len(sys.argv) != 3:
    print(
        f"Usage: {sys.argv[0]} input.hepmc output_directory"
    )
    sys.exit(1)

src = sys.argv[1]
outdir = sys.argv[2]


if not os.path.isfile(src):
    print(f"Error: input file does not exist: {src}")
    sys.exit(1)


os.makedirs(outdir, exist_ok=True)


# ============================================================
# FastJet setup
# ============================================================

jetdef = fj.JetDefinition(
    fj.antikt_algorithm,
    R
)


# ============================================================
# Process one event
# ============================================================

def dump(event_number, particles):

    if not particles:
        return False

    # Keep ClusterSequence alive while accessing constituents.
    cluster_sequence = fj.ClusterSequence(
        particles,
        jetdef
    )

    # Cluster jets
    jets = cluster_sequence.inclusive_jets(
        MIN_JET_PT
    )

    # Sort by pT
    jets = fj.sorted_by_pt(jets)

    if not jets:
        return False

    # Leading jet
    leading_jet = jets[0]

    # IMPORTANT:
    # This must be called while cluster_sequence is alive.
    constituents = leading_jet.constituents()

    # Output filename
    output_file = os.path.join(
        outdir,
        f"event_{event_number:06d}.dat"
    )

    # Write constituents
    with open(output_file, "w") as f:

        for c in constituents:

            f.write(
                f"{c.px():.8e} "
                f"{c.py():.8e} "
                f"{c.pz():.8e} "
                f"{c.e():.8e}\n"
            )

    return True


# ============================================================
# Main event loop
# ============================================================

event_number = None
particles = []

processed_events = 0
written_events = 0


print("========================================")
print("HepMC3 → FastJet")
print("========================================")
print(f"Input       : {src}")
print(f"Output      : {outdir}")
print(f"Algorithm   : anti-kT")
print(f"Jet radius  : R = {R}")
print(f"Jet pT cut  : {MIN_JET_PT} GeV")
print("========================================")
print()


with open(src, "r") as infile:

    for line in infile:

        line = line.strip()

        if not line:
            continue


        # ====================================================
        # Event record
        # ====================================================

        if line.startswith("E "):

            # Process previous event
            if event_number is not None:

                processed_events += 1

                if dump(
                    event_number,
                    particles
                ):
                    written_events += 1

                if processed_events % 1000 == 0:

                    print(
                        f"Processed events: "
                        f"{processed_events}"
                    )


            # Start new event
            fields = line.split()

            try:
                event_number = int(fields[1])

            except (IndexError, ValueError):

                event_number = processed_events + 1


            particles = []


        # ====================================================
        # Particle record
        # ====================================================

        elif line.startswith("P "):

            fields = line.split()

            

            if len(fields) < 9:
                continue

            try:

                pdgid = int(fields[2])

                px = float(fields[3])
                py = float(fields[4])
                pz = float(fields[5])
                energy = float(fields[6])

                status = int(fields[8])

            except (ValueError, IndexError):

                continue


            # =================================================
            # Only final-state particles
            # =================================================

            if status != 1:
                continue


            # =================================================
            # Remove invisible particles
            # =================================================

            if abs(pdgid) in INVISIBLE:
                continue


            # =================================================
            # Create FastJet PseudoJet
            # =================================================

            particles.append(
                fj.PseudoJet(
                    px,
                    py,
                    pz,
                    energy
                )
            )


# ============================================================
# Process final event
# ============================================================

if event_number is not None:

    processed_events += 1

    if dump(
        event_number,
        particles
    ):
        written_events += 1


# ============================================================
# Summary
# ============================================================

print()
print("========================================")
print("Finished")
print("========================================")
print(f"Events processed : {processed_events}")
print(f"Events written   : {written_events}")
print(f"Output directory : {outdir}")
print("========================================")
