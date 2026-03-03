#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
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


def _build_stage(output_usd: Path, mass_kg: float, mu_static: float, mu_dynamic: float, headless: bool) -> int:
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": headless})
    try:
        import omni.usd
        from pxr import Gf, PhysxSchema, Sdf, UsdGeom, UsdPhysics, UsdShade

        output_usd.parent.mkdir(parents=True, exist_ok=True)

        ctx = omni.usd.get_context()
        ctx.new_stage()
        stage = ctx.get_stage()

        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        world = UsdGeom.Xform.Define(stage, Sdf.Path("/World"))
        stage.SetDefaultPrim(world.GetPrim())

        scene = UsdPhysics.Scene.Define(stage, Sdf.Path("/World/physicsScene"))
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr(9.81)
        PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())

        ground = UsdGeom.Cube.Define(stage, Sdf.Path("/World/ground"))
        ground.CreateSizeAttr(1.0)
        UsdGeom.XformCommonAPI(ground).SetScale((20.0, 20.0, 0.1))
        UsdGeom.XformCommonAPI(ground).SetTranslate((0.0, 0.0, -0.05))
        UsdPhysics.CollisionAPI.Apply(ground.GetPrim())

        block = UsdGeom.Cube.Define(stage, Sdf.Path("/World/block"))
        block.CreateSizeAttr(1.0)
        UsdGeom.XformCommonAPI(block).SetScale((0.2, 0.2, 0.2))
        UsdGeom.XformCommonAPI(block).SetTranslate((0.0, 0.0, 0.6))

        block_prim = block.GetPrim()
        UsdPhysics.CollisionAPI.Apply(block_prim)
        rb = UsdPhysics.RigidBodyAPI.Apply(block_prim)
        rb.CreateRigidBodyEnabledAttr(True)
        mass_api = UsdPhysics.MassAPI.Apply(block_prim)
        mass_api.CreateMassAttr(mass_kg)

        mat = UsdShade.Material.Define(stage, Sdf.Path("/World/physicsMaterial"))
        mat_prim = mat.GetPrim()
        mat_api = UsdPhysics.MaterialAPI.Apply(mat_prim)
        mat_api.CreateStaticFrictionAttr(mu_static)
        mat_api.CreateDynamicFrictionAttr(mu_dynamic)
        mat_api.CreateRestitutionAttr(0.0)
        PhysxSchema.PhysxMaterialAPI.Apply(mat_prim)

        UsdShade.MaterialBindingAPI(ground.GetPrim()).Bind(mat)
        UsdShade.MaterialBindingAPI(block_prim).Bind(mat)

        stage.GetRootLayer().Export(str(output_usd))
        app.update()
        print(f"Wrote USD: {output_usd}")
        return 0
    finally:
        app.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic block-on-plane USD scene")
    parser.add_argument("--output", type=Path, default=Path("assets/usd/block_on_plane/block_on_plane.usd"))
    parser.add_argument("--config", type=Path, default=Path("experiments/block_on_plane/config.yaml"))
    parser.add_argument("--headless", action="store_true", help="Run Isaac Sim app headless while generating")
    parser.add_argument("--_in_isaac", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if not args._in_isaac:
        forward = [a for a in sys.argv[1:] if a != "--_in_isaac"]
        return _relaunch_in_isaac(forward)

    cfg = {}
    if args.config.is_file():
        cfg = json.loads(args.config.read_text(encoding="utf-8"))
    block = cfg.get("block", {})
    contact = cfg.get("contact", {})

    return _build_stage(
        output_usd=args.output,
        mass_kg=float(block.get("mass_kg", 1.0)),
        mu_static=float(contact.get("mu_static", 0.6)),
        mu_dynamic=float(contact.get("mu_dynamic", 0.5)),
        headless=bool(args.headless),
    )


if __name__ == "__main__":
    raise SystemExit(main())
