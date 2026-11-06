# Submission kit (FGCU IBM Qiskit FallFest)

Everything to paste into the submission form, plus the video plan and a final checklist.
Update the three `[ ]` spots if you complete a real-hardware run (see "Biggest remaining points" below).

---

## Project name
```
RoadQure
```

## Description (paste into the form; under 5,000 characters)
```
RoadQure helps a city decide which flooded roads to repair first, so evacuation and hospital routes stay open after the next king tide.

THE PROBLEM
In South Florida, king tides and a rising water table soak the ground under roads, so they fail from below before a pothole ever shows. Cities repair what residents complain about, so these hidden failures get missed, often on evacuation and hospital routes. With a limited repair budget, which combination of roads should a city fix? The answer is not just "the worst roads": repairs on connected roads reinforce each other, because fixing one block of a route is worth little if the next block still floods. It affects residents who rely on those routes, emergency managers and public-works teams in low-lying coastal cities. Miami Beach is our demo area.

WHAT WE BUILT
1. A transparent hidden-damage risk score for every road (tide exposure, groundwater depth, elevation) and an importance weight for evacuation and hospital routes.
2. The repair decision written as a QUBO (one yes/no variable per road, bonuses for connected repairs, a budget), converted to an Ising Hamiltonian and solved with QAOA in Qiskit.
3. A live web app (RoadQure): a 3D map of hidden damage, a dollar budget slider, and a "Find the best repairs" button that runs the quantum search live and compares the result with today's approach (fix the roads with the most complaints) and with an exact classical solver.
4. A fully explained notebook with the circuit, transpilation, training, sampling, noise and error-suppression analysis.

WHY QUANTUM, AND HONEST LIMITS
The number of possible repair plans doubles with every road (2^n), and the connected-repair bonuses couple the choices. That is exactly the QUBO/Ising shape QAOA targets. But we want to be clear: our demo has 8 qubits and 256 possible plans, a laptop solves it exactly in milliseconds, and we do not claim a quantum speedup. Real classical solvers already handle hundreds of roads, no one has shown QAOA beating them, and today's quantum hardware is noisy and cannot run city-sized problems. What we show is a working end-to-end pipeline, the formulation lessons that mattered, and how noise and compilation affect the answer.

HOW WE USED QISKIT
QAOAAnsatz builds the circuit from our Hamiltonian (to_ising). EstimatorV2 (Aer) with COBYLA trains the angles; SamplerV2 samples the circuit (2,000 to 4,000 shots). We transpile for a real IBM device (FakeTorino snapshot, optimization levels 0 to 3), build a noisy simulator from that device's noise model, and apply error suppression (heavier compilation, dynamical decoupling). Results are post-selected to respect the budget. The same circuit powers the live app (Qiskit Aer simulator).

RESULTS (Mid-Beach demo data, 8 roads, budget of 14 crew-days)
- Against random guessing, QAOA finds a near-best plan about 31 times more often on an ideal simulator and about 26 times more often with the noise model of a real IBM chip.
- QAOA's best plan matches the exact classical optimum.
- Same budget, the optimized plan keeps the route to the hospital open about 33% of the time versus 0.3% when repairs go to the most-complained-about roads.
- A key lesson: encoding the budget as a price per crew-day (8 qubits, 37 two-qubit gates after transpiling) beat the standard slack-qubit encoding (12 qubits, 468 gates), 31x versus 2.8x over random.
- [ ] REAL HARDWARE: (add one sentence after running scripts/run_hardware.py, otherwise delete this line)

DATA
The street names, the official Collins Ave evacuation route and the hospital location are real. Elevation, tide exposure, groundwater depth, 311 counts and repair costs are estimated or simulated for the demo, and the app says so. Results show the method works, not what Miami Beach should repair. Measured data can be swapped in without code changes.

WHAT WE LEARNED AND WHAT IS NEXT
Formulation matters as much as the algorithm; a small-looking circuit grows a lot when transpiled for real hardware; and a classical baseline is what makes a result believable. Next: replace the demo inputs with measured data, run on real hardware and compare, and test larger problem sizes.

Code, notebook and run instructions are in the GitHub repository.
```

