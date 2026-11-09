# HU — Detectar regresiones de permisos antes de desplegar

**Historia:** Como agricultor, quiero que cada cambio en AgriTech verifique que mis hallazgos siguen siendo privados, para que una ruta nueva o modificada no permita a otro usuario acceder a mis fotos.

## Alcance realizado

El backend actual ya usa `owner_id` para filtrar el listado de hallazgos, las fotografías y la exportación. Esta HU agrega **pruebas de regresión concretas**, sin cambiar permisos existentes, para evitar que futuras modificaciones eliminen estas restricciones.

Suite: `mvp/tests/test_regresion_permisos.py`.

Pruebas:
1. Dos agricultores independientes solo ven sus propios hallazgos e identificadores en `GET /api/hallazgos`.
2. Cada uno puede abrir su foto JPEG, pero no la del otro al modificar directamente la URL `/api/hallazgos/<id>/imagen`.
3. Un visitante sin sesión no puede listar hallazgos ni abrir fotos.
4. Las fotografías de registros sin propietario (datos legados) no quedan accesibles por defecto.
5. Una exportación autorizada `GET /api/dataset/export` solo contiene fotografías del usuario que la solicitó.

Todas las pruebas usan SQLite y archivos JPEG temporales; no leen datos reales, no usan modelos YOLO y no requieren servicios externos. La prueba de exportación habilita `pro` solamente en la base de datos temporal.

## Ejecución local

Desde la raíz del repositorio, con las dependencias de Flask instaladas:

```bash
python -m unittest discover -s mvp/tests -p 'test_regresion_permisos.py' -v
```

## CI y criterio de aceptación

El job **3. Pruebas de seguridad** ejecuta la suite existente y después esta nueva suite. Si falla una de las pruebas de permisos, el job falla y **6. Puerta de calidad** impide considerar la ejecución exitosa. Los resultados se adjuntan en el artefacto `favio-evidencia-seguridad`, archivo `regresion-permisos.txt`.

Antes de dar por concluida la HU, comprobar en GitHub Actions una ejecución verde del PR y descargar su evidencia. El merge depende de la revisión del equipo. Para convertir la puerta de calidad en un bloqueo obligatorio de merge, el administrador debe configurar el check como requisito en las reglas de la rama `main`.

## Criterios de aceptación verificados por las pruebas

- A solo ve hallazgos de A y B solo los de B.
- Las URLs de imágenes del otro agricultor responden 403/404.
- Las rutas privadas no permiten acceso anónimo.
- Los hallazgos sin propietario no se exponen.
- El ZIP de exportación no incluye fotografías ajenas.
- La verificación se ejecuta ante cada PR a `main`.

Esta suite se limita a las rutas y condiciones cubiertas; no sustituye una auditoría de seguridad ni un análisis automático de endpoints futuros.
