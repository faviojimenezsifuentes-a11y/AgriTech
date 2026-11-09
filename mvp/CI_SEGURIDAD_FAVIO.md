# CI y seguridad — contribución Favio

## Objetivo
Pasar de una validación UX exclusivamente estructural a un pipeline con trabajos independientes de calidad, historias de usuario, seguridad, integración funcional y pruebas E2E con un navegador real, con una puerta final de aprobación. **Esta rama todavía no está integrada a `main`.**

## Rama
`Favio/mejoras-ci-seguridad` — fork: [faviojimenezsifuentes-a11y/AgriTech](https://github.com/faviojimenezsifuentes-a11y/AgriTech/tree/Favio/mejoras-ci-seguridad).

## Pipeline nuevo
Archivo `.github/workflows/favio-ci-seguridad.yml`:

1. **Calidad:** `compileall`, Flake8 (errores críticos) y sintaxis de tres archivos JavaScript.
2. **UX/UI:** nueve pruebas estructurales vinculadas a historias SCRUM-18/19/20/21/23/87/89 y comprobaciones adicionales de plantillas.
3. **Seguridad:** pruebas Flask de sesión, CSRF, autenticación, roles, aislamiento entre usuarios, encabezados de seguridad y redirecciones de login.
4. **Integración:** `smoke_test.py` verifica respuestas HTTP, detección simulada cuando faltan los pesos YOLO, registros, cuotas, controles de acceso y exportaciones.
5. **Navegador Playwright:** abre Chromium contra Flask local y comprueba navegación del portal a inspección, responsive móvil, rechazo de archivo inválido, registro, acceso privado y logout. Genera capturas PNG y log de pruebas.
6. **Puerta de calidad:** falla si cualquiera de los cinco trabajos anteriores no termina con resultado `success`.

Los trabajos 1–5 pueden ejecutarse en paralelo; el sexto depende de todos ellos. Se guardan artefactos descargables para UX, seguridad, integración y E2E (capturas de Chromium).

**Disparadores:** push a ramas `Favio/**`, Pull Requests dirigidos a `main` y ejecución manual.

## Mejoras concretas de seguridad
En `mvp/accounts.py` se reforzó la validación de `next` tras el inicio de sesión. Se impiden destinos ambiguos que utilicen doble barra, barra invertida y secuencias codificadas que puedan interpretarse como rutas externas. Las rutas relativas locales válidas continúan permitidas.

`mvp/tests/test_favio_security.py` incorpora pruebas reproducibles que usan SQLite temporal. Las pruebas no dependen de credenciales reales ni contactan SENASA.

## Qué no se modificó
No se modificaron modelos YOLO, datasets, pesos ni el proceso de inferencia. Tampoco se habilitó despliegue automático a producción: el pipeline propuesto es de **CI**.

## Cómo demostrarlo
1. Abrir **Actions** en el fork y seleccionar **AgriTech | Favio | CI y Seguridad**.
2. Abrir una ejecución de la rama `Favio/mejoras-ci-seguridad`.
3. Mostrar seis trabajos: calidad, HU, seguridad, integración, Playwright y aprobación.
4. Abrir los logs de Playwright, descargar `favio-evidencia-playwright` y enseñar sus capturas.
5. Explicar que la aprobación depende de que todos los trabajos anteriores terminen correctamente.

### Ejecución local
Desde `mvp`, con entorno virtual preparado:

```powershell
python -m pip install "Flask>=3,<4" "Pillow>=10" "pypdf>=4" "PyYAML>=6" "Jinja2>=3,<4"
python -m unittest discover -s tests -p "test_favio_security.py" -v
python -m unittest discover -s tests -p "test_ux_jira.py" -v
python smoke_test.py
# Playwright requiere instalar su paquete y navegador Chromium, además de tener Flask local activo.
python -m pip install playwright
python -m playwright install chromium
python -m unittest discover -s tests -p "test_favio_e2e.py" -v
```

Los resultados de GitHub Actions deben consultarse antes de afirmar que las pruebas pasaron. Playwright verifica un navegador real contra el servidor de CI, pero no comprueba inferencia YOLO real, cámara física ni el sitio público SIGIA. Una ejecución verde de CI no demuestra precisión del modelo YOLO ni reemplaza pruebas con cámara real y SIGIA.

## Pendiente
- Comprobar la ejecución real del nuevo workflow en GitHub Actions.
- Abrir Pull Request desde esta rama hacia `jjjoaquo/AgriTech:main`.
- Solicitar revisión de cambios al equipo antes de fusionar.


## Refuerzo adicional: cabeceras HTTP defensivas

Se implementaron en `mvp/accounts.py`:

- `X-Frame-Options: DENY`: impide cargar las pantallas de AgriTech dentro de un iframe de otro sitio, reduciendo el riesgo de **clickjacking**.
- `Content-Security-Policy: frame-ancestors 'none'`: defensa equivalente para navegadores modernos, limitada a la política de incrustación.
- `Strict-Transport-Security: max-age=31536000`: se emite **solo** si `AGRI_ENV=production`, para indicar al navegador que utilice HTTPS después de recibirla por una conexión HTTPS válida. No se usa `includeSubDomains` ni `preload`.

**Consideraciones:** estas cabeceras asumen que AgriTech se utiliza como sitio independiente; si más adelante debe integrarse en un iframe legítimo, será necesario revisar la política `DENY` / `frame-ancestors`. HSTS no sustituye la configuración HTTPS del hosting.

Se añadieron dos pruebas automatizadas en `mvp/tests/test_favio_security.py` que verifican las cabeceras públicas/privadas y el comportamiento de HSTS según el entorno. La ejecución CI correspondiente debe revisarse antes de afirmar que las pruebas están aprobadas.
