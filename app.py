from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Firebase
cred = credentials.Certificate("credenciales.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://mihijobotjason-default-rtdb.firebaseio.com/'
})

app = Flask(__name__)

# Cargar memoria y aprendizaje


def cargar_memoria():
    ref = db.reference("memoria")
    memoria = ref.get()
    if memoria is None:
        memoria = {"nombre": None, "edad": None,
                   "sentimiento": None, "último_tema": None}
        ref.set(memoria)
    return memoria


def guardar_memoria(memoria):
    db.reference("memoria").set(memoria)


def cargar_aprendizaje():
    ref = db.reference("aprendizaje")
    data = ref.get()
    return data.get("preguntas", []), data.get("respuestas", [])


def guardar_aprendizaje(preguntas, respuestas):
    ref = db.reference("aprendizaje")
    ref.set({"preguntas": preguntas, "respuestas": respuestas})


preguntas, respuestas = cargar_aprendizaje()
vectorizador = TfidfVectorizer()
vectores_preguntas = vectorizador.fit_transform(
    preguntas) if preguntas else None


def actualizar_modelo():
    global vectores_preguntas
    vectores_preguntas = vectorizador.fit_transform(preguntas)


def responder(mensaje):
    if mensaje in preguntas:
        return respuestas[preguntas.index(mensaje)]
    if not preguntas or vectores_preguntas is None:
        return None
    mensaje_vector = vectorizador.transform([mensaje])
    similitudes = cosine_similarity(mensaje_vector, vectores_preguntas)
    if similitudes.max() < 0.85:
        return None
    return respuestas[similitudes.argmax()]


@app.route('/')
def index():
    return render_template("chat.html")


@app.route('/mensaje', methods=["POST"])
def mensaje():
    user_input = request.json.get("mensaje")
    memoria = cargar_memoria()
    memoria["último_tema"] = user_input
    guardar_memoria(memoria)

    respuesta = responder(user_input)
    if respuesta is None:
        return jsonify({"respuesta": "No sé cómo responder a eso. Enséñame."})
    return jsonify({"respuesta": respuesta})


if __name__ == '__main__':
    app.run()
