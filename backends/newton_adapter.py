"""Thin backend adapter contract for future Newton engine integration.

Current experiments can run analytic/reference dynamics headlessly,
while preserving a stable adapter shape for Newton-compatible backends.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class StepResult:
    time: float
    position: float
    velocity: float
    normal_force: float
    friction_force: float


class NewtonAdapter:
    def reset(self, config: Dict) -> None:
        raise NotImplementedError

    def step(self, applied_force: float, dt: float) -> StepResult:
        raise NotImplementedError
