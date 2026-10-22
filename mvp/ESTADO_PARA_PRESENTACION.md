# Estado del MVP para la presentación

## Qué se puede demostrar hoy

El público objetivo son inspectores de campo y supervisores agronómicos de espárrago en Perú. La aplicación permite analizar una foto o la cámara con YOLOv8n V2, mostrar recuadros, clase, confianza, conteo, latencia y FPS observado, y generar una alerta cuando una detección persiste en varios fotogramas. El supervisor puede congelar la imagen, corregir las cajas, confirmar un hallazgo y exportar los ejemplos revisados. SIGIA de SENASA se consulta desde la pantalla como fuente pública externa.

Hay **24 fotos descargadas de *Asparagus officinalis*** en `dataset_candidates/asparagus_context/images/`. Su `manifest.csv` registra observación, autor, licencia y enlace de origen. Son fotos de contexto para revisar cómo responde el detector ante imágenes del cultivo. **No se ha verificado si contienen o no las plagas objetivo**; por ello no son un conjunto de negativos ni sirven para medir falsos positivos. Hay además 96 fotos de las especies objetivo, mayormente sobre otros hospederos, en `dataset_candidates/inaturalist/`.

## Resultado que debe mostrarse sin exagerar

Se entrenó un YOLO26n experimental y se comparó con V2 en 32 fotos externas reservadas: V2 detectó la clase esperada en 25; YOLO26n, en 6. Esa prueba carece de cajas revisadas y no acredita desempeño sobre espárrago peruano. Por eso V2 sigue en la cámara y YOLO26n se ofrece solo para comparar fotos. El umbral inicial de V2 se eligió en fotos de desarrollo y se contrastó en las 32 reservadas: 24/32 a 30 % frente a 21/32 a 45 %, ambos a 640 px. Los detalles están en `MEJORA_MODELO.md`.

## Correcciones pendientes antes de afirmar validación de campo

**Informe académico:** `Informe_Final_Proyecto_Plagas.docx` todavía describe como paso pendiente cambiar el peso web de V1-2 a V2, aunque el MVP actual ya usa V2. Tampoco documenta la cámara en tiempo real, la revisión de cajas, las 24 fotos de espárrago ni el experimento YOLO26n. Antes de entregar el informe, actualizar esas secciones y distinguir las métricas internas de V1-2/V2 de la prueba externa reciente. La frase que atribuye un rendimiento cercano al 98 % no representa desempeño validado en parcelas nuevas.

1. **Prioridad máxima — datos del cultivo:** fotografiar plagas y plantas sin plagas en parcelas de espárrago de Perú, con permiso del productor. Anotar fecha, sector, etapa del cultivo, dispositivo y condiciones de luz. Buscar expresamente larvas de *Prodiplosis longifila*, ausentes de la prueba externa actual.
2. **Etiquetas verificadas:** una persona competente debe identificar especie y etapa, dibujar o corregir cada caja y marcar imágenes sin plagas objetivo. Las pseudoetiquetas de iNaturalist no bastan para validar o reentrenar la versión final.
3. **Prueba independiente:** separar las fotos por parcela o sesión antes de entrenar, reservar un conjunto que no se use para ajustar modelo o umbral y medir mAP por clase, omisiones, alertas incorrectas y FPS en el equipo de presentación.
4. **Procedencia de las fotos originales:** recuperar con el compañero las fuentes y permisos de las imágenes reunidas para Roboflow. La licencia declarada del proyecto no confirma por sí sola la licencia de cada foto original.
5. **Ensayo en el lugar de exposición:** probar cámara, iluminación, red, navegador Chrome y consulta SIGIA. La consulta depende del portal público y puede fallar si cambia o no responde; llevar capturas y fotos locales de ejemplo para demostrar el flujo sin internet.

## Guion breve de demostración

1. Abrir `http://127.0.0.1:5000`, explicar que el usuario es un inspector o supervisor y que V2 es el detector activo.
2. Subir una foto con plaga conocida y mostrar recuadro, clase, confianza, conteo y umbral. Después abrir la cámara para mostrar la superposición y el FPS observado en ese equipo.
3. Congelar un fotograma, corregir una caja, registrar sector y confirmar el hallazgo. Mostrar el historial y exportar etiquetas revisadas.
4. Consultar SIGIA para una clase detectada y explicar que SENASA aporta información fitosanitaria, mientras que la identificación visual queda sujeta a revisión humana.
5. Mostrar la comparación V2/YOLO26n y las fotos de espárrago como contexto. Explicar por qué la siguiente etapa requiere imágenes propias del cultivo con cajas verificadas.

El MVP **está listo para una demostración académica del flujo**. Aún **no está validado como sistema de diagnóstico de campo** ni hay evidencia para reemplazar V2 por YOLO26n.
