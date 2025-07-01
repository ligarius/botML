Aquí tienes un ejemplo profesional de **AGENTS.md** pensado para un bot de trading automatizado, orientado a operación intradía, autoaprendizaje y con objetivos de rentabilidad claros. Este documento define convenciones, flujos y expectativas para humanos y agentes IA, y deja claro el estándar del proyecto.

---

# AGENTS.md

## Propósito

Este archivo centraliza las normas y recomendaciones para el desarrollo y operación del bot de trading automático de este repositorio. Está diseñado para que tanto personas como agentes automatizados (scripts, IA, CI/CD, bots de control) mantengan la coherencia, calidad y seguridad del proyecto.

---

## Objetivos del Bot

* **Automatización total**: El bot debe operar de forma 100% autónoma, incluyendo descarga de datos, entrenamiento, optimización, generación y ejecución de señales.
* **Enfoque intradía**: Todas las estrategias, datos y evaluaciones deben ser de timeframe menor o igual a 1 día (preferentemente 1-15 minutos).
* **Rentabilidad mínima**: El sistema debe buscar un ROI mínimo de 0,5% neto diario, aplicando lógica de defensa de capital y adaptación constante de parámetros.
* **Evolución continua**: Se espera que el bot aprenda, valide y reentrene modelos en ciclos frecuentes (mínimo cada 15-60 minutos).

---

## Estructura de Carpetas y Archivos

* **/botml/** – Lógica principal, features, modelos ML, procesamiento.
* **/backtest/** – Motor de simulación histórica, métricas, validación.
* **/tests/** – Pruebas unitarias y de integración.
* **config.yaml** – Configuración principal (usar variables de entorno para secretos).
* **orchestrator.py** – Loop maestro: orquesta descarga, entrenamiento, evaluación.
* **live\_trading.py** – Solo ejecución real; debe poder desactivarse en modo research.

**Regla:**
*Coloca cualquier nueva funcionalidad según su propósito: lógica core en `/botml/`, backtesting en `/backtest/`, pruebas en `/tests/`.*

---

## Convenciones de Código

* **Python ≥ 3.9.**
* **Style Guide:** PEP8, docstrings obligatorios en módulos, clases y funciones públicas.
* **Idioma:** Comentarios y docstrings en inglés.
* **No expongas datos sensibles:** No hardcodear claves, no loggear secrets, usar env vars.
* **Nomenclatura:** snake\_case para funciones/variables, CamelCase para clases.
* **Funcionalidad aislada:** Cada función debe tener una única responsabilidad.

---

## Flujo de Automatización

1. **Descarga y actualización de datos:** Cada ciclo, solo descargar nuevos datos.
2. **Procesamiento y features:** Calcular indicadores relevantes y actualizarlos.
3. **Entrenamiento ML:** Reentrenar modelo en cada ciclo (o usar lógica incremental).
4. **Generación y validación de señales:** Aplicar backtest automático en cada iteración.
5. **Ejecución (si aplica):** Solo en modo producción, ejecutar órdenes reales bajo control de riesgo.
6. **Auditoría:** Guardar todas las señales, métricas y logs para revisión posterior.

---

## Pruebas y Validación

* **Pull Requests:** Todo cambio debe incluir pruebas unitarias si modifica la lógica de features, modelos, riesgo o ejecución.
* **Ejecución de tests:**

  ```
  pytest --maxfail=1 --disable-warnings
  ```
* **Revisión de logs:** No debe haber errores críticos ni warnings no justificados en los logs.
* **Backtest:** Al menos una simulación sobre los últimos 7 días, buscando ROI > 0,5% diario antes de permitir despliegue a producción.

---

## Seguridad

* **No subir secrets a git.** Usa `.env` o variables de entorno para credenciales.
* **Revisa dependencias:** Mantén `requirements.txt` actualizado y libre de vulnerabilidades conocidas.
* **Logs limpios:** Filtra cualquier información sensible antes de loggear.

---

## Mantenimiento y Escalabilidad

* **Actualiza AGENTS.md** cada vez que se agregue una convención, carpeta o funcionalidad relevante.
* **Deja TODO/FIXME claros:** Usa etiquetas en el código para puntos críticos pendientes, pero nunca en producción.
* **Contribución:** Incluye en cada PR una breve justificación de cambios y cómo fueron probados.

---

## Contacto y Soporte

Para dudas sobre estándares, estructuras o automatización, contacta al mantenedor principal o abre un issue con el tag `AGENTS-QUESTION`.

---

¿Quieres que te genere el archivo para adjuntarlo directamente a tu repositorio? ¿O deseas personalizar alguna sección más en detalle?
