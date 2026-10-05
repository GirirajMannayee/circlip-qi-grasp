.PHONY: simulate rust-results all setup python-test rust-test test noise montecarlo tables figures circuits reference verify bench clean
PY ?= python3
all: reference noise montecarlo circuits tables figures rust-test verify rust-results   ## full reproduction (~1 min)

setup:            ## pinned Python stack (Qiskit 2.5.2 / Aer 0.17.2 / ibm-runtime 0.50.0)
	$(PY) -m pip install -e "python[quantum,stats,dev]" tabulate pylatexenc
reference:        ## Python reference vectors for the Rust cross-check
	$(PY) scripts/export_reference_vectors.py
noise:            ## Gates 2-3: ideal + FakeManilaV2 (Tables 12-14, Fig 17)
	$(PY) scripts/run_noise.py
montecarlo:       ## Gate 1 selection study (Table 15, Fig 18)
	$(PY) scripts/run_montecarlo.py
circuits:         ## Quirk JSON/URL + OpenQASM (App. B.4-B.5)
	$(PY) scripts/export_circuits.py
simulate:         ## fill the planned log; write the SIMULATED example log
	$(PY) stats/randomize_run_order.py --seed 20261005 --out data/trial_log_planned.csv && $(PY) scripts/simulate_trial_log.py
tables:
	$(PY) scripts/extract_manuscript_tables.py && $(PY) scripts/make_tables.py && $(PY) scripts/weight_sensitivity.py
figures:
	$(PY) scripts/make_figures.py
python-test:
	cd python && $(PY) -m pytest -q
rust-test:
	cd rust && cargo test --release
test: python-test rust-test
verify:           ## Rust core vs Python reference (500 records)
	cd rust && cargo build --release && ./target/release/qi-grasp verify --ref ../data/reference/reference_vectors.csv
rust-results:     ## Rust Monte-Carlo + dev-machine latency into data/results/
	cd rust && cargo build --release && ./target/release/qi-grasp montecarlo > ../data/results/rust_montecarlo.txt
	(echo "# Rust latency ($$(uname -sr), $$(nproc) cores) - NOT the target edge hardware; H5 remains open"; for m in argmax hard "soft --k 2"; do rust/target/release/qi-grasp bench --mode $$m --calls 100000 | head -1; done) > data/results/rust_latency_dev_machine.txt
bench:            ## latency profile on THIS machine (H5 needs the target hardware)
	cd rust && cargo build --release && for m in argmax hard "soft --k 2"; do ./target/release/qi-grasp bench --mode $$m --calls 100000; done
clean:
	rm -rf rust/target python/*.egg-info python/.pytest_cache figures/generated/* tables/generated/* data/results/*
