def test_version():
    pkg = __import__("tox_lsr", fromlist=["__version__"])
    assert pkg.__version__
