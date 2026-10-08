import os
from functools import wraps
from flask import Flask, jsonify, render_template, request, session
from modelo import agregar, descartar_pendiente, entrenar, leer, leer_pendientes, responder

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "solo-desarrollo-cambiar-en-produccion")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "demo123")


def autorizacion(f):
    @wraps(f)
    def interior(*args, **kwargs):
        if not session.get("admin"):
            return jsonify(error="Acceso restringido al administrador."), 403
        return f(*args, **kwargs)
    return interior


@app.get("/")
def inicio():
    return render_template("index.html")


@app.get("/api/estado")
def estado():
    return jsonify(ejemplos=len(leer()), admin=bool(session.get("admin")), tipo="TF-IDF local basado en ejemplos")


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    pregunta = str(data.get("pregunta", "")).strip()
    if not pregunta or len(pregunta) > 500:
        return jsonify(error="Escribe una pregunta entre 1 y 500 caracteres."), 400
    return jsonify(responder(pregunta))


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    if str(data.get("clave", "")) != ADMIN_KEY:
        return jsonify(error="Clave incorrecta"), 401
    session["admin"] = True
    return jsonify(ok=True)


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/ejemplos")
@autorizacion
def ejemplos():
    return jsonify(ejemplos=leer())


@app.post("/api/entrenar")
@autorizacion
def actualizar_modelo():
    return jsonify(ok=True, ejemplos=entrenar())


@app.post("/api/aprender")
@autorizacion
def aprender():
    data = request.get_json(silent=True) or {}
    pregunta = str(data.get("pregunta", "")).strip()
    respuesta = str(data.get("respuesta", "")).strip()
    if not pregunta or not respuesta or len(pregunta) > 500 or len(respuesta) > 3000:
        return jsonify(error="Pregunta (1-500) y respuesta (1-3000) obligatorias."), 400
    return jsonify(ok=True, ejemplos=agregar(pregunta, respuesta))


@app.get("/api/pendientes")
@autorizacion
def pendientes():
    return jsonify(pendientes=leer_pendientes())


@app.post("/api/pendientes/descartar")
@autorizacion
def pendientes_descartar():
    data = request.get_json(silent=True) or {}
    pregunta = str(data.get("pregunta", "")).strip()
    if not pregunta:
        return jsonify(error="Falta la pregunta a descartar."), 400
    return jsonify(ok=True, pendientes=descartar_pendiente(pregunta))


if __name__ == "__main__":
    entrenar()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
