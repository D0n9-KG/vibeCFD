# Submarine Case Library

Current reusable case families in this repository:

- `DARPA SUBOFF`
  - Resistance baseline
  - Pressure distribution study
  - Near free-surface placeholder for later expansion
- `Joubert BB2`
  - Wake-field baseline
  - Pressure and velocity template
  - Drag and pressure combined workflow
- `Type 209`
  - Engineering drag workflow
  - Pressure and velocity OpenFOAM template

Match logic should prioritize:

1. Task type alignment
2. Geometry family alignment
3. Expected outputs overlap
4. Input format compatibility

The authoritative raw source remains `domain/submarine/cases/index.json`.
