#!/usr/bin/env python3
import csv
import sys

# Input CSV columns: name,x,y,z
# Output: XML fragment of ball bodies

if len(sys.argv) < 2:
    print("Usage: python3 scripts/25_generate_ball_bodies.py <balls.csv>")
    sys.exit(1)

with open(sys.argv[1], "r", newline="") as f:
    reader = csv.DictReader(f)
    for i, r in enumerate(reader):
        name = r.get("name") or f"ball_{i:03d}"
        x = float(r["x"])
        y = float(r["y"])
        z = float(r["z"])
        print(f"<body name=\"{name}\" pos=\"{x:.9f} {y:.9f} {z:.9f}\">")
        print("  <freejoint/>")
        print("  <geom type=\"mesh\" mesh=\"ball_collision\" rgba=\"0.9 0.7 0.2 1\"/>")
        print("  <geom type=\"mesh\" mesh=\"ball_visual\" contype=\"0\" conaffinity=\"0\" rgba=\"0.95 0.8 0.3 1\"/>")
        print("</body>")
