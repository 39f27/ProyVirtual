from app import app, db

with app.app_context():
    print('=== VERIFICACIÓN MySQL ===')
    print('Programas:', db.session.execute('SELECT COUNT(*) FROM programa').scalar())
    print('Programas_alt:', db.session.execute('SELECT COUNT(*) FROM programas').scalar())
    print('Docentes:', db.session.execute('SELECT COUNT(*) FROM docentes').scalar())
    
    print('\nPrimer programa:')
    result = db.session.execute('SELECT nombre, codigo FROM programa LIMIT 1').fetchone()
    if result:
        print(f'  - {result.nombre} ({result.codigo})')
    else:
        print('  - VACÍO')
