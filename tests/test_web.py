import os
import tempfile


def test_health_and_login(monkeypatch):
    fd, path = tempfile.mkstemp()
    os.close(fd)

    monkeypatch.setenv("WIZE_DB_PATH", path)
    monkeypatch.setenv("WIZE_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("WIZE_ADMIN_PASSWORD", "TestOnlyPassword123!")

    from wize_wizard.web import create_app

    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test",
    })

    client = app.test_client()

    r = client.get("/healthz")
    assert r.status_code == 200

    r = client.get("/login")
    assert r.status_code == 200

    os.unlink(path)


def test_fresh_install_requires_bootstrap_credentials(monkeypatch):
    fd, path = tempfile.mkstemp()
    os.close(fd)

    monkeypatch.setenv("WIZE_DB_PATH", path)
    monkeypatch.delenv("WIZE_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("WIZE_ADMIN_PASSWORD", raising=False)

    from wize_wizard.web import create_app

    try:
        create_app({
            "TESTING": True,
            "SECRET_KEY": "test",
        })
        assert False, "Fresh install should require bootstrap credentials"
    except RuntimeError as exc:
        assert "WIZE_ADMIN_USERNAME" in str(exc)
        assert "WIZE_ADMIN_PASSWORD" in str(exc)
    finally:
        os.unlink(path)
