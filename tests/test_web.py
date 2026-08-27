import os, tempfile

def test_health_and_login(monkeypatch):
    fd,path=tempfile.mkstemp(); os.close(fd)
    monkeypatch.setenv('WIZE_DB_PATH',path)
    from wize_wizard.web import create_app
    app=create_app({'TESTING':True,'SECRET_KEY':'test'})
    c=app.test_client()
    assert c.get('/healthz').status_code==200
    r=c.get('/login'); assert r.status_code==200
