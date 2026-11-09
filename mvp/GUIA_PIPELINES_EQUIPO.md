# Guía del equipo — GitHub Actions: calidad, UX y seguridad

## Qué compartimos

El workflow `.github/workflows/favio-ci-seguridad.yml` está preparado para que **todos los integrantes** puedan validar cambios con GitHub Actions sin copiar el archivo entero. Este pipeline no instala ni entrena pesos YOLO. Seis jobs:

1. **Calidad y sintaxis:** compila Python, Flake8 para errores críticos y `node --check`.
2. **Historias de usuario / UX:** pruebas `test_ux_jira.py`.
3. **Seguridad:** pruebas de autenticación, roles, sesiones, CSRF, redirecciones y cabeceras HTTP.
4. **Integración Flask:** `smoke_test.py`, usando un detector simulado cuando no existen pesos YOLO.
5. **E2E con Playwright:** navega por la aplicación con Chromium y guarda capturas.
6. **Puerta de calidad:** depende de los otros cinco; falla si alguno falla o es cancelado.

También se conservan **artefactos** de UX, seguridad, integración y Playwright para la sustentación.

## Requisito antes de usarlo en el equipo

Primero se debe **revisar y fusionar el PR** de la rama `Favio/mejoras-ci-seguridad` hacia el repositorio original `jjjoaquo/AgriTech:main`. Mientras esté solo en el fork de Favio, los compañeros **no verán el workflow en Actions del repositorio principal**. La fusión requiere revisión y aprobación del equipo.

## Opción A: cada integrante usa el pipeline compartido automáticamente

1. Actualizar la rama local `main` desde el repositorio original.
2. Crear una rama de trabajo propia, por ejemplo `feature/david-mejora-login` o `feature/michelle-registros`.
3. Realizar cambios y añadir pruebas para la HU asignada.
4. Crear un commit y hacer `git push` de la rama.
5. En el repositorio original, ir a **Actions → AgriTech | Favio | CI y Seguridad**. La rama aparece entre las ejecuciones.
6. Abrir una ejecución: revisar jobs, errores y artefactos. Corregir los problemas reales y repetir con otro commit.
7. Crear un Pull Request hacia `main`. El workflow también se dispara para ese PR.

**Nota de costo:** la configuración `push` en todas las ramas ejecuta pruebas por cada push; los PR hacia `main` pueden producir una segunda ejecución de validación. Evitar commits innecesarios; el repositorio puede ajustar los disparadores si hay demasiadas ejecuciones. `cancel-in-progress: true` prioriza los commits recientes dentro de la misma referencia.

## Opción B: cada integrante crea su propio pipeline especializado

El workflow de Favio también incluye `workflow_call`. Una vez integrado en `main`, otro colaborador puede crear `.github/workflows/ci-michelle.yml` (o equivalente) con:

```yaml
name: CI de Michelle + validaciones compartidas
on:
  pull_request:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  validacion-compartida:
    uses: jjjoaquo/AgriTech/.github/workflows/favio-ci-seguridad.yml@main
```

Esto reutiliza **todos los jobs** del workflow común sin duplicar el código YAML. Cada integrante puede complementar con trabajos adicionales de su HU. **La reutilización solo funcionará cuando el archivo exista en `main` del repo original**.

> Alternativa: no es obligatorio crear un nuevo workflow. Para la mayoría del equipo basta la **Opción A**, que evita la duplicación de ejecuciones y mantenimiento.

## Cómo agregar nuevas pruebas según las HU

- Nuevas pruebas de interfaz: archivos `mvp/tests/test_*.py` y/o Playwright.
- Pruebas funcionales del backend: `unittest` con Flask test client y una base de datos temporal.
- Cuando se agregue una suite propia, actualizar el job correspondiente o crear otro job en un workflow propio.
- No agregar tokens, claves, contraseñas, pesos de IA o archivos SQLite reales al repositorio.
- No deshabilitar pruebas para que salgan verdes. Un fallo debe bloquear la puerta de calidad y quedar registrado.
- No afirmar que las pruebas de navegador con servidor local validan cámara física, disponibilidad real de SIGIA ni precisión del modelo YOLO.

## Cómo compartir evidencias con el docente

1. Abrir **Actions** y filtrar la ejecución por rama o Pull Request.
2. Abrir el gráfico de jobs y mostrar el trabajo de seguridad, el de Playwright y la puerta de calidad.
3. En la parte inferior de la ejecución, descargar los **Artifacts**: `favio-evidencia-ux`, `favio-evidencia-seguridad`, `favio-evidencia-integracion`, `favio-evidencia-playwright`.
4. En Jira, enlazar la HU y su Pull Request. Utilizar el identificador `SCRUM-XXX` en los títulos de commits futuros cuando corresponda.
5. Mostrar capturas de pantalla y el resultado de las pruebas junto al PR que incorporó la HU.

## Permisos

- Para **ver** pipelines de un repositorio público normalmente no se necesita acceso de escritura.
- Para hacer push a una rama del repositorio original se necesita permiso de colaboración. Si no lo tienen, cada integrante puede trabajar en su fork y enviar PR.
- Para ejecutar manualmente `workflow_dispatch` en el repositorio del equipo se necesita acceso de escritura y el workflow disponible en la rama principal (si GitHub no muestra `Run workflow`, revisar permisos y configuración de Actions).
- La configuración de **branch protection / rulesets** para exigir la puerta de calidad antes de fusionar es una decisión del propietario o administrador; no se activa solo por agregar el YAML.

## Criterio de término

Una HU se considera lista para revisión cuando su rama y PR muestran la ejecución correcta de las pruebas aplicables, sin saltos de seguridad ni falsas aprobaciones. El Merge requiere el visto bueno del equipo y, si el administrador lo configura, la comprobación obligatoria **6. Puerta de calidad**.
