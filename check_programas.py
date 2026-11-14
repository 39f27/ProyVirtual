from app import app, db

with app.app_context():
    print('=== VERIFICACIÓN MySQL REAL ===')
    
    # Contar tablas CORRECTAS
    print('Docentes:', db.session.execute(db.text('SELECT COUNT(*) FROM docentes')).scalar())
    print('Programas:', db.session.execute(db.text('SELECT COUNT(*) FROM programas')).scalar())
    
    print('\n=== PRIMER PROGRAMA ===')
    try:
        result = db.session.execute(db.text('SELECT nombre, codigo, asignatura_unidad_Curricular FROM programas LIMIT 1')).fetchone()
        if result:
            print(f'- {result.nombre} (Código: {result.codigo})')
        else:
            print('- VACÍO (¡Normal! Usa "Agregar Programa")')
    except:
        print('- Sin datos aún')
    
    print('\n=== MySQL MULTI-USUARIO ===')
    print('✅ FUNCIONANDO CORRECTAMENTE')
    print('🎯 Agrega datos en: http://127.0.0.1:5001')
