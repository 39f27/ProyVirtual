from app import app, db

with app.app_context():
    print('=== TABLAS EN MySQL ===')
    
    # Método correcto SQLAlchemy 2.0+
    result = db.engine.connect().execute(db.text('SHOW TABLES'))
    tables = result.fetchall()
    
    if tables:
        for table in tables:
            print(f'- {table[0]}')
    else:
        print('- NO HAY TABLAS')
    
    print('\n=== VERIFICAR programa ===')
    try:
        count = db.session.execute(db.text('SELECT COUNT(*) FROM programa')).scalar()
        print(f'Registros en programa: {count}')
    except Exception as e:
        print(f'  TABLA programa NO EXISTE: {e}')
    
    print('\n=== ESTADO MySQL ===')
    print('¡CONEXIÓN MySQL ACTIVA!')
