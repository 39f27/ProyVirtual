import os
# Importamos el contexto, la base de datos y el modelo desde tu archivo del proyecto
from app import app, db, Docente  

def precargar_docentes():
    """
    Inserta un listado de docentes maestros de prueba en la base de datos MySQL,
    evitando duplicar registros existentes mediante la validación del email.
    """
    print("\n" + "="*50)
    print("🚀 INICIANDO PRECARGA DE DATOS MAESTROS (UCLA)")
    print("="*50)

    # Catálogo de docentes de prueba para el sistema STEMA
    lista_docentes = [
        {"nombre": "Prof. Alejandro Silva", "email": "asilva@ucla.edu.ve"},
        {"nombre": "Dra. María Elena Rodríguez", "email": "merodriguez@ucla.edu.ve"},
        {"nombre": "Ing. Carlos Mendoza", "email": "cmendoza@ucla.edu.ve"},
        {"nombre": "MSc. Beatriz Torrealba", "email": "btorrealba@ucla.edu.ve"},
        {"nombre": "Prof. Luis Javier Gómez", "email": "ljgomez@ucla.edu.ve"}
    ]

    # Ejecutar dentro del contexto de la aplicación para interactuar con MySQL
    with app.app_context():
        # Crea las tablas si aún no existen en tu base de datos programas_ucla
        db.create_all()
        
        docentes_creados = 0
        docentes_omitidos = 0

        for datos in lista_docentes:
            # Evitar duplicados usando el email único
            docente_existente = Docente.query.filter_by(email=datos["email"]).first()
            
            if not docente_existente:
                nuevo_docente = Docente(
                    nombre=datos["nombre"],
                    email=datos["email"]
                )
                db.session.add(nuevo_docente)
                docentes_creados += 1
                print(f"✅ Registrado exitosamente: {datos['nombre']} ({datos['email']})")
            else:
                docentes_omitidos += 1
                print(f"⚠️ Ya registrado (Omitido): {datos['nombre']}")

        # Confirmar la transacción en MySQL
        if docentes_creados > 0:
            db.session.commit()
            print("-"*50)
            print(f"🎉 Sincronización exitosa. Se agregaron {docentes_creados} nuevos docentes.")
        else:
            print("-"*50)
            print(f"ℹ️ Base de datos al día. Todos los docentes ({docentes_omitidos}) ya estaban precargados.")
        
        print("="*50 + "\n")

if __name__ == "__main__":
    precargar_docentes()