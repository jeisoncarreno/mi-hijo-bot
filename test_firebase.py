from firebase_config import db

# Crear o actualizar un documento de ejemplo
doc_ref = db.collection("usuarios").document("usuario_prueba")
doc_ref.set({
    "nombre": "HijoBot",
    "nivel": 1,
    "memoria": {}
})

print("Documento guardado en Firebase.")
