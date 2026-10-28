# MVP de inspección de plagas en cultivos

Aplicación Flask para agricultores, inspectores de campo y supervisores agronómicos. La portada ofrece dos módulos:

- **Clasificación general:** ResNet‑152 de Alonso, 102 clases de plagas de distintos cultivos. Analiza la foto completa y muestra tres hipótesis; no genera cajas ni determina el cultivo. El peso instalado proviene del entrenamiento no balanceado. Su uso sigue siendo experimental hasta evaluarlo con un conjunto independiente.
- **Inspección de espárrago:** YOLOv8n V2 analiza fotos o fotogramas de cámara y muestra recuadros, clases, confianza, conteos y velocidad observada. El usuario puede congelar la captura, corregir cajas, registrar hallazgos y consultar SIGIA de SENASA para espárrago. Esta consulta es una fuente pública externa y no valida la identificación visual.

El checkpoint ResNet entregado por Alonso **ya está entrenado** para clasificar imágenes completas. La colección IP102 recibida contiene fotos organizadas por clase: esas etiquetas de imagen bastan para clasificación, pero no indican la posición de cada insecto. Para ampliar YOLO como detector a las ~45 000 fotos originales de IP102 habría que crear y revisar recuadros por objeto en cada imagen seleccionada. Esos recuadros son *bounding boxes*; una máscara pixel a pixel solo se requiere si se entrena segmentación, que no es el objetivo del módulo actual. Por eso el MVP conserva la clasificación general con ResNet y la detección con cajas de YOLO en el conjunto de espárrago ya anotado.

## Cuentas, dashboard y planes del MVP

- `/registro` crea una cuenta de agricultor con contraseña propia; `/login` abre su sesión. El análisis visual sigue disponible sin cuenta, pero guardar y consultar hallazgos requiere iniciar sesión. Cada cuenta solo ve sus propios registros, imágenes, resúmenes y exportaciones. Los registros anteriores a la migración quedan preservados en la base de datos y ocultos a las cuentas nuevas hasta que se les asigne un propietario de forma verificada.
- `/dashboard` muestra registros, confirmados, pendientes, cuota mensual, clases frecuentes de las últimas 100 inspecciones y acceso al historial. Estas cifras describen registros del usuario, no prevalencia de plagas en el cultivo.
- `/cultivo-3d` permite girar una escena proyectada de espárrago y ajustar etapa y puntos de revisión. Es una simulación visual ilustrativa; no representa coordenadas del lote ni calcula un diagnóstico.
- `/planes` ofrece **Explorar** (gratis, 10 hallazgos/mes), **Campo Pro** (200 hallazgos/mes y exportación de ejemplos confirmados) y **Cooperativa** (1000 hallazgos/mes y la misma exportación). El usuario solicita los dos últimos desde la página; el superadmin revisa y activa el plan. Son propuestas comerciales del MVP: todavía no hay precios definitivos, pasarela de pago ni facturación automática.
- `/admin` es privado para el superadmin y permite revisar usuarios, cantidad de hallazgos y solicitudes de planes. Para crear el primer administrador se usa `python -m flask --app app bootstrap-admin correo@dominio.es`, que emite un enlace de activación de un solo uso válido 24 horas. No hay contraseñas compartidas o predeterminadas.

En producción se debe establecer `AGRI_ENV=production` y una clave aleatoria persistente `AGRI_SECRET_KEY`. Las sesiones usan cookies HttpOnly, SameSite=Lax y Secure con HTTPS; formularios y guardado de hallazgos usan token CSRF. El archivo SQLite de producción y su respaldo deben permanecer fuera de Git.

## Ejecutar en local

Desde esta carpeta, con Python 3.10 o superior:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Abrir `http://127.0.0.1:5000` para elegir un módulo. El peso ResNet no se guarda en Git: colocar `best_resnet152_baseline.safetensors` en `models/` o definir `AGRI_RESNET_WEIGHTS` con su ruta absoluta. Se puede convertir el checkpoint original `.pth` mediante [convert_resnet_checkpoint.py](convert_resnet_checkpoint.py). La cámara YOLO requiere permiso del navegador. Para verificar las funciones principales:

```powershell
python smoke_test.py
python -m unittest discover -s tests -v
node --check static/app.js
node --check static/general.js
node --check static/cultivo_3d.js
```

## Modelos y resultados

- `models/classes_ip102.txt` contiene las 102 etiquetas que proporcionó Alonso. `models/best_resnet152_baseline.safetensors` deriva directamente del `.pth` entregado, sin el estado del optimizador; pesa aproximadamente 234 MB y no se publica en Git. Alonso confirmó que es el peso no balanceado y que el tamaño de entrada es 256 × 256 px. El checkpoint informa F1 macro de validación 0,6365 con `epoch=7`, pero no incluye métricas de prueba. Véase [CLASIFICADOR_GENERAL.md](CLASIFICADOR_GENERAL.md).
- El conjunto balanceado con StyleGAN2 se recibió como ZIP de imágenes. Para entrenar y comparar un candidato sin reemplazar prematuramente el peso publicado, véase [IP102_ENTRENAMIENTO.md](IP102_ENTRENAMIENTO.md) y el [cuaderno listo para Colab](colab_entrenar_ip102.ipynb).
- `models/esparragos_yolov8n_v2.pt` es el detector predeterminado del MVP. Es el peso V2 del equipo.
- `models/esparragos_yolo26n_semisupervisado.pt` es un experimento disponible solo para comparar fotografías. En 32 fotos externas reservadas detectó la clase esperada en 6, frente a 25 de V2; esta prueba no tiene cajas verificadas y no demuestra precisión en parcelas.
- El umbral inicial del detector V2 es 30 %. En la prueba de umbral a 640 px encontró la clase esperada en 24 de 32 fotos, frente a 21 con 45 %.
- Los reportes, parámetros y límites de la evaluación están en `training_runs/` y [MEJORA_MODELO.md](MEJORA_MODELO.md).

## Datos y procedencia

El repositorio conserva manifiestos, atribuciones y scripts de preparación, pero **no publica las fotos descargadas, etiquetas originales del compañero, datos de usuarios ni archivos de entrenamiento pesados**. El conjunto Roboflow v1 del colaborador tenía 99 originales y 297 variantes; su procedencia detallada aún necesita revisión. Las 24 fotos de espárrago de contexto no son imágenes negativas verificadas. Véanse los archivos `dataset_candidates/*/manifest.csv` y [ESTADO_PARA_PRESENTACION.md](ESTADO_PARA_PRESENTACION.md).

Los scripts de entrenamiento requieren los conjuntos originales en las rutas indicadas en [MEJORA_MODELO.md](MEJORA_MODELO.md). No se debe comparar un modelo con imágenes originales o variantes que ya usó para entrenar.

## Despliegue

La versión pública está en [https://esparragos.comextech.es/](https://esparragos.comextech.es/). La configuración del VPS está en [deploy/DEPLOY_VPS.md](deploy/DEPLOY_VPS.md). La portada y el análisis se abren sin cuenta. Los hallazgos guardados y sus imágenes son privados para el agricultor autenticado.
