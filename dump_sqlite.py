import sqlite3
con = sqlite3.connect('programas.db')
with open('backup_programas.sql', 'w') as f:
    for line in con.iterdump():
        f.write(f'{line}\n')
print("¡Dump creado: backup_programas.sql")
con.close()
