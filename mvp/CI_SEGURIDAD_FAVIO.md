# CI y seguridad — contribución Favio

## Objetivo
Pasar de una validación UX exclusivamente estructural a un pipeline con trabajos independientes de calidad, historias de usuario, seguridad e integración funcional, con una puerta final de aprobación. **Esta rama todavía no está integrada a `main`.**

## Rama
`Favio/mejoras-ci-seguridad` — fork: [faviojimenezsifuentes-a11y/AgriTech](https://github.com/faviojimenezsifuentes-a11y/AgriTech/tree/Favio/mejoras-ci-seguridad).

## Pipeline nuevo
Archivo `.github/workflows/favio-ci-seguridad.yml`:

1. **Calidad:** `compileall`, Flake8 (errores críticos) y sintaxis de tres archivos JavaScript.
2. **UX/UI:** nueve pruebas estructurales vinculadas a historias SCRUM-18/19/20/21/23/87/89 y comprobaciones adicionales de plantillas.
3. **Seguridad:** pruebas Flask de sesión, CSRF, autenticación, roles, aislamiento entre usuarios, encabezados de seguridad y redirecciones de login.
4. **Integración:** `smoke_test.py` verifica respuestas HTTP, detección simulada cuando faltan los pesos YOLO, registros, cuotas, controles de acceso y exportaciones.
5. **Puerta de calidad:** falla si cualquiera de los cuatro trabajos anteriores no termina con resultado `success`.

Los trabajos 1–4 pueden ejecutarse en paralelo; el quinto depende de todos ellos. Se guardan artefactos descargables para UX, seguridad e integración.

**Disparadores:** push a ramas `Favio/**`, Pull Requests dirigidos a `main` y ejecución manual.

## Mejoras concretas de seguridad
En `mvp/accounts.py` se reforzó la validación de `next` tras el inicio de sesión. Se impiden destinos ambiguos que utilicen doble barra, barra invertida y secuencias codificadas que puedan interpretarse como rutas externas. Las rutas relativas locales válidas continúan permitidas.

`mvp/tests/test_favio_security.py` incorpora pruebas reproducibles que usan SQLite temporal. Las pruebas no dependen de credenciales reales ni contactan SENASA.

## Qué no se modificó
No se modificaron modelos YOLO, datasets, pesos ni el proceso de inferencia. Tampoco se habilitó despliegue automático a producción: el pipeline propuesto es de **CI**.

## Cómo demostrarlo
1. Abrir **Actions** en el fork y seleccionar **AgriTech | Favio | CI y Seguridad**.
2. Abrir una ejecución de la rama `Favio/mejoras-ci-seguridad`.
3. Mostrar cinco trabajos: calidad, HU, seguridad, integración y aprobación.
4. Abrir logs de seguridad y descargar los artefactos.
5. Explicar que la aprobación depende de que todos los trabajos anteriores terminen correctamente.

### Ejecución local
Desde `mvp`, con entorno virtual preparado:

```powershell
python -m pip install "Flask>=3,<4" "Pillow>=10" "pypdf>=4" "PyYAML>=6" "Jinja2>=3,<4"
python -m unittest discover -s tests -p "test_favio_security.py" -v
python -m unittest discover -s tests -p "test_ux_jira.py" -v
python smoke_test.py
```

Los resultados de GitHub Actions deben consultarse antes de afirmar que las pruebas pasaron. Una ejecución verde de CI no demuestra precisión del modelo YOLO ni reemplaza pruebas con cámara real y SIGIA.

## Pendiente
- Comprobar la ejecución real del nuevo workflow en GitHub Actions.
- Abrir Pull Request desde esta rama hacia `jjjoaquo/AgriTech:main`.
- Solicitar revisión de cambios al equipo antes de fusionar.
