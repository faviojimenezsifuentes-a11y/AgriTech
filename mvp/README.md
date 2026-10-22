# MVP de inspección de plagas del espárrago

Aplicación Flask para inspectores de campo y supervisores agronómicos en Perú. YOLOv8n V2 analiza fotos o fotogramas de cámara y muestra recuadros, clases, confianza, conteos y velocidad observada. El usuario puede congelar la captura, corregir cajas, registrar hallazgos y consultar SIGIA de SENASA. La consulta a SENASA es una fuente pública externa y no valida por sí misma la identificación visual.

## Ejecutar en local

Desde esta carpeta, con Python 3.10 o superior:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Abrir `http://127.0.0.1:5000`. La cámara requiere permiso del navegador. Para verificar las funciones principales:

```powershell
python smoke_test.py
node --check static/app.js
```

## Modelos y resultados

- `models/esparragos_yolov8n_v2.pt` es el detector predeterminado del MVP. Es el peso V2 del equipo.
- `models/esparragos_yolo26n_semisupervisado.pt` es un experimento disponible solo para comparar fotografías. En 32 fotos externas reservadas detectó la clase esperada en 6, frente a 25 de V2; esta prueba no tiene cajas verificadas y no demuestra precisión en parcelas.
- El umbral inicial del detector V2 es 30 %. En la prueba de umbral a 640 px encontró la clase esperada en 24 de 32 fotos, frente a 21 con 45 %.
- Los reportes, parámetros y límites de la evaluación están en `training_runs/` y [MEJORA_MODELO.md](MEJORA_MODELO.md).

## Datos y procedencia

El repositorio conserva manifiestos, atribuciones y scripts de preparación, pero **no publica las fotos descargadas, etiquetas originales del compañero, datos de usuarios ni archivos de entrenamiento pesados**. El conjunto Roboflow v1 del colaborador tenía 99 originales y 297 variantes; su procedencia detallada aún necesita revisión. Las 24 fotos de espárrago de contexto no son imágenes negativas verificadas. Véanse los archivos `dataset_candidates/*/manifest.csv` y [ESTADO_PARA_PRESENTACION.md](ESTADO_PARA_PRESENTACION.md).

Los scripts de entrenamiento requieren los conjuntos originales en las rutas indicadas en [MEJORA_MODELO.md](MEJORA_MODELO.md). No se debe comparar un modelo con imágenes originales o variantes que ya usó para entrenar.

## Despliegue

La versión pública está en [https://esparragos.comextech.es/](https://esparragos.comextech.es/). La configuración del VPS está en [deploy/DEPLOY_VPS.md](deploy/DEPLOY_VPS.md). El sitio no requiere usuario ni contraseña; las fotos, ubicaciones e historial que se guarden serán visibles públicamente.
