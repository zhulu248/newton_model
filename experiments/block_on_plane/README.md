# Block on Plane Isaac Sim Demo

Minimal lab-screen demo: one ground plane and one dynamic block in USD.

## Generate USD (deterministic)
From repo root:

```bash
python3 tools/make_block_on_plane_usd.py --headless
```

This writes:
- `assets/usd/block_on_plane/block_on_plane.usd`

## Open in Isaac Sim GUI
Option 1 (recommended):
1. Launch Isaac Sim GUI.
2. `File > Open...`
3. Select `assets/usd/block_on_plane/block_on_plane.usd`.

Option 2 (script-driven GUI sim run):

```bash
python3 tools/run_block_on_plane_sim.py --gui --seconds 3
```

## Run simulation script (headless)

```bash
python3 tools/run_block_on_plane_sim.py --seconds 3
```

Outputs:
- `results/block_on_plane/<timestamp>/signals.csv`
- `results/block_on_plane/<timestamp>/summary.json`
