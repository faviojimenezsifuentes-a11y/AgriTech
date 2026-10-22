# Mejoras propuestas para el modelo de clasificación de imágenes

## 1. Validación de clases
Implementar validaciones para garantizar que las 102 clases estén correctamente mapeadas en los conjuntos de entrenamiento, validación y prueba, evitando inconsistencias en las etiquetas.

## 2. Optimización del entrenamiento
Mejorar la compatibilidad del entrenamiento con CPU y GPU mediante una configuración automática de la precisión mixta, optimizando el uso de los recursos disponibles.

## 3. Recuperación del entrenamiento
Ampliar el sistema de checkpoints para guardar el estado del modelo, el optimizador, el scheduler y la época actual, permitiendo reanudar el entrenamiento ante interrupciones.

## 4. Evaluación detallada del modelo
Incorporar un reporte de clasificación por clase que incluya precisión, recall, F1-score y cantidad de imágenes evaluadas, para identificar las categorías con menor rendimiento.

## 5. Tratamiento del desbalance de clases
Evaluar el uso de pesos por clase en la función de pérdida para reducir el impacto del desbalance de imágenes y mejorar el rendimiento en categorías con menor representación.

## 6. Reproducibilidad de resultados
Establecer semillas aleatorias y registrar los hiperparámetros y las versiones de las librerías utilizadas, facilitando la repetición y comparación de experimentos.

## Objetivo
Estas mejoras buscan aumentar la confiabilidad, reproducibilidad y capacidad de evaluación del modelo de clasificación de imágenes basado en ResNet-152 y PyTorch.
