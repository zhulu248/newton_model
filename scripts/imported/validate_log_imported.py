#!/usr/bin/env python3
import csv
import math
import sys

# Expected CSV columns:
# t, spindle_omega_rad_s, nut_v_m_s, spindle_torque_nm, nut_force_n, total_energy_j

if len(sys.argv) < 2:
    print("Usage: python3 scripts/30_validate_log.py <log.csv> [nominal_lead_m]")
    sys.exit(1)

path = sys.argv[1]
nominal_lead = float(sys.argv[2]) if len(sys.argv) > 2 else None

rows = []
with open(path, "r", newline="") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

if not rows:
    print("No data rows found")
    sys.exit(1)

def avg(vals):
    return sum(vals) / len(vals) if vals else float("nan")

omega = [float(r["spindle_omega_rad_s"]) for r in rows]
vnut = [float(r["nut_v_m_s"]) for r in rows]
torque = [float(r["spindle_torque_nm"]) for r in rows]
force = [float(r["nut_force_n"]) for r in rows]
energy = [float(r["total_energy_j"]) for r in rows]

obs_leads = []
for w, v in zip(omega, vnut):
    if abs(w) > 1e-8:
        obs_leads.append(2.0 * math.pi * v / w)

lead_obs = avg(obs_leads)
print(f"Observed lead [m/rev]: {lead_obs:.8f}")

if nominal_lead is not None and math.isfinite(lead_obs):
    rel = abs(lead_obs - nominal_lead) / max(abs(nominal_lead), 1e-12)
    print(f"Lead error [%]: {100.0 * rel:.4f}")

# Linear fit torque ~= a*force + b (least squares closed form)
mx = avg(force)
my = avg(torque)
num = sum((x - mx) * (y - my) for x, y in zip(force, torque))
den = sum((x - mx) ** 2 for x in force)
a = num / den if den > 1e-12 else float("nan")
b = my - a * mx if math.isfinite(a) else float("nan")
print(f"Torque-thrust slope [Nm/N]: {a:.8e}")
print(f"Torque-thrust intercept [Nm]: {b:.8f}")

if len(energy) >= 2:
    drift = energy[-1] - energy[0]
    rel_drift = drift / max(abs(energy[0]), 1e-12)
    print(f"Energy drift [J]: {drift:.8f}")
    print(f"Relative energy drift [-]: {rel_drift:.8e}")
