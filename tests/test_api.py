from codebase_analysis.api import app

 
def test_health_endpoint():
    client = app.test_client()
    resp = client.get('/healthz')
    assert resp.status_code == 200
    assert resp.data == b'ok' 