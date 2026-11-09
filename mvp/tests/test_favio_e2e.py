"""Pruebas E2E con Chromium real sobre el servidor Flask local de CI.

Se ejecutan únicamente contra AGRI_E2E_BASE_URL (por defecto localhost).
No necesitan pesos YOLO, cámara física ni SENASA externo.
"""
import os
import unittest
import uuid
from pathlib import Path


BASE_URL = os.environ.get("AGRI_E2E_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
EVIDENCE = Path(__file__).resolve().parents[1] / "test-results" / "playwright"


@unittest.skipUnless(os.environ.get("AGRI_RUN_PLAYWRIGHT") == "1",
                     "Las pruebas E2E solo se ejecutan en el job de Playwright")
class BrowserJourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright

        EVIDENCE.mkdir(parents=True, exist_ok=True)
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1280, "height": 800},
                                                 reduced_motion="reduce")
        self.page = self.context.new_page()
        self.page.set_default_timeout(10000)

    def tearDown(self):
        if self.page:
            name = self.id().rsplit(".", 1)[-1]
            self.page.screenshot(path=str(EVIDENCE / f"{name}.png"), full_page=True)
        self.context.close()

    def test_portal_to_inspection_navigation(self):
        self.page.goto(BASE_URL + "/", wait_until="domcontentloaded")
        self.assertTrue(self.page.get_by_role("heading", name="¿Qué necesitas analizar?").is_visible())
        self.page.get_by_role("link", name="Abrir inspección con YOLO").click()
        self.page.wait_for_url("**/esparrago")
        self.assertTrue(self.page.locator("#photoInput").count() == 1)
        self.assertTrue(self.page.locator("#cameraBtn").is_visible())
        self.assertTrue(self.page.locator("#resultados").count() == 1)

    def test_mobile_layout_and_section_navigation(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.page.goto(BASE_URL + "/esparrago", wait_until="domcontentloaded")
        self.assertTrue(self.page.get_by_role("heading", name="Inspeccionar cultivo").is_visible())
        self.assertTrue(self.page.locator("#photoInput").count() == 1)
        self.page.locator('nav a[href="#historial"]').click()
        self.assertEqual(self.page.evaluate("location.hash"), "#historial")
        # No debe haber desplazamiento horizontal global involuntario.
        metrics = self.page.evaluate("({screen: document.documentElement.clientWidth, content: document.documentElement.scrollWidth})")
        self.assertLessEqual(metrics["content"], metrics["screen"] + 2, metrics)

    def test_invalid_upload_reports_error_without_server_inference(self):
        self.page.goto(BASE_URL + "/esparrago", wait_until="domcontentloaded")
        self.page.locator("#photoInput").set_input_files({
            "name": "invalido.txt",
            "mimeType": "text/plain",
            "buffer": b"no es una imagen",
        })
        self.assertIn("archivo de imagen", self.page.locator("#message").inner_text().lower())
        self.assertTrue(self.page.locator("#emptyState").is_visible())

    def test_register_private_dashboard_and_logout(self):
        email = f"favio-e2e-{uuid.uuid4().hex[:12]}@example.org"
        self.page.goto(BASE_URL + "/registro", wait_until="domcontentloaded")
        self.page.locator('input[name="name"]').fill("Usuario E2E")
        self.page.locator('input[name="email"]').fill(email)
        self.page.locator('input[name="password"]').fill("Password-Seguro-E2E-2026")
        self.page.get_by_role("button", name="Crear cuenta gratuita").click()
        self.page.wait_for_url("**/dashboard")
        self.assertTrue(self.page.locator("body").is_visible())
        self.assertEqual(self.page.request.get(BASE_URL + "/api/hallazgos").status, 200)
        # El logout POST requiere token CSRF. Leerlo de un formulario real de la sesión.
        token = self.page.locator('input[name="csrf_token"]').first.input_value()
        response = self.page.request.post(BASE_URL + "/logout", form={"csrf_token": token})
        self.assertEqual(response.status, 200)  # Playwright sigue la redirección 302
        self.assertEqual(self.page.request.get(BASE_URL + "/api/hallazgos").status, 401)


if __name__ == "__main__":
    unittest.main()
