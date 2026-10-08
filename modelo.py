"""Motor local de recuperación de respuestas con TF-IDF sobre una base JSON.
No es un modelo generativo; aprende ejemplos mediante actualización del índice.
"""
from __future__ import annotations
import json
import os
import threading
from pathlib import Path
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE = Path(__file__).resolve().parent
DATA_FILE = Path(os.environ.get("KNOWLEDGE_FILE", str(BASE / "data" / "conocimiento.json")))
MODEL_FILE = Path(os.environ.get("MODEL_FILE", str(BASE / "data" / "modelo.joblib")))
PENDIENTES_FILE = Path(os.environ.get("PENDIENTES_FILE", str(BASE / "data" / "pendientes.json")))
LOCK = threading.RLock()


def leer():
    with LOCK:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        ejemplos = data.get("ejemplos", [])
        if not isinstance(ejemplos, list):
            raise ValueError("La base debe contener una lista 'ejemplos'.")
        return ejemplos


def entrenar():
    """Reconstruye el índice y lo guarda, atómicamente en disco."""
    with LOCK:
        ejemplos = leer()
        preguntas = [e["pregunta"] for e in ejemplos if e.get("pregunta") and e.get("respuesta")]
        respuestas = [e["respuesta"] for e in ejemplos if e.get("pregunta") and e.get("respuesta")]
        if not preguntas:
            raise ValueError("No hay ejemplos para entrenar.")
        vectorizer = TfidfVectorizer(strip_accents="unicode", lowercase=True, analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True)
        matrix = vectorizer.fit_transform(preguntas)
        payload = {"vectorizer": vectorizer, "matrix": matrix, "preguntas": preguntas, "respuestas": respuestas}
        MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = MODEL_FILE.with_suffix(".tmp")
        joblib.dump(payload, tmp)
        tmp.replace(MODEL_FILE)
        return len(preguntas)


def cargar():
    with LOCK:
        if not MODEL_FILE.exists() or MODEL_FILE.stat().st_mtime < DATA_FILE.stat().st_mtime:
            entrenar()
        return joblib.load(MODEL_FILE)


def responder(texto: str, umbral: float = 0.40):
    with LOCK:
        modelo = cargar()
        query = modelo["vectorizer"].transform([texto])
        scores = cosine_similarity(query, modelo["matrix"])[0]
        i = int(scores.argmax())
        score = float(scores[i])
        if score < umbral:
            _registrar_pendiente(texto)
            return {"respuesta": "Aún no sé responder eso. Puedes enseñármelo desde la pestaña Enseñar.", "confianza": round(score, 3), "conocido": False}
        return {"respuesta": modelo["respuestas"][i], "confianza": round(score, 3), "conocido": True, "pregunta_parecida": modelo["preguntas"][i]}


def _registrar_pendiente(texto: str):
    """Guarda preguntas sin respuesta para que el administrador las revise y enseñe."""
    normalizada = texto.strip().casefold()
    if not normalizada:
        return
    try:
        data = json.loads(PENDIENTES_FILE.read_text(encoding="utf-8")) if PENDIENTES_FILE.exists() else {"pendientes": []}
    except (json.JSONDecodeError, OSError):
        data = {"pendientes": []}
    pendientes = data.setdefault("pendientes", [])
    for item in pendientes:
        if item["pregunta"].strip().casefold() == normalizada:
            item["veces"] = item.get("veces", 1) + 1
            break
    else:
        pendientes.append({"pregunta": texto.strip(), "veces": 1})
    PENDIENTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporal = PENDIENTES_FILE.with_suffix(".tmp")
    temporal.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporal.replace(PENDIENTES_FILE)


def leer_pendientes():
    with LOCK:
        if not PENDIENTES_FILE.exists():
            return []
        try:
            data = json.loads(PENDIENTES_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return sorted(data.get("pendientes", []), key=lambda x: x.get("veces", 1), reverse=True)


def descartar_pendiente(pregunta: str):
    with LOCK:
        if not PENDIENTES_FILE.exists():
            return 0
        normalizada = pregunta.strip().casefold()
        data = json.loads(PENDIENTES_FILE.read_text(encoding="utf-8"))
        pendientes = data.get("pendientes", [])
        restantes = [p for p in pendientes if p["pregunta"].strip().casefold() != normalizada]
        data["pendientes"] = restantes
        temporal = PENDIENTES_FILE.with_suffix(".tmp")
        temporal.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporal.replace(PENDIENTES_FILE)
        return len(restantes)


def agregar(pregunta: str, respuesta: str):
    with LOCK:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        existentes = data.setdefault("ejemplos", [])
        normalizada = pregunta.strip().casefold()
        for item in existentes:
            if item["pregunta"].strip().casefold() == normalizada:
                item["respuesta"] = respuesta.strip()
                break
        else:
            existentes.append({"pregunta": pregunta.strip(), "respuesta": respuesta.strip()})
        temporal = DATA_FILE.with_suffix(".tmp")
        temporal.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporal.replace(DATA_FILE)
        cantidad = entrenar()
        descartar_pendiente(pregunta)
        return cantidad
