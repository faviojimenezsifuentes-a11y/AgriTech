"""Pruebas de regresión IDOR/BOLA: hallazgos y fotos no se comparten entre agricultores.

Usa dos sesiones independientes, imágenes JPEG reales y una base SQLite temporal.
No utiliza el modelo YOLO ni servicios externos.
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app as project


class FindingPrivacyRegressionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.original_paths = (
            project.DATA_DIR, project.IMAGE_DIR, project.PDF_DIR, project.DB_PATH
        )
        base = Path(self.directory.name)
        project.DATA_DIR = base
        project.IMAGE_DIR = base / "hallazgos"
        project.PDF_DIR = base / "senasa"
        project.DB_PATH = base / "hallazgos.sqlite3"
        self.app = project.create_app()
        self.app.config["TESTING"] = True
        self.alice = self.app.test_client()
        self.bob = self.app.test_client()
        self.guest = self.app.test_client()
        self.alice_id = self.register(self.alice, "alice@example.org")
        self.bob_id = self.register(self.bob, "bob@example.org")
        self.alice_finding = self.seed_finding(self.alice_id, "alice-foto", "Sector A")
        self.bob_finding = self.seed_finding(self.bob_id, "bob-foto", "Sector B")

    def tearDown(self):
        (project.DATA_DIR, project.IMAGE_DIR, project.PDF_DIR,
         project.DB_PATH) = self.original_paths
        self.directory.cleanup()

    def register(self, client, email):
        response = client.get("/registro")
        self.assertEqual(response.status_code, 200)
        with client.session_transaction() as session:
            csrf = session["csrf_token"]
        response = client.post("/registro", data={
            "name": "Agricultor Prueba",
            "email": email,
            "password": "Password-Segura-2026",
            "csrf_token": csrf,
        })
        self.assertEqual(response.status_code, 302)
        with client.session_transaction() as session:
            return session["user_id"]

    def seed_finding(self, owner_id, finding_id, sector):
        # El endpoint de lectura debe proteger fotografías ya existentes.
        # Se insertan fixtures directamente sin pasar por YOLO.
        project.IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{finding_id}.jpg"
        img = Image.new("RGB", (48, 48), (95, 135, 85))
        img.save(project.IMAGE_DIR / filename, "JPEG")
        now = datetime.now(timezone.utc).isoformat()
        with project.db_connection() as db:
            db.execute(
                """INSERT INTO hallazgos
                   (id,created_at,sector,lat,lon,observations,
                    detections_json,image_name,status,reviewed_at,model_name,owner_id)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (finding_id, now, sector, None, None, "Inspección privada",
                 json.dumps([]), filename, "confirmado", now, "desconocido", owner_id),
            )
        return finding_id

    def test_each_farmer_sees_only_own_findings_in_list(self):
        alice = self.alice.get("/api/hallazgos")
        bob = self.bob.get("/api/hallazgos")
        self.assertEqual(alice.status_code, 200)
        self.assertEqual(bob.status_code, 200)
        self.assertEqual([item["id"] for item in alice.json], [self.alice_finding])
        self.assertEqual([item["id"] for item in bob.json], [self.bob_finding])
        self.assertEqual(alice.json[0]["image_url"],
                         f"/api/hallazgos/{self.alice_finding}/imagen")
        self.assertNotIn(self.bob_finding, alice.get_data(as_text=True))
        self.assertNotIn(self.alice_finding, bob.get_data(as_text=True))

    def test_cross_account_photo_urls_are_forbidden(self):
        for viewer, own, foreign in (
            (self.alice, self.alice_finding, self.bob_finding),
            (self.bob, self.bob_finding, self.alice_finding),
        ):
            with self.subTest(own=own, foreign=foreign):
                own_response = viewer.get(f"/api/hallazgos/{own}/imagen")
                self.assertEqual(own_response.status_code, 200)
                self.assertEqual(own_response.mimetype, "image/jpeg")
                Image.open(io.BytesIO(own_response.data)).verify()

                # Conocer el identificador UUID no autoriza a obtener la foto.
                foreign_response = viewer.get(f"/api/hallazgos/{foreign}/imagen")
                self.assertIn(foreign_response.status_code, (403, 404))
                self.assertNotEqual(foreign_response.mimetype, "image/jpeg")

    def test_anonymous_cannot_list_or_read_photos(self):
        self.assertEqual(self.guest.get("/api/hallazgos").status_code, 401)
        for finding in (self.alice_finding, self.bob_finding):
            with self.subTest(finding=finding):
                self.assertEqual(
                    self.guest.get(f"/api/hallazgos/{finding}/imagen").status_code,
                    401,
                )

    def test_nonexistent_and_legacy_unowned_photo_is_not_public(self):
        self.assertEqual(
            self.alice.get("/api/hallazgos/no-existe/imagen").status_code, 404
        )
        self.seed_finding(None, "foto-sin-duenio", "Registro antiguo")
        for client in (self.alice, self.bob):
            self.assertNotIn(
                "foto-sin-duenio", client.get("/api/hallazgos").get_data(as_text=True)
            )
            self.assertEqual(
                client.get("/api/hallazgos/foto-sin-duenio/imagen").status_code,
                404,
            )

    def test_dataset_export_cannot_include_another_farmer_photos(self):
        # Campo Pro habilita exportación; verifica que el ZIP incluya solo
        # registros del usuario, incluso si ambos tienen hallazgos confirmados.
        with project.db_connection() as db:
            db.execute("UPDATE users SET plan='pro' WHERE id IN (?,?)",
                       (self.alice_id, self.bob_id))
        for client, own, foreign in (
            (self.alice, self.alice_finding, self.bob_finding),
            (self.bob, self.bob_finding, self.alice_finding),
        ):
            with self.subTest(own=own):
                response = client.get("/api/dataset/export")
                self.assertEqual(response.status_code, 200)
                import zipfile
                with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
                    filenames = archive.namelist()
                    self.assertIn(f"images/{own}.jpg", filenames)
                    self.assertNotIn(f"images/{foreign}.jpg", filenames)


if __name__ == "__main__":
    unittest.main()
