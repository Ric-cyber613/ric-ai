def test_app_import():
    # Ensure the Flask app module imports cleanly and exposes `app`
    import importlib
    m = importlib.import_module('web.app')
    assert hasattr(m, 'app')
    from flask import Flask
    assert isinstance(m.app, Flask)
