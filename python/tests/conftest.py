def pytest_configure(config):
    config.addinivalue_line("markers", "quantum: needs the pinned Qiskit stack (pip install -e 'python[quantum]')")
