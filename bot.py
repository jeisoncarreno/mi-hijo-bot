import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import firebase_admin
from firebase_admin import credentials, db

# Inicializar Firebase con tu archivo de credenciales
cred = credentials.Certificate("credenciales.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://mihijobotjason-default-rtdb.firebaseio.com/'
})

# Cargar memoria desde Firebase


def cargar_memoria():
    ref = db.reference("memoria")
    memoria = ref.get()
    if memoria is None:
        memoria = {
            "nombre": None,
            "edad": None,
            "sentimiento": None,
            "último_tema": None
        }
        ref.set(memoria)
    return memoria

# Guardar memoria en Firebase


def guardar_memoria(memoria):
    ref = db.reference("memoria")
    ref.set(memoria)

# Cargar aprendizaje desde Firebase


def cargar_aprendizaje():
    ref = db.reference("aprendizaje")
    data = ref.get()
    if data and "preguntas" in data and "respuestas" in data:
        return data["preguntas"], data["respuestas"]
    else:
        return [], []

# Guardar aprendizaje en Firebase


def guardar_aprendizaje(preguntas, respuestas):
    ref = db.reference("aprendizaje")
    ref.set({
        "preguntas": preguntas,
        "respuestas": respuestas
    })


# Cargar memoria y aprendizaje
memoria = cargar_memoria()
preguntas, respuestas = cargar_aprendizaje()

# Vectorización
vectorizador = TfidfVectorizer()
vectores_preguntas = vectorizador.fit_transform(
    preguntas) if preguntas else None


def actualizar_modelo():
    global vectores_preguntas
    vectores_preguntas = vectorizador.fit_transform(preguntas)
    print(f"Modelo actualizado con {len(preguntas)} preguntas.")



def responder(mensaje):
    if mensaje in preguntas:
        indice = preguntas.index(mensaje)
        return respuestas[indice]

    if not preguntas or vectores_preguntas is None:
        return None

    mensaje_vector = vectorizador.transform([mensaje])
    similitudes = cosine_similarity(mensaje_vector, vectores_preguntas)
    similitud_max = similitudes.max()

    if similitud_max < 0.7:
        return None
    else:
        indice_max = similitudes.argmax()
        return respuestas[indice_max]


# Bucle del bot
while True:
    entrada = input("Tú: ")

    if entrada.lower() in ["salir", "adiós"]:
        print("Bot: Hasta luego!")
        break

    memoria["último_tema"] = entrada  # Guarda lo último que se dijo

    if entrada.lower() in ["¿cómo me llamo?", "como me llamo", "¿sabes mi nombre?", "dime mi nombre"]:
        if memoria["nombre"]:
            print(f"Bot: Te llamas {memoria['nombre']}.")
        else:
            print("Bot: Aún no sé tu nombre, ¿cómo te llamas?")
        continue

    if "me llamo" in entrada.lower():
        nombre = entrada.lower().split("me llamo")[-1].strip().capitalize()
        memoria["nombre"] = nombre
        guardar_memoria(memoria)
        print(f"Bot: Encantado de conocerte, {nombre}!")
        continue

    if "mi nombre es" in entrada.lower():
        nombre = entrada.lower().split("mi nombre es")[-1].strip().capitalize()
        memoria["nombre"] = nombre
        guardar_memoria(memoria)
        print(f"Bot: Hola {nombre}, lo recordaré.")
        continue

    # 😌 Aprender emociones por tema
    if "me hace sentir" in entrada.lower():
        partes = entrada.lower().split("me hace sentir")
        tema = partes[0].replace("hablar de", "").strip()
        emocion = partes[1].strip()

        ref_emociones = db.reference("emociones_por_tema")
        ref_emociones.child(tema).set(emocion)

        memoria["último_tema"] = tema
        guardar_memoria(memoria)

        print(
            f"Bot: Entiendo. Hablar de {tema} te hace sentir {emocion}. Lo recordaré.")
        continue

    # 😃 Verificar si el tema tiene emoción asociada
    if tema_actual in emociones_por_tema:
        emocion = emociones_por_tema[tema_actual]
        print(f"Bot: Sé que hablar de {tema_actual} te hace sentir {emocion}. 😊")
    else:
        print(f"Bot: No estoy seguro de cómo te hace sentir hablar de {tema_actual}. ¿Te gustaría contarme?")


    # 🤖 Procesar respuestas aprendidas
    respuesta = responder(entrada)

    if respuesta is None:
        print("Bot: No sé cómo responder a eso.")
        nueva_respuesta = input("¿Qué debería decir? ")
        preguntas.append(entrada)
        respuestas.append(nueva_respuesta)
        actualizar_modelo()
        guardar_aprendizaje(preguntas, respuestas)
        print("Bot: ¡Gracias por enseñarme!")
    else:
        print("Bot:", respuesta)

        guardar_memoria(memoria)  # Actualiza el último_tema en cada turno
