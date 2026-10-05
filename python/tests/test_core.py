import numpy as np, pytest
from qi_grasp import *
from qi_grasp.force import overshoot_pct, tilt_deg
from qi_grasp.montecarlo import run as mc_run

F = candidate_set_seed42(); U = utility(F)

def test_weights_sum_to_one(): assert WEIGHTS.sum() == pytest.approx(1.0)
def test_seed42_best_candidate(): assert (int(U.argmax()), round(float(U.max()), 3)) == (5, 0.725)
def test_grover_values_proposition_1():
    assert grover_p(np.arange(7)) == pytest.approx([0.062, 0.473, 0.908, 0.961, 0.582, 0.125, 0.020], abs=6e-4)
def test_hard_oracle_equals_grover_law():
    assert [amplitude_search(hard_phases(U), k)[5] for k in range(7)] == pytest.approx(list(grover_p(np.arange(7))), abs=1e-12)
def test_soft_oracle_k2_k3():
    ps = soft_phases(U)
    assert amplitude_search(ps, 2)[5] == pytest.approx(0.506, abs=1e-3) and amplitude_search(ps, 3)[5] == pytest.approx(0.280, abs=1e-3)
def test_probabilities_normalised():
    for k in range(8): assert amplitude_search(soft_phases(U), k).sum() == pytest.approx(1.0)
def test_mask_respected():
    v = np.ones(16, bool); v[5] = False
    for mode in ("argmax", "hard", "soft"): assert select(U, mode, valid=v) != 5
def test_overshoot_matches_manuscript():
    for z, w in ((0.5, 30), (0.7, 21), (1.0, 14), (1.5, 8)): assert overshoot_pct(z) == pytest.approx(w, abs=1.0)
def test_tilt_small_angle(): assert tilt_deg(10, 5, 0.5) == pytest.approx(np.degrees(0.1))
def test_montecarlo_ordering_and_exactness():
    r = mc_run(500).set_index("Method")
    assert r.loc["Exhaustive argmax", "Top-1 (%)"] == 100 and r.loc["QI hard K = 3", "Top-1 (%)"] == 100
    assert r.loc["Greedy (position only)", "Top-1 (%)"] < r.loc["Random subset (8 evals)", "Top-1 (%)"] < r.loc["QI soft K = 3", "Top-1 (%)"]

@pytest.mark.quantum
def test_qasm_export_and_gate_level_equals_statevector():
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    from qi_grasp.circuits import gate_level_qasm2, build_gate_level, quirk_json
    p = Statevector.from_instruction(QuantumCircuit.from_qasm_str(gate_level_qasm2(3)).remove_final_measurements(inplace=False)).probabilities()
    assert p[5] == pytest.approx(0.9613, abs=5e-4) and p.argmax() == 5
    assert len(quirk_json(3)["cols"]) == 1 + 3 * 10 + 1

@pytest.mark.quantum
def test_noise_transpile_cost_matches_table_12():
    from qiskit_ibm_runtime.fake_provider import FakeManilaV2
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    qc = __import__("qi_grasp.circuits", fromlist=["x"]).build_gate_level(3)
    isa = generate_preset_pass_manager(backend=FakeManilaV2(), optimization_level=1, seed_transpiler=42).run(qc)
    assert (isa.depth(), isa.count_ops().get("cx", 0)) == (277, 189)
