"""Run the same QAOA on real IBM Quantum hardware. UNTESTED in the starter: needs your IBM token.

Setup (once per machine):
    pip install qiskit-ibm-runtime
    python -c "from qiskit_ibm_runtime import QiskitRuntimeService as S; S.save_account(channel='ibm_quantum_platform', token='YOUR_TOKEN', overwrite=True)"

Then:
    python run_demo.py --hardware

Notes:
- Hardware runs queue. Run it once early (Saturday morning), save the output, and demo from the saved file.
- Keep shots and maxiter low; every optimizer iteration is a hardware job inside one session.
- Check the hackathon's instructions for which channel/instance and backends you're allowed to use.
- If Runtime's API has changed, check the qiskit-ibm-runtime docs: the shape here is
  "get a backend, wrap it in SamplerV2, transpile for that backend".
"""

from __future__ import annotations


def get_ibm_sampler(backend_name: str | None = None, shots: int = 1000):
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService()
    backend = service.backend(backend_name) if backend_name else service.least_busy(operational=True, simulator=False)
    sampler = SamplerV2(mode=backend)
    sampler.options.default_shots = shots
    return sampler, backend
