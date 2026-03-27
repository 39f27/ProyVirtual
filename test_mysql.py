from app import app, db

with app.app_context():
    conn = db.engine.connect()
    print("¡MySQL CONECTADO EXITOSAMENTE!")
    conn.close()
print("Prueba completada.")
