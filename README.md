newton-open-model-lab_README_v2.md

Yes, I understand. You are not building an “app.” You are building a set of small, reproducible example models (experiments) to learn and validate Newton-compatible physics (geometry, contact, friction), and later grow those into actuator / ball screw / gearbox entry models.

Below are the regenerated “remaining files” in a repo-friendly form (each file content is ready to paste).

================================================================================
README.md
=========

Newton Open Model Lab

Purpose
This repo is a simulation-only sandbox for building and validating small mechanism models with geometry + contact + friction, using Newton-compatible and open (non-licensed) tooling. The output is not an application; it is a set of example models (“experiments”) plus a repeatable way to run them and compare physics signals.

What this repo is

* A collection of small models you can run, inspect, and validate.
* A consistent way to store assets, parameters, and results.
* A place to test Newton behavior on contact/friction problems before scaling to ball screw / actuator / gearbox entry models.

What this repo is not

* Not a web app, not a product UI, not an end-user application.
* Not a large framework. Keep it minimal and experiment-driven.

Model scope (phased)
Phase 1: smallest contact/friction models

* block on plane (sliding friction)
* ball on plane or ball in groove (rolling/sliding + contact)
* pin-in-slot (contact-rich constraint)

Phase 2: ball screw entry model

* rotational-to-linear conversion
* frictional loss mapping
* optional compliance/backlash later

Phase 3: actuator/gearbox building blocks

* gear contact simplifications
* bearings/friction losses
* efficiency and thermal proxy signals (later)

Key rule: script-first, GUI optional
You may use graphical tools to author or inspect geometry, but every experiment must be runnable headless from a script so results are reproducible.

Repository layout

* experiments/
  Each experiment is self-contained: config + runner script + notes.
* assets/
  Geometry and scene assets (meshes, USD/URDF/SDF, materials).
* backends/
  Thin adapters for physics engines (Newton first, others optional).
* results/
  Auto-generated outputs from runs (should be git-ignored).
* docs/
  Modeling conventions, parameter definitions, validation notes.

Experiment format (recommended)
Each experiment folder includes:

* config.yaml
  Canonical parameters for geometry, contact, friction, solver settings, and run length.
* run.py
  A minimal runner that loads config, executes sim steps, logs signals.
* expected_behavior.md
  What “sanity” looks like (qualitative + any quick quantitative checks).

Signals to log (minimum set)

* time
* generalized coordinates (q, qd) or pose/vel for key bodies
* contact normal force (or total normal impulse)
* friction force (or tangential impulse)
* slip velocity at contact (or relative tangential speed)
* penetration depth (if compliant contact)
* energy proxies (work by friction, etc.)

Physics conventions (canonical)
Units

* meters, kilograms, seconds, radians
* Newtons, N·m

Friction parameters

* mu_static
* mu_dynamic
* optional v_stribeck (if your backend supports Stribeck)
* contact stiffness/damping (if using compliant contact)

How to use this repo (typical workflow)

1. Pick one experiment (start with block_on_plane).
2. Run it with a simple script.
3. Inspect plots and sanity checks.
4. Adjust contact/friction parameters and rerun.
5. Lock a baseline result for regression.

Roadmap checkpoints

* C0: one experiment runs end-to-end and produces logs
* C1: contact/friction signals behave qualitatively correct
* C2: stable results across small dt changes
* C3: ball screw entry model runs and produces consistent loss curves
* C4: compare Newton vs one other open engine on the same experiment configs

License
Use an OSI license for code (MIT/BSD/Apache). Ensure any geometry assets have compatible licenses.

================================================================================
docs/MODELING_CONVENTIONS.md
============================

Modeling Conventions

1. Canonical coordinate frames

* World frame: +Z up (or +Y up), choose one and never mix.
* Document the choice per experiment in config.yaml.

2. Canonical parameter schema (suggested keys)

* model:
  name:
  asset:
* run:
  dt:
  steps:
  seed:
* contact:
  model: coulomb | stribeck | backend_default
  mu_static:
  mu_dynamic:
  v_stribeck: (optional)
  restitution:
  normal_stiffness: (optional)
  normal_damping: (optional)