## Links to fill in
- YouTube demo video: `[ ]`
- GitHub repository: `https://github.com/KatharineRingo/Qiskit-Hackathon`
- Live app (Vercel): `[ ]`
- Files to attach (optional): the two slide charts `results/slide_route_open.png`, `results/slide_good_plans_vs_random.png`, and `results/network_plan.png`

---

## Video plan (about 3 minutes; the rubric in brackets)

| Time | What is on screen | What to say |
|---|---|---|
| 0:00 to 0:20 | The map, hidden damage glowing orange, king tide month | "[problem] In South Florida roads fail from below. Cities fix what people complain about, so soaked roads on evacuation and hospital routes get missed." |
| 0:20 to 0:40 | Click a street (card), toggle "See the water underneath" | "[problem] Here is why this road is at risk, and the water in the ground beneath it. Who it affects: residents, emergency managers, public works." |
| 0:40 to 1:05 | Drag the budget slider | "[solution] With a limited budget, which roads do you fix? Connected repairs reinforce each other, so the best set is a puzzle with 2 to the n possible answers." |
| 1:05 to 1:50 | Press "Find the best repairs": the dot grid, then the result | "[quantum + Qiskit] We write the puzzle as a QUBO and solve it with QAOA in Qiskit, live. Each dot is one of 256 possible plans; brightness shows how often the quantum search found it. A classical computer confirms the answer." |
| 1:50 to 2:15 | Turn on Compare; show the hospital route numbers | "[results] Same budget: the hospital route stays open about 33% of the time instead of 0.3%." |
| 2:15 to 2:55 | Notebook: the results table and the noise/hardware section | "[results, limits] Versus random guessing the quantum search is about 31 times better; with real-chip noise about 26 times. We compared compilation levels and dynamical decoupling. [if run] On real hardware: ..." |
| 2:55 to 3:20 | "How it works" panel, honest limits | "[honesty] This is 8 qubits. A laptop solves it instantly, and there is no proven quantum speedup. What we built is a working pipeline that is ready to scale as hardware improves. Next: measured data, hardware runs, bigger problems." |

Tips: record at 1920x1080; use the Medium budget ($140,000); do one take of the live solve in advance in case the solver is slow; show the notebook output, not the code; keep the voiceover plain (no jargon without a half-sentence of explanation). The website in the video should be the deployed version or `npm run dev` with the solver running.

## Biggest remaining points (be honest about these)
1. **Real hardware (criteria 09 and 10).** Worth up to +3 and more. We have not run on real hardware yet. With an IBM Quantum account: `python scripts/run_hardware.py` (details in `QUANTUM.md`), then re-run the notebook's section 9 and add one sentence to the description. If you cannot, say so plainly. The simulator bonus (criterion 08) is already earned.
2. **Real data.** Replacing the estimated inputs (see `data/DATA_NOTES.md`) strengthens the problem and results criteria.

## Questions the judges may ask, and plain answers
- **Why quantum if classical works?** At this size it does not help, and we say so. The problem grows as 2^n, and QAOA is built for this shape. We prove the formulation and pipeline, not a speedup.
- **Did you run on a real quantum computer?** Answer truthfully from `results/hardware_run.json`: if it exists, give the device name and job id; if not, "simulator only, including a noise model of a real IBM chip."
- **Is the data real?** Street names, the evacuation route and the hospital are real. The rest is estimated, and the app labels it.
- **How does QAOA find the answer?** It prepares a quantum state, a classical optimizer tunes the angles, and measuring gives bitstrings. Good plans are made more likely, then we keep the best valid one.
- **What did each person do?** Fill in before the video.
