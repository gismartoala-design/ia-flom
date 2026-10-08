# Aula IA · Flask + JSON

Aplicación web pequeña para conversar con un motor local de preguntas y respuestas y entrenarlo con ejemplos. Incluye **12 preguntas/respuestas iniciales**. El modelo usa TF-IDF de caracteres y similitud coseno: **no es una IA generativa ni aprende automáticamente de las conversaciones**. Aprende cuando un administrador guarda ejemplos nuevos o actualizados.

## Instalación

Requiere Python 3.10 o superior.

```bash
cd flask_modelo_json
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Iniciar

Para pruebas locales, define una clave de administrador propia:

```bash
# Linux/macOS:
export ADMIN_KEY='cambia-esta-clave'
export SECRET_KEY='frase-larga-aleatoria'
python app.py
```

En PowerShell:

```powershell
$env:ADMIN_KEY="cambia-esta-clave"
$env:SECRET_KEY="frase-larga-aleatoria"
python app.py
```

Abre `http://127.0.0.1:5000`.

En ausencia de la variable `ADMIN_KEY`, se usa la clave de demostración `demo123`, **solo apta para pruebas locales**.

## Uso

1. **Conversar:** pregunta algo y el sistema buscará la respuesta más similar.
2. **Enseñar:** entra con tu clave de administrador y agrega una pregunta y su respuesta. Si ya existe una pregunta idéntica (ignorando mayúsculas), se actualiza.
3. **Base de datos:** revisa las preguntas almacenadas, con permisos de administrador.

Los cambios se guardan en `data/conocimiento.json` y generan automáticamente `data/modelo.joblib`. El índice se recompone a partir de los datos disponibles. Puedes editar el JSON y reiniciar el servicio para reconstruirlo.

## API

- `GET /api/estado` — estado del motor.
- `POST /api/chat` — `{ "pregunta": "hola" }`.
- `POST /api/login` — `{ "clave": "..." }`.
- `POST /api/logout` — cerrar sesión.
- `GET /api/ejemplos` — base completa (administrador).
- `POST /api/aprender` — `{ "pregunta": "...", "respuesta": "..." }` (administrador).
- `POST /api/entrenar` — actualizar índice (administrador).

## Archivos

- `app.py`: web y endpoints Flask.
- `modelo.py`: entrenamiento y respuestas.
- `data/conocimiento.json`: conocimientos iniciales editables.
- `templates/index.html`: interfaz web.
- `static/`: estilos y JavaScript.
- `tests/test_app.py`: comprobaciones principales.

## Limitaciones y seguridad

Este proyecto es una demostración **para ejecución local**. No es adecuado para Internet ni datos sensibles sin implementar usuarios reales, hashing de contraseñas, controles CSRF, rate limiting, HTTPS, logs y almacenamiento transaccional con base de datos. El archivo `.joblib` solo debe generarse y cargarse desde datos confiables. Nunca cargues modelos `.joblib` enviados por usuarios. El sistema no obtiene información de Internet ni cambia el conocimiento sin autorización.
