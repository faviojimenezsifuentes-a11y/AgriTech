# AgriTech

En Proyecto Final de Carrera III desarrollamos AgriTech, un MVP de inspección fitosanitaria para agricultores. El portal combina dos herramientas: ResNet-152 clasifica la fotografía completa entre 102 clases de plagas y YOLOv8 localiza plagas de espárrago mediante recuadros. La consulta a SIGIA–SENASA muestra una fuente externa para revisar productos autorizados; no valida automáticamente la predicción.

El MVP incluye registro e inicio de sesión, hallazgos privados por agricultor, dashboard, sesión de superadmin, una simulación 3D ilustrativa del cultivo y tres planes con cuotas. Las solicitudes de los planes Pro y Cooperativa se revisan manualmente; no existe pasarela de pago.

## Código y ejecución

La aplicación está en [`mvp/`](mvp/README.md). Para ejecutarla:

```powershell
cd mvp
python -m pip install -r requirements.txt
python app.py
```

El clasificador general necesita el archivo `mvp/models/best_resnet152_baseline.safetensors` entregado por Alonso. Por superar el límite de GitHub normal, el peso no está en el repositorio; consulte [`mvp/models/README.md`](mvp/models/README.md). Los pesos YOLO pequeños, las clases y los scripts de evaluación sí forman parte de la entrega. Las fotografías originales, los datos de usuarios y los secretos tampoco se publican en Git.

## Validación y sitio

```powershell
python mvp/smoke_test.py
node --check mvp/static/app.js
node --check mvp/static/general.js
node --check mvp/static/cultivo_3d.js
```

El sitio de demostración está en [esparragos.comextech.es](https://esparragos.comextech.es/). La simulación 3D muestra un escenario visual y no coordenadas medidas del lote. Las métricas de los modelos se documentan en `mvp/training_runs/` y en los informes técnicos de `mvp/`.

## Equipo y trazabilidad

Dividimos la integración por las historias asignadas en Jira a Michelle Montoya Rocca, Alonso Ortiz Rodríguez, Favio Sifuentes y Joaquín Callupe. Cada PR y commit nuevo debe empezar con la clave y el título de su historia, por ejemplo `SCRUM-11 HU2 – Identificar la plaga con YOLOv8: validar recuadros`. Conservamos la autoría original de los artefactos y registramos en cada PR el cambio efectivamente realizado.
