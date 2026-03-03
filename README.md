# Newton Open Model Lab

Simulation-only sandbox for small, reproducible mechanism experiments (contact/friction first), with script-first headless runs.

## Layout
- `experiments/`: self-contained experiment folders (config, runner, expected behavior)
- `assets/`: geometry/asset placeholders
- `scripts/common/`: shared config + logging helpers
- `scripts/imported/`: utilities imported from existing source repos
- `docs/`: conventions and checklists
- `results/`: generated run outputs (git-ignored)

## First experiment
Run the block-on-plane friction experiment:

```bash
python3 experiments/block_on_plane/run.py --config experiments/block_on_plane/config.yaml
```

It writes:
- `results/block_on_plane/<timestamp>/signals.csv`
- `results/block_on_plane/<timestamp>/summary.json`
- `results/block_on_plane/<timestamp>/config_used.yaml`
