def test_health():
    from services.inference_api.main import app
    assert app is not None