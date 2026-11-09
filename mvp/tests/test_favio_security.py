"""Pruebas de seguridad de la aplicación Flask (sin servicios externos ni pesos YOLO)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app as project


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.old = (project.DATA_DIR, project.IMAGE_DIR, project.PDF_DIR, project.DB_PATH)
        base = Path(self.directory.name)
        project.DATA_DIR = base
        project.IMAGE_DIR = base / "hallazgos"
        project.PDF_DIR = base / "senasa"
        project.DB_PATH = base / "hallazgos.sqlite3"
        self.app = project.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        project.DATA_DIR, project.IMAGE_DIR, project.PDF_DIR, project.DB_PATH = self.old
        self.directory.cleanup()

    def token(self, client):
        client.get("/registro")
        with client.session_transaction() as session:
            return session["csrf_token"]

    def register(self, client, email):
        csrf = self.token(client)
        response = client.post("/registro", data={
            "name": "Usuario de prueba",
            "email": email,
            "password": "Password-De-Prueba-2026",
            "csrf_token": csrf,
        })
        self.assertEqual(response.status_code, 302)
        # El registro rota la sesión y borra el CSRF previo intencionalmente.
        # Una petición a la página autenticada emite el nuevo token.
        self.assertEqual(client.get("/dashboard").status_code, 200)
        with client.session_transaction() as session:
            self.assertIn("csrf_token", session)
            return session["csrf_token"]

    def test_cookie_and_response_security_headers(self):
        self.assertTrue(self.app.config["SESSION_COOKIE_HTTPONLY"])
        self.assertEqual(self.app.config["SESSION_COOKIE_SAMESITE"], "Lax")
        self.assertEqual(self.app.config["PERMANENT_SESSION_LIFETIME"].total_seconds(), 12 * 3600)
        response = self.client.get("/login")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("Referrer-Policy"), "no-referrer")

    def test_anonymous_private_resources_are_blocked(self):
        for path in ("/api/hallazgos", "/api/cultivo/resumen", "/api/dataset/export"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.get("/dashboard").status_code, 302)

    def test_csrf_prevents_mutating_requests(self):
        self.assertEqual(self.client.post("/registro", data={
            "name": "Usuario", "email": "csrf@example.org",
            "password": "Password-De-Prueba-2026",
        }).status_code, 400)
        csrf = self.register(self.client, "user@example.org")
        self.assertEqual(self.client.post("/api/hallazgos", json={}).status_code, 400)
        self.assertEqual(self.client.post("/api/hallazgos", json={},
                         headers={"X-CSRF-Token": "invalido"}).status_code, 400)
        self.assertEqual(self.client.post("/api/hallazgos", json={},
                         headers={"X-CSRF-Token": csrf}).status_code, 400)

    def test_login_rejects_external_or_ambiguous_return_urls(self):
        self.register(self.client, "redirect@example.org")
        for destination in ("//evil.example", "/\\\\evil.example", "/%5Cevil.example",
                            "/%2Fevil.example"):
            with self.subTest(next=destination):
                browser = self.app.test_client()
                csrf = self.token(browser)
                response = browser.post("/login", data={
                    "email": "redirect@example.org",
                    "password": "Password-De-Prueba-2026",
                    "csrf_token": csrf,
                    "next": destination,
                })
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.headers["Location"], "/dashboard")
        browser = self.app.test_client()
        csrf = self.token(browser)
        accepted = browser.post("/login", data={
            "email": "redirect@example.org",
            "password": "Password-De-Prueba-2026",
            "csrf_token": csrf,
            "next": "/esparrago",
        })
        self.assertEqual(accepted.headers["Location"], "/esparrago")

    def test_user_cannot_open_superadmin(self):
        self.register(self.client, "agricultor@example.org")
        self.assertEqual(self.client.get("/admin").status_code, 403)

    def test_logout_invalidates_current_browser_session(self):
        csrf = self.register(self.client, "logout@example.org")
        self.assertEqual(self.client.get("/dashboard").status_code, 200)
        self.assertEqual(self.client.post("/logout", data={"csrf_token": csrf}).status_code, 302)
        self.assertEqual(self.client.get("/api/hallazgos").status_code, 401)
        self.assertEqual(self.client.get("/dashboard").status_code, 302)

    def test_users_cannot_access_other_users_records(self):
        first = self.app.test_client()
        second = self.app.test_client()
        self.register(first, "primero@example.org")
        self.register(second, "segundo@example.org")
        self.assertEqual(first.get("/api/hallazgos").json, [])
        self.assertEqual(second.get("/api/hallazgos").json, [])
        self.assertEqual(second.get("/api/hallazgos/registro-inexistente/imagen").status_code, 404)
        self.assertEqual(second.get("/api/dataset/export").status_code, 403)


if __name__ == "__main__":
    unittest.main()