* logging:
  rate_hz:
  signals: [list]

3. What counts as “validated”
   At minimum:

* friction direction opposes motion
* friction magnitude is near mu*N during steady sliding (for Coulomb)
* energy dissipated by friction is nonnegative and increases with sliding distance
* results are stable when dt is reduced (within a tolerance you define)

4. Result storage

* Every run writes:

  * config_used.yaml (exact config copied)
  * summary.json (metadata + quick stats)
  * signals.csv (time series)
  * plots/ (optional)

================================================================================
docs/ENTRY_MODEL_CHECKLIST.md
=============================

Entry Model Checklist (for each new experiment)

Definition

* What is the mechanism and what question does it answer?
* What is the minimum geometry required to express the physics?

Inputs

* Geometry parameters
* Material/contact parameters
* Initial conditions
* Control inputs (if any)

Outputs (log)

* State (pose/velocity of key bodies)
* Contact normal and tangential signals
* Slip velocity at contact
* Energy/work proxies

Sanity checks (must pass)

* Contact only active when bodies intersect/approach correctly
* Normal force nonnegative (or physically consistent with your contact law)
* Friction opposes relative tangential motion
* No obvious numerical explosion at baseline dt

Regression baseline

* Save one baseline config and baseline result stats
* Define tolerances for future changes

================================================================================
experiments/block_on_plane/expected_behavior.md
===============================================

Block on Plane: Expected Behavior

Goal
Validate basic sliding friction behavior with a simple contact pair.

Qualitative expectations

* With gravity on, the block rests with a nonzero normal force approximately equal to m*g (depending on contact model).
* If a horizontal force is applied:

  * below static threshold: no sliding (or near-zero slip)
  * above static threshold: sliding begins
* During steady sliding:

  * friction magnitude is near mu_dynamic * N
  * friction direction opposes slip velocity

Quantitative quick checks (rough)

* N ~ m*g (within a tolerance depending on contact stiffness/damping)
* |F_friction| / N ~ mu_dynamic during steady sliding

Failure patterns to watch

* friction accelerates the block (sign error)
* friction magnitude grows without bound (unstable contact)
* penetration depth unrealistic (contact stiffness too low or dt too large)

================================================================================
experiments/block_on_plane/config.yaml
======================================

model:
name: block_on_plane
asset: assets/block_on_plane/usd_or_urdf_placeholder

run:
dt: 0.001
steps: 5000
seed: 0

contact:
model: coulomb
mu_static: 0.6
mu_dynamic: 0.5
restitution: 0.0
normal_stiffness: 1.0e6
normal_damping: 1.0e3

logging:
rate_hz: 200
signals:
- time
- block_pos
- block_vel
- normal_force
- friction_force
- slip_velocity
- penetration_depth
- friction_work

================================================================================
CODEx_PROMPT_experiment_only.txt
================================

You are working in a repository that is NOT an app. It is a simulation experiment sandbox.

Task:
Create the minimal files needed to run one experiment called experiments/block_on_plane without any GUI requirement.

Requirements:

1. Provide a simple Python script experiments/block_on_plane/run.py that:

   * loads experiments/block_on_plane/config.yaml
   * runs a simulation loop (backend can be a placeholder if Newton API is not wired yet)
   * logs signals listed in config to results/block_on_plane/<timestamp>/
   * writes config_used.yaml and summary.json

2. Keep the code minimal and readable:

   * no web server
   * no UI
   * no complex framework

3. If Newton backend integration is unknown, implement a stub backend that generates physically plausible placeholder signals (normal force ~ m*g, friction ~ mu*N when sliding), so the pipeline is runnable now.

Output:

* create the file tree
* write the code files
* ensure “python experiments/block_on_plane/run.py” runs end-to-end and produces results.

If you want the repo even simpler, tell me and I’ll collapse it to only:

* experiments/block_on_plane/{config.yaml, run.py, expected_behavior.md}
* docs/{MODELING_CONVENTIONS.md, ENTRY_MODEL_CHECKLIST.md}
* README.md
* .gitignore (results/ ignored)
