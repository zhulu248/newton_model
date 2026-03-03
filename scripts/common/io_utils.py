from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


def load_config(config_path: Path) -> Dict:
    # Use JSON payload inside *.yaml for zero-dependency parsing.
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def make_run_dir(root: Path, experiment_name: str) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    run_dir = root / "results" / experiment_name / ts
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def write_config_copy(config: Dict, out_path: Path) -> None:
    out_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def write_signals(rows: List[Dict], out_path: Path, fieldnames: Iterable[str]) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)


def write_summary(summary: Dict, out_path: Path) -> None:
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
