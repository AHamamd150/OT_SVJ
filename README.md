# OT Lund-Plane Pipeline

Installation and run guide — removing event-generator dependence from Lund-plane analysis of semi-visible jets (SVJs) using Optimal Transport (OT).

## Overview

This pipeline removes event-generator effects from Lund-plane analysis of SVJs by comparing Pythia and Herwig outputs using Optimal Transport. Event generation is split between two people: Hammad generates the Herwig samples, and Christiane generates the Pythia samples.

The pipeline has four stages:

1. Install the software environment.
2. Generate events with Pythia and Herwig.
3. Cluster the raw output into `.dat` files.
4. Build Lund trees / images from those `.dat` files for plotting.

Each stage is covered in its own section below.

## Table of Contents

- [1. Installation](#1-installation)
- [2. Working Directory & Activating the Environment](#2-working-directory--activating-the-environment)
- [3. How to Run: Generating Events](#3-how-to-run-generating-events)
- [4. Clustering HepMC Output into .dat Files](#4-clustering-hepmc-output-into-dat-files)
- [5. Create Lund Trees](#5-create-lund-trees)
- [6. Plotting](#6-plotting)
- [7. Full Workflow (Summary)](#7-full-workflow-summary)

## 1. Installation

### 1.1 Create the conda environment

Create a dedicated conda environment named `OT` with the compilers and build tools needed to build Herwig from source:

```bash
conda create -n OT -c conda-forge \
    gcc_linux-64=12 gxx_linux-64=12 gfortran_linux-64=12 \
    make autoconf libtool automake pkg-config zlib python=3.11
```

Then activate it before continuing:

```bash
conda activate OT
```

### 1.2 Get the bootstrap files

Two files are needed to build Herwig with its own LHAPDF: `OT-LHAPDF.py` and `herwig-bootstrap`. Both are available on the external hard disk.

### 1.3 Build Herwig

Run the bootstrap script to build Herwig, skipping the optional add-ons that are not needed for this pipeline:

```bash
./herwig-bootstrap -j $(nproc) \
    --without-pythia --without-evtgen --without-rivet --without-yoda \
    --without-madgraph --without-njet --without-vbfnlo --without-gosam \
    --without-openloops --without-hjets \
    herwig
```

> This builds Herwig itself, but not Pythia — Pythia 8 is installed/compiled separately (see [3.2](#32-pythia-8)).

## 2. Working Directory & Activating the Environment

All work for this pipeline happens under the following directory on host `pmu4`:

```
pmu4:/data1/Hammad/OT
```

Every time you start a new session, activate the Herwig environment from inside this directory before doing anything else:

```bash
source herwig/bin/activate
```

> **Important:** This must be done first — it runs Herwig using the OT conda environment built in [Section 1](#1-installation). Nothing below will work correctly until this is sourced.

## 3. How to Run: Generating Events

### 3.1 Herwig

1. Prepare the input file `qcd.in`.
2. Let Herwig read the input file. This creates a `.run` file:

   ```bash
   Herwig read qcd.in
   ```

3. Run the generated `.run` file:

   ```bash
   Herwig run QCD.run -N 30000 -s 1234
   ```

   `-N` sets the number of events (30000 above) and `-s` sets the random seed (1234 above).

   > **Note:** The original handwritten notes included one or two additional flags after `-s 1234` that were not fully legible. If your run needs a specific thread count or debug flag, check `Herwig run --help` and add it here.

### 3.2 Pythia 8

1. To get HepMC output, use the `main144` example that ships with Pythia 8. From the Pythia examples directory, compile it:

   ```bash
   make main144
   ```

2. Run `main144` from that same examples directory:

   ```bash
   ./main144 -c qcd_Pythia.cmnd -o qcd_PythiaOutput -n 50000 -s 1234
   ```

   `-c` is the Pythia command/settings file, `-o` is the output file name prefix, `-n` is the number of events, and `-s` is the random seed.

## 4. Clustering HepMC Output into .dat Files

Once the HepMC files exist for both generators, cluster them into `.dat` files. Run this from the `Prepare_files` directory:

**Pythia:**

```bash
python cluster_hepmc_Pythia.py <input_hepmc_dir> <output_dir>
```

**Herwig:**

```bash
python cluster_hepmc_herwig.py <input_hepmc_dir> <output_dir>
```

`<input_hepmc_dir>` is the directory containing the HepMC files produced in [Section 3](#3-how-to-run-generating-events), and `<output_dir>` is where the resulting `.dat` files are written.

## 5. Create Lund Trees

Once the `.dat` files have been produced from the clustering step above, they can be used to generate the Lund trees for both Pythia and Herwig. The code for this step lives in the `create_lund` directory and is run as follows.

**Pythia:**

```bash
python3 lund_tree.py <pythia_directory>/ output_pythia.jsonl
```

where `<pythia_directory>/` is the directory containing the Pythia `.dat` files, and `output_pythia.jsonl` is the resulting Lund-tree file.

**Herwig:**

```bash
python3 lund_tree.py <herwig_directory>/ output_herwig.jsonl
```

where `<herwig_directory>/` is the directory containing the Herwig `.dat` files, and `output_herwig.jsonl` is the resulting Lund-tree file.

## 6. Plotting

Plotting of the Lund images is done in the parent directory, in a notebook called `Plot.ipynb`.

## 7. Full Workflow (Summary)

1. Activate the environment: `source herwig/bin/activate` from `pmu4:/data1/Hammad/OT` ([Section 2](#2-working-directory--activating-the-environment)).
2. Generate HepMC files with Pythia and Herwig ([Section 3](#3-how-to-run-generating-events)).
3. Cluster the HepMC files into `.dat` files from the `Prepare_files` directory ([Section 4](#4-clustering-hepmc-output-into-dat-files)).
4. Create the Lund trees from the `.dat` files using `create_lund/lund_tree.py` ([Section 5](#5-create-lund-trees)).
5. Plot the Lund images using `Plot.ipynb` in the parent directory ([Section 6](#6-plotting)).
