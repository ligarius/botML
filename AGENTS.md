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



**Regla:**


---

## Convenciones de Código

Python 3.11+

scikit-learn, Optuna para optimización y modelos básicos (o PyTorch si vas a escalar a deep learning).

SQLAlchemy/SQLite para almacenamiento persistente.

Websocket/REST API para conexión con Binance y el dashboard.

Streamlit avanzado para dashboard, o migrar a Dash/Plotly si quieres mayor control.

pytest para tests automáticos.

---

Características clave a implementar
1. Robustez y Operación 24/7
Watchdog integrado: monitoriza el proceso, detecta cuelgues o errores, reinicia automáticamente si hay fallo.

Manejo avanzado de errores y reconexión automática en todas las conexiones con Binance.

Persistencia de estado: el bot debe guardar su estado (último modelo, posiciones, histórico de señales, parámetros) para poder recuperarse exactamente donde quedó después de un crash o reinicio.

2. Entrenamiento y Evolución Autónoma
Entrenamiento automático y periódico del modelo (por tiempo, cantidad de trades o performance).

Optimización de hiperparámetros: usa Optuna, Hyperopt o similar para que el bot busque solo los mejores parámetros (no solo GridSearch).

Recompensa/castigo de estrategias: guarda histórico de performance y ajusta pesos/selección automática de modelos según su éxito real en producción.

Selección adaptativa de features e intervalos: el bot debe poder probar distintos intervalos y features, y quedarse con los que mejor performance entreguen de forma autónoma.

3. Especialización Intradía y Velas Pequeñas
Datafeed flexible: descarga y actualiza datos en el intervalo más pequeño que permita Binance (ideal 1m o menor si es posible), configurable desde YAML y modificable en caliente por el propio bot.

Gestión inteligente de históricos: carga incremental, sin volver a descargar lo ya obtenido, con almacenamiento eficiente (por ejemplo, en SQLite).

4. Live Trading y Simulación Realista
Modo “live” y “simulado” usando exactamente la misma lógica y flujo.

Simulación realista: incluye comisiones, slippage, delays y fills parciales, igual que en condiciones reales de Binance.

Gestión de capital y posiciones: controla balance, sizing dinámico y control de riesgo por operación y global.

Chequeo y control de órdenes: verifica fills, estado de órdenes y saldos antes de cada acción.

5. Dashboard en Tiempo Real
Dashboard web robusto (Streamlit, Dash o similar) mostrando:

PnL acumulado y por símbolo

ROI, drawdown, winrate, Sharpe Ratio, y demás KPIs clave

Estadísticas de señales, operaciones abiertas/cerradas, errores y alertas

Evolución de hiperparámetros, selección de features, y modelo actual usado

Logs y eventos críticos del sistema

Historial de decisiones y operaciones consultable en el dashboard

6. Logging y Auditoría
Logging estructurado (idealmente JSON o similar) y simple para humanos.

Logs de decisiones: cada señal, motivo de entrada/salida, parámetros, performance, anomalías, etc.

Alertas automáticas por Telegram/email para eventos críticos: caídas, errores API, drawdown extremo, fill anómalo, etc.

7. Seguridad y Autodefensa
Límites de pérdidas y drawdown: el bot debe auto-desactivarse o pausar si se supera un drawdown, una pérdida máxima diaria o un umbral de riesgo predeterminado.

Verificación de saldos y estado de la cuenta antes de ejecutar operaciones.

8. Modularidad y Escalabilidad
Código desacoplado por módulos: feed de datos, modelo, ejecución, backtest, dashboard, logging, watchdog, etc., cada uno en su package/carpeta.

Fácil de testear y actualizar cada módulo sin romper el sistema completo.

Listo para agregar nuevos modelos, indicadores, exchanges o estrategias en el futuro.

Extras para operación real:
Backtest con visualización y comparación automática de diferentes estrategias, modelos, y periodos.

Capacidad de operar múltiples símbolos, cada uno con lógica y modelo propio si es necesario.

Herramientas de análisis automático de errores y eventos para aprender del pasado.



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
