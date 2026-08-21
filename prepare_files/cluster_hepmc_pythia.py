#!/usr/bin/env python3

"""
Cluster HepMC events with FastJet and save the constituents
of the leading anti-kT R=0.8 jet.

Usage
-----
python3 cluster_hepmc.py input.hepmc output_directory

Example
-------
python3 cluster_hepmc.py qcd_pythia_dijet.hepmc out_pythia
python3 cluster_hepmc.py herwig_qcd_dijet.hepmc out_herwig
"""

import os
import sys
import fastjet as fj


# ============================================================
# Configuration
# ============================================================

R = 0.8
MIN_JET_PT = 20.0

# Neutrinos
INVISIBLE = {
    12,    # nu_e
    14,    # nu_mu
    16,    # nu_tau
}


# ============================================================
# Command-line arguments
# ============================================================

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} input.hepmc output_directory")
    sys.exit(1)

src = sys.argv[1]
outdir = sys.argv[2]

if not os.path.isfile(src):
    print(f"Error: input file does not exist: {src}")
    sys.exit(1)

os.makedirs(outdir, exist_ok=True)


# ============================================================
# FastJet
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



    cluster_sequence = fj.ClusterSequence(
        particles,
        jetdef
    )

    jets = cluster_sequence.inclusive_jets(
        MIN_JET_PT
    )

    jets = fj.sorted_by_pt(jets)

    if not jets:
        return False

    # Leading jet
    leading_jet = jets[0]

    # Must be called while cluster_sequence is alive
    constituents = leading_jet.constituents()

    output_file = os.path.join(
        outdir,
        f"event_{event_number:06d}.dat"
    )

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
# Read HepMC
# ============================================================

event_number = None
particles = []

processed_events = 0
written_events = 0


print(f"Input : {src}")
print(f"Output: {outdir}")
print(f"Jet   : anti-kT R = {R}")
print(f"pT    : > {MIN_JET_PT} GeV")
print()


with open(src, "r") as infile:

    for line in infile:

        line = line.strip()

        if not line:
            continue


        # ====================================================
        # Event
        # ====================================================

        if line.startswith("E "):

            # Finish previous event
            if event_number is not None:

                processed_events += 1

                if dump(event_number, particles):
                    written_events += 1

                if processed_events % 100 == 0:
                    print(
                        f"Processed events: "
                        f"{processed_events}"
                    )

            fields = line.split()

            try:
                event_number = int(fields[1])
            except (IndexError, ValueError):
                event_number = processed_events + 1

            particles = []


        # ====================================================
        # Particle
        # ====================================================

        elif line.startswith("P "):

            fields = line.split()

            if len(fields) < 10:
                continue

            try:

                pdgid = int(fields[3])

                px = float(fields[4])
                py = float(fields[5])
                pz = float(fields[6])
                energy = float(fields[7])

                status = int(fields[9])

            except (ValueError, IndexError):

                continue


            # =================================================
            # Final-state particles only
            # =================================================

            if status != 1:
                continue


            # =================================================
            # Remove neutrinos
            # =================================================

            if abs(pdgid) in INVISIBLE:
                continue


            # =================================================
            # FastJet particle
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

    if dump(event_number, particles):
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
