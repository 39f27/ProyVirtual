import sys
import os


# Ruta absoluta al directorio del proyecto donde esta app.py
project_path = '/home/gavidia/Proyetos/Proyecto/ProyVirtual'
if project_path not in sys.path:
    sys.path.insert(0, project_path) 


# Ruta al entorno virtual para  cargue las librerias instaladas 
activate_env = os.path.expanduser('/home/gavidia/Proyectos/Proyecto/ProyVirtual_Linux/bin/activate_this.py')
if os.path.exists(activate_env):
    with open (activate_env) as file:
    exec(file.read(), dict(__fle__=activate_env))

#Importa la istancia flask
from app import app as application

