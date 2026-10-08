# Aula IA · Flask + JSON

Aplicación web pequeña para conversar con un motor local de preguntas y respuestas y entrenarlo con ejemplos. Incluye **67 preguntas/respuestas iniciales** sobre el asistente mismo, el aula virtual (clases, tareas, asistencia, calificaciones) y nociones técnicas (Flask, Python, JSON, TF-IDF). El modelo usa TF-IDF de caracteres y similitud coseno: **no es una IA generativa ni aprende automáticamente de las conversaciones**. Aprende cuando un administrador guarda ejemplos nuevos o actualizados.

### Novedad: aprendizaje asistido desde preguntas reales

Cada vez que alguien hace una pregunta que el asistente no sabe responder, queda registrada en `data/pendientes.json` junto con el número de veces que se repitió. Desde la pestaña **Base de datos → Preguntas sin responder**, el administrador puede:

- Pulsar **Enseñar** para llevar esa pregunta directo al formulario de enseñanza.
- Pulsar **Descartar** si no quiere agregarla a la base.

Así el asistente "crece" con el uso real, pero siempre bajo revisión humana — nunca se auto-modifica sin que un administrador lo apruebe.

## Instalación

Requiere Python 3.10 o superior.

```bash
cd flask_modelo_json
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
cd flask_modelo_json
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Levantar el proyecto

Para pruebas locales, define una clave de administrador y una clave de sesión propias:

```bash
# Linux/macOS:
source .venv/bin/activate
export ADMIN_KEY='cambia-esta-clave'
export SECRET_KEY='frase-larga-aleatoria'
python app.py
```

```powershell
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
$env:ADMIN_KEY="cambia-esta-clave"
$env:SECRET_KEY="frase-larga-aleatoria"
python app.py
```

Abre `http://127.0.0.1:5000`. En ausencia de la variable `ADMIN_KEY`, se usa la clave de demostración `demo123`, **solo apta para pruebas locales**.

## Ejecutar las pruebas

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```

## Uso

1. **Conversar:** pregunta algo y el sistema buscará la respuesta más similar. Si no la conoce, la guarda como pendiente.
2. **Enseñar:** entra con tu clave de administrador y agrega una pregunta y su respuesta. Si ya existe una pregunta idéntica (ignorando mayúsculas), se actualiza.
3. **Base de datos:** revisa las preguntas almacenadas y las preguntas sin responder, con permisos de administrador.

Los cambios se guardan en `data/conocimiento.json` y generan automáticamente `data/modelo.joblib`. El índice se recompone a partir de los datos disponibles. Puedes editar el JSON y reiniciar el servicio para reconstruirlo, o agregar tus propios temas y volver a entrenar.

## API

- `GET /api/estado` — estado del motor.
- `POST /api/chat` — `{ "pregunta": "hola" }`.
- `POST /api/login` — `{ "clave": "..." }`.
- `POST /api/logout` — cerrar sesión.
- `GET /api/ejemplos` — base completa (administrador).
- `POST /api/aprender` — `{ "pregunta": "...", "respuesta": "..." }` (administrador).
- `POST /api/entrenar` — actualizar índice (administrador).
- `GET /api/pendientes` — preguntas sin responder, ordenadas por frecuencia (administrador).
- `POST /api/pendientes/descartar` — `{ "pregunta": "..." }`, elimina una pregunta pendiente (administrador).

## Archivos

- `app.py`: web y endpoints Flask.
- `modelo.py`: entrenamiento, respuestas y registro de preguntas sin responder.
- `data/conocimiento.json`: conocimientos iniciales editables.
- `data/pendientes.json`: preguntas sin responder (se genera automáticamente con el uso).
- `templates/index.html`: interfaz web.
- `static/`: estilos y JavaScript.
- `tests/test_app.py`: comprobaciones principales.

## Ampliar la base de conocimientos

Puedes agregar más temas de dos formas:

1. **Desde la interfaz:** pestaña Enseñar (requiere clave de administrador).
2. **Editando el JSON:** agrega objetos `{"pregunta": "...", "respuesta": "..."}` dentro de la lista `ejemplos` en `data/conocimiento.json` y reinicia el servidor (o llama a `POST /api/entrenar`) para que se reconstruya el índice.

El umbral de confianza (qué tan parecida debe ser una pregunta para considerarse "conocida") está en `modelo.py`, función `responder()`, parámetro `umbral` (por defecto `0.40`). Súbelo si notas falsos positivos (respuestas incorrectas con confianza alta) o bájalo si el asistente es demasiado estricto.

## Limitaciones y seguridad

Este proyecto es una demostración **para ejecución local**. No es adecuado para Internet ni datos sensibles sin implementar usuarios reales, hashing de contraseñas, controles CSRF, rate limiting, HTTPS, logs y almacenamiento transaccional con base de datos. El archivo `.joblib` solo debe generarse y cargarse desde datos confiables. Nunca cargues modelos `.joblib` enviados por usuarios. El sistema no obtiene información de Internet ni cambia el conocimiento sin autorización: las preguntas sin responder solo se registran para revisión humana, nunca se agregan solas a la base.
