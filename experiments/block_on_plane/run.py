#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

# Allow direct execution via:
#   python3 experiments/block_on_plane/run.py
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.common.io_utils import load_config, make_run_dir, write_config_copy, write_signals, write_summary


def friction_force(v: float, applied: float, normal: float, mu_s: float, mu_d: float, v_eps: float = 1e-9) -> float:
    static_limit = mu_s * normal
    if abs(v) < v_eps and abs(applied) <= static_limit:
        return -applied
    direction = math.copysign(1.0, v) if abs(v) >= v_eps else math.copysign(1.0, applied)
    return -mu_d * normal * direction


def main() -> int:
    parser = argparse.ArgumentParser(description="Headless block-on-plane friction experiment")
    parser.add_argument("--config", type=Path, default=Path("experiments/block_on_plane/config.yaml"))
    parser.add_argument("--steps", type=int, default=None, help="Override number of steps")
    args = parser.parse_args()

    repo_root = REPO_ROOT
    cfg = load_config(args.config)

    model = cfg["model"]
    run = cfg["run"]
    block = cfg["block"]
    contact = cfg["contact"]
    force_cmd = float(cfg["inputs"]["applied_force_n"])

    dt = float(run["dt"])
    steps = int(args.steps if args.steps is not None else run["steps"])
    mass = float(block["mass"])
    gravity = float(contact["gravity"])
    mu_s = float(contact["mu_static"])
    mu_d = float(contact["mu_dynamic"])

    x = float(block["x0"])
    v = float(block["v0"])
    normal = mass * gravity

    rows = []
    friction_work = 0.0

    for k in range(steps):
        t = k * dt
        ff = friction_force(v=v, applied=force_cmd, normal=normal, mu_s=mu_s, mu_d=mu_d)
        a = (force_cmd + ff) / mass
        v_next = v + a * dt
        x_next = x + v_next * dt

        friction_work += abs(ff * v_next) * dt
        energy = 0.5 * mass * (v_next**2)

        rows.append(
            {
                "time": t,
                "block_pos": x_next,
                "block_vel": v_next,
                "normal_force": normal,
                "friction_force": ff,
                "applied_force": force_cmd,
                "slip_velocity": v_next,
                "mechanical_energy": energy,
            }
        )

        x, v = x_next, v_next

    run_dir = make_run_dir(repo_root, model["name"])
    fields = cfg["logging"]["signals"]
    write_signals(rows, run_dir / "signals.csv", fields)
    write_summary(
        {
            "experiment": model["name"],
            "dt": dt,
            "steps": steps,
            "final_pos": x,
            "final_vel": v,
            "normal_force": normal,
            "mu_static": mu_s,
            "mu_dynamic": mu_d,
            "applied_force_n": force_cmd,
            "friction_work_proxy": friction_work,
        },
        run_dir / "summary.json",
    )
    write_config_copy(cfg, run_dir / "config_used.yaml")

    print(f"Run complete: {run_dir}")
    print(f"Final state: x={x:.6f} m, v={v:.6f} m/s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
