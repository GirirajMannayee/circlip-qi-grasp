"""FakeManilaV2 noise experiment (Sec. 4.4, Table 8, 12, 14) and global-depolarizing fit (Eq. 13, Table 13)."""
from __future__ import annotations
import numpy as np
from qiskit.quantum_info import Statevector
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2
from .circuits import build_circuit, build_gate_level
from .core import N, soft_phases, hard_phases, utility, candidate_set_seed42

SEEDS = list(range(42, 52)); SHOTS = 4096


def ideal_probs(qc_nomeas) -> np.ndarray:
    return Statevector.from_instruction(qc_nomeas).probabilities()


def hellinger_fidelity(p, q) -> float:
    return float(np.sum(np.sqrt(p * q)) ** 2)


def run_config(name, qc, qc_ideal, target, backend, shots=SHOTS, seeds=SEEDS):
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1, seed_transpiler=42)
    isa = pm.run(qc)
    ops = isa.count_ops()
    two_q = sum(v for k, v in ops.items() if k in ("cx", "ecr", "cz"))
    sim = AerSimulator.from_backend(backend)
    p_ideal = ideal_probs(qc_ideal)
    t, fid, modal, mean_dist = [], [], [], np.zeros(N)
    for s in seeds:
        counts = sim.run(isa, shots=shots, seed_simulator=s).result().get_counts()
        dist = np.zeros(N)
        for bits, c in counts.items():
            dist[int(bits.replace(" ", ""), 2)] += c
        dist /= shots
        t.append(dist[target]); fid.append(hellinger_fidelity(p_ideal, dist))
        modal.append(int(np.argmax(dist)) == target); mean_dist += dist / len(seeds)
    return dict(name=name, depth=isa.depth(), two_qubit_gates=two_q,
                ideal_p=float(p_ideal[target]), noisy_p_mean=float(np.mean(t)),
                noisy_p_sd=float(np.std(t, ddof=1)), hellinger_mean=float(np.mean(fid)),
                hellinger_sd=float(np.std(fid, ddof=1)), modal_best_all_seeds=bool(all(modal)),
                modal_best_mean_dist=bool(int(np.argmax(mean_dist)) == target),
                mean_dist=mean_dist.tolist(), ideal_dist=p_ideal.tolist())


def strip_measure(qc):
    return qc.remove_final_measurements(inplace=False)


def run_all(shots=SHOTS, seeds=SEEDS):
    backend = FakeManilaV2()
    U = utility(candidate_set_seed42()); target = int(np.argmax(U))
    cfgs = [("Hard, K=3 (gate-level X-CCCZ-X)", build_gate_level(3), 3),
            ("Hard, K=3 (DiagonalGate)", build_circuit(hard_phases(U), 3), 3),
            ("Soft (g=6), K=2 (DiagonalGate)", build_circuit(soft_phases(U), 2), 2),
            ("Soft (g=6), K=3 (DiagonalGate)", build_circuit(soft_phases(U), 3), 3)]
    return [run_config(n, qc, strip_measure(qc), target, backend, shots, seeds) for n, qc, _ in cfgs]


def depolarizing_fit(p_ideal, p_noisy, g, n=N):
    """Eq. (13) inverted: lambda = (Pn - 1/N)/(Pi - 1/N), f = lambda**(1/g)."""
    lam = (p_noisy - 1 / n) / (p_ideal - 1 / n)
    f = lam ** (1 / g)
    return lam, f


def predicted_noisy(p_ideal, g, f, n=N):
    return f ** g * p_ideal + (1 - f ** g) / n


def g_max_for_threshold(f, p_ideal=0.961, thr=0.5, n=N):
    """Largest g with P_noisy >= thr under Eq. (13)."""
    lam = (thr - 1 / n) / (p_ideal - 1 / n)
    return np.log(lam) / np.log(f)
