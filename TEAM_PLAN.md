# Team plan (2 devs)

The pipeline already runs end to end on fake data. Each of you swaps fake pieces for real ones
without breaking the other person. **The contract between you is the CSV schema** in
`src/undertow/data_synthetic.py` (`SEGMENT_COLUMNS`). Don't change it without telling each other.

## Dev A — Data + risk ("what's failing underwater")
Owns `data_sources.py`, `risk.py`, `data/segments.csv`.

1. **Pick the area.** One neighborhood, 30–60 road segments. West Miami Beach along the bay is the safe pick.
2. **Roads.** `pip install osmnx`, get `load_road_segments()` working, then save a CSV.
3. **Elevation + tides.** Get `add_elevation()` and `load_tides()` working (NOAA Virginia Key 8723214).
   Cache everything to CSV; don't hit the APIs during the demo.
4. **311 potholes.** Download one year from the Miami-Dade Open Data Hub, filter to potholes, count per segment.
5. **Corridors.** Mark the real evacuation route and the road(s) into the nearest hospital.
6. **Deliver `data/segments.csv`.** Dev B runs `python run_demo.py --data data/segments.csv`.
7. **Stretch:** check whether 311 repeat reports line up with low elevation/high tide.
   If they do, that's your best slide ("the data agrees: these roads fail from below").

## Dev B — Quantum + demo ("which repairs keep the city connected")
Owns `qubo.py`, `solve.py`, `hardware.py`, `viz.py`, `run_demo.py`, the slides.

1. **Run it and understand it.** `python run_demo.py`, open `results/demo_map.html`, read `results/demo_qubo.lp`.
   You need to explain the objective to judges in 30 seconds.
2. **Tune the problem size.** Try `--candidates 8/10/12` and `--budget`. Find the biggest size where QAOA
   still matches or nearly matches the exact solver. Record the results for a slide.
3. **IBM hardware.** Set up your token (see `hardware.py`) and run `--hardware` once, early. Save the output.
   Even a noisy hardware result is a great slide when you're honest about it.
4. **Demo polish.** Map legend, pitch slide with the before/after table (current policy vs. your plan).
5. **Stretch (pick one):**
   - Repair *types*: patch vs. full-depth per segment (one-hot constraint, more qubits).
   - King tide scheduling: which week to repair before the next king tide.
   - A small Streamlit app with a budget slider.

## Checkpoints
- **Checkpoint 1:** Dev A has real roads on the map (even with fake attributes). Dev B has run QAOA at 2–3 sizes.
- **Checkpoint 2:** real `segments.csv` runs through the full pipeline.
- **Feature freeze:** stop adding things. Polish the demo, record a backup video, practice the pitch twice.

## Workflow
- Work on branches (`data/...`, `quantum/...`) and merge to `main` often. `main` must always run.
- Run `pytest -q` before merging.
- If you're blocked on the other person, use the synthetic data. Never wait.
