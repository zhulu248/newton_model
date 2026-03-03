#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _candidate_python_sh() -> list[Path]:
    candidates: list[Path] = []

    env_path = os.environ.get("ISAACSIM_PATH")
    if env_path:
        candidates.append(Path(env_path) / "python.sh")
    env_py = os.environ.get("ISAACSIM_PYTHON")
    if env_py:
        candidates.append(Path(env_py))

    repo_root = Path(__file__).resolve().parents[1]
    for parent in [repo_root] + list(repo_root.parents):
        candidates.append(parent / "_isaac_sim" / "python.sh")
        candidates.append(parent / "isaac-sim" / "python.sh")

    patterns = [
        "/home/user01/.local/share/ov/pkg/isaac-sim*/python.sh",
        "/home/user01/isaacsim*/python.sh",
        "/home/user01/isaac-sim*/python.sh",
        "/opt/nvidia/isaacsim*/python.sh",
        "/home/user01/Desktop/isaac-sim*/python.sh",
        "/home/user01/Desktop/IsaacLab/_isaac_sim/python.sh",
    ]
    for pat in patterns:
        candidates.extend(Path(p) for p in glob.glob(pat))

    seen = set()
    unique = []
    for c in candidates:
        c = c.expanduser().resolve()
        if c in seen:
            continue
        seen.add(c)
        unique.append(c)

    existing = [c for c in unique if c.is_file() and os.access(c, os.X_OK)]
    existing.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return existing


def _relaunch_in_isaac(args: list[str]) -> int:
    py_sh_list = _candidate_python_sh()
    if not py_sh_list:
        print("ERROR: Isaac Sim python.sh not found.")
        print("Searched in ~/.local/share/ov/pkg, /home/user01/isaacsim*, /opt/nvidia/isaacsim*, and nearby IsaacLab tree.")
        return 2

    python_sh = py_sh_list[0]
    cmd = [str(python_sh), str(Path(__file__).resolve()), *args, "--_in_isaac"]
    print(f"[launcher] Using Isaac Sim python: {python_sh}")
    return subprocess.call(cmd)


def _run_sim(config: dict, usd_path: Path, gui: bool, seconds_override: float | None) -> int:
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": not gui})
    try:
        import carb
        import omni.timeline
        import omni.usd
        from pxr import UsdGeom

        dt = float(config.get("run", {}).get("dt", 1.0 / 240.0))
        steps = int(config.get("run", {}).get("steps", 720))
        if seconds_override is not None:
            steps = max(1, int(seconds_override / dt))

        log_rate_hz = float(config.get("logging", {}).get("rate_hz", 60.0))
        log_every = max(1, int(round((1.0 / log_rate_hz) / dt)))

        settings = carb.settings.get_settings()
        settings.set_float("/physics/timeStepsPerSecond", 1.0 / dt)

        usd_abs = usd_path.resolve()
        if not usd_abs.is_file():
            print(f"ERROR: USD not found: {usd_abs}")
            return 3

        ctx = omni.usd.get_context()
        if not ctx.open_stage(str(usd_abs)):
            print(f"ERROR: Failed to open USD: {usd_abs}")
            return 4

        for _ in range(20):
            app.update()

        stage = ctx.get_stage()
        block_path = config.get("scene", {}).get("block_prim_path", "/World/block")
        block_prim = stage.GetPrimAtPath(block_path)
        if not block_prim.IsValid():
            print(f"ERROR: Block prim not found: {block_path}")
            return 5

        xformable = UsdGeom.Xformable(block_prim)

        repo_root = Path(__file__).resolve().parents[1]
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        run_dir = repo_root / "results" / "block_on_plane" / ts
        run_dir.mkdir(parents=True, exist_ok=False)

        rows = []
        prev_pos = None

        timeline = omni.timeline.get_timeline_interface()
        timeline.play()

        for i in range(steps):
            app.update()

            if i % log_every != 0 and i != steps - 1:
                continue

            xf = xformable.ComputeLocalToWorldTransform(0.0)
            p = xf.ExtractTranslation()
            pos = (float(p[0]), float(p[1]), float(p[2]))

            if prev_pos is None:
                vel = (0.0, 0.0, 0.0)
            else:
                vel = (
                    (pos[0] - prev_pos[0]) / dt,
                    (pos[1] - prev_pos[1]) / dt,
                    (pos[2] - prev_pos[2]) / dt,
                )

            rows.append(
                {
                    "time": i * dt,
                    "block_pos_x": pos[0],
                    "block_pos_y": pos[1],
                    "block_pos_z": pos[2],
                    "block_vel_x": vel[0],
                    "block_vel_y": vel[1],
                    "block_vel_z": vel[2],
                }
            )
            prev_pos = pos

        timeline.stop()

        signals_path = run_dir / "signals.csv"
        with signals_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "time",
                    "block_pos_x",
                    "block_pos_y",
                    "block_pos_z",
                    "block_vel_x",
                    "block_vel_y",
                    "block_vel_z",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)

        summary = {
            "usd": str(usd_abs),
            "dt": dt,
            "steps": steps,
            "log_rate_hz": log_rate_hz,
            "samples": len(rows),
            "notes": "TODO: add direct contact/friction force logging hooks via PhysX tensor/contact APIs.",
        }
        (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

        print(f"Run complete: {run_dir}")
        print(f"Signals: {signals_path}")
        return 0
    finally:
        app.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run block_on_plane USD simulation and log kinematics")
    parser.add_argument("--config", type=Path, default=Path("experiments/block_on_plane/config.yaml"))
    parser.add_argument("--usd", type=Path, default=Path("assets/usd/block_on_plane/block_on_plane.usd"))
    parser.add_argument("--seconds", type=float, default=None, help="Override runtime in seconds")
    parser.add_argument("--gui", action="store_true", help="Run with GUI")
    parser.add_argument("--_in_isaac", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if not args._in_isaac:
        forward = [a for a in sys.argv[1:] if a != "--_in_isaac"]
        return _relaunch_in_isaac(forward)

    if not args.config.is_file():
        print(f"ERROR: Config missing: {args.config}")
        return 1

    config = json.loads(args.config.read_text(encoding="utf-8"))
    return _run_sim(config=config, usd_path=args.usd, gui=bool(args.gui), seconds_override=args.seconds)


if __name__ == "__main__":
    raise SystemExit(main())
