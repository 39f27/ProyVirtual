import os
import hashlib

from flask import Flask, flash, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from werkzeug.utils import secure_filename
from wtforms import StringField, IntegerField, TextAreaField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from sqlalchemy import Date, Index
from sqlalchemy.exc import IntegrityError
from decouple import config
from dotenv import load_dotenv

# Crear la aplicación Flask
app = Flask(__name__)

# Configuración
app.config['SECRET_KEY'] = config('SECRET_KEY')  # Busca en .env o en entorno

if not app.config['SECRET_KEY']:
    raise RuntimeError("SECRET_KEY no está definida en .env ni en variables de entorno.")

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Botella.0101@localhost/programas_ucla'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads', 'programas')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

ALLOWED_EXTENSIONS = {'doc', 'docx'}

# Crear directorio de subida si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializar extensiones
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# =================== MODELOS ===================

class Docente(db.Model):
    __tablename__ = 'docentes'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)  # opcional
    programas = db.relationship('Programa', back_populates='docente')

    def __repr__(self):
        return f"<Docente {self.nombre} (id={self.id})>"

class Programa(db.Model):
    __tablename__ = 'programas'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    asignatura_unidad_Curricular = db.Column(db.String(100), nullable=False)
    area_curricular = db.Column(db.String(100), nullable=False)
    eje_curricular = db.Column(db.String(100), nullable=False)
    semestre = db.Column(db.Integer, nullable=False)
    codigo = db.Column(db.String(20), nullable=False)
    coordinador_asignatura_unidad = db.Column(db.String(100), nullable=False)
    lapso_academico = db.Column(db.String(50), nullable=False)
    prelacion = db.Column(db.String(50), nullable=True)
    modalidad = db.Column(db.String(50), nullable=False)
    docentes = db.Column(db.String(200), nullable=False)
    unidad_credito = db.Column(db.Integer, nullable=False)
    credito_academico = db.Column(db.Integer, nullable=False)
    ht = db.Column(db.Integer, nullable=False)
    hp = db.Column(db.Integer, nullable=False)
    htp = db.Column(db.Integer, nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha_ultima_correcion = db.Column(Date, nullable=True)  # nullable=True para permitir opcionallidad
    archivo_word = db.Column(db.String(300), nullable=True)  # ruta/nombre archivo
    hash_archivo = db.Column(db.String(64), nullable=True)  # SHA256 hash
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=True)
    docente = db.relationship('Docente', back_populates='programas')

    __table_args__ = (
        Index('idx_busqueda', 'semestre', 'area_curricular', 'eje_curricular'),
    )

    def __repr__(self):
        return (f"<Programa {self.nombre} (id={self.id}), area_curricular='{self.area_curricular}', "
                f"eje_curricular='{self.eje_curricular}', fecha_ultima_correcion={self.fecha_ultima_correcion}, docente_id={self.docente_id}>")

# =================== FORMULARIO ===================

class ProgramaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=200)])
    asignatura_unidad_Curricular = StringField('Asignatura Unidad Curricular', validators=[DataRequired(), Length(max=100)])
    area_curricular = StringField('Area Curricular', validators=[DataRequired(), Length(max=100)])
    eje_curricular = StringField('Eje Curricular', validators=[DataRequired(), Length(max=100)])
    semestre = IntegerField('Semestre', validators=[DataRequired(), NumberRange(min=1, max=12)])
    codigo = StringField('Codigo', validators=[DataRequired(), Length(max=20)])
    coordinador_asignatura_unidad = StringField('Coordinador', validators=[DataRequired(), Length(max=100)])
    lapso_academico = StringField('Lapso Academico', validators=[DataRequired(), Length(max=50)])
    prelacion = StringField('Prelacion', validators=[Optional(), Length(max=50)])
    modalidad = StringField('Modalidad', validators=[DataRequired(), Length(max=50)])
    docentes = StringField('Docentes', validators=[DataRequired(), Length(max=200)])
    unidad_credito = IntegerField('Unidad de Credito', validators=[DataRequired(), NumberRange(min=1, max=10)])
    credito_academico = IntegerField('Credito Academico', validators=[DataRequired(), NumberRange(min=1, max=10)])
    ht = IntegerField('HT', validators=[DataRequired(), NumberRange(min=1)])
    hp = IntegerField('HP', validators=[DataRequired(), NumberRange(min=1)])
    htp = IntegerField('HTP', validators=[DataRequired(), NumberRange(min=1)])
    descripcion = TextAreaField('Descripcion', validators=[DataRequired()])
    # Cambié a Optional para reflejar el nullable=True en el modelo
    fecha_ultima_correcion = DateField('Fecha Ultima Correccion', validators=[Optional()])
    archivo_word = FileField('Documento Word', validators=[
        FileAllowed(['doc', 'docx'], 'Solo archivos Word (.doc, .docx)')
    ])
    submit = SubmitField('Guardar')

# =================== FUNCIONES AUXILIARES ===================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def procesar_word(file_storage, programa_id):
    try:
        filename_base = f"programa_{programa_id}"
        ext = file_storage.filename.rsplit('.', 1)[1].lower()

        # Guardar archivo temporalmente para obtener hash
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{programa_id}.{ext}")
        file_storage.save(temp_path)

        with open(temp_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        filename_final = secure_filename(f"{filename_base}_{file_hash[:8]}.{ext}")
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename_final)

        os.rename(temp_path, save_path)

        return {'ruta_archivo': filename_final, 'hash': file_hash}
    except Exception as e:
        # En caso de error, intentar borrar archivo temporal si existe
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

# =================== RUTAS ===================

@app.route('/')
def index():
    programas = Programa.query.all()
    return render_template('index.html', programas=programas)

@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    form = ProgramaForm()
    if form.validate_on_submit():
        try:
            nuevo_programa = Programa(
                nombre=form.nombre.data,
                asignatura_unidad_Curricular=form.asignatura_unidad_Curricular.data,
                area_curricular=form.area_curricular.data,
                eje_curricular=form.eje_curricular.data,
                semestre=form.semestre.data,
                codigo=form.codigo.data,
                coordinador_asignatura_unidad=form.coordinador_asignatura_unidad.data,
                lapso_academico=form.lapso_academico.data,
                prelacion=form.prelacion.data,
                modalidad=form.modalidad.data,
                docentes=form.docentes.data,
                unidad_credito=form.unidad_credito.data,
                credito_academico=form.credito_academico.data,
                ht=form.ht.data,
                hp=form.hp.data,
                htp=form.htp.data,
                descripcion=form.descripcion.data,
                fecha_ultima_correcion=form.fecha_ultima_correcion.data
            )
            db.session.add(nuevo_programa)
            db.session.flush()  # para obtener id antes del commit

            file = form.archivo_word.data
            if file and allowed_file(file.filename):
                datos_word = procesar_word(file, nuevo_programa.id)
                nuevo_programa.archivo_word = datos_word['ruta_archivo']
                nuevo_programa.hash_archivo = datos_word['hash']
            elif file:
                flash('Archivo no permitido. Solo .doc y .docx', 'danger')
                return render_template('agregar.html', form=form)

            db.session.commit()
            flash("Programa agregado exitosamente.", "success")
            return redirect(url_for('index'))

        except IntegrityError as e:
            db.session.rollback()
            flash(f"Error al agregar el programa: {str(e)}", "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Error inesperado: {str(e)}", "danger")

    return render_template('agregar.html', form=form)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    programa = Programa.query.get_or_404(id)
    form = ProgramaForm(obj=programa)
    if form.validate_on_submit():
        try:
            form.populate_obj(programa)
            archivo = request.files.get('archivo_word')
            if archivo and archivo.filename:
                if allowed_file(archivo.filename):
                    datos_word = procesar_word(archivo, programa.id)
                    programa.archivo_word = datos_word['ruta_archivo']
                    programa.hash_archivo = datos_word['hash']
                else:
                    flash('Archivo no permitido. Solo .doc y .docx', 'danger')
                    return render_template('editar.html', form=form, programa=programa)

            db.session.commit()
            flash("Programa actualizado correctamente.", "success")
            return redirect(url_for('index'))

        except IntegrityError as e:
            db.session.rollback()
            flash(f"Error al actualizar el programa: {str(e)}", "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Error inesperado: {str(e)}", "danger")

    return render_template('editar.html', form=form, programa=programa)

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    programa = Programa.query.get_or_404(id)
    try:
        # Intentar borrar archivo asociado si existe
        if programa.archivo_word:
            archivo_path = os.path.join(app.config['UPLOAD_FOLDER'], programa.archivo_word)
            if os.path.exists(archivo_path):
                os.remove(archivo_path)

        db.session.delete(programa)
        db.session.commit()
        flash("Programa eliminado correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el programa: {str(e)}", "danger")
    return redirect(url_for('index'))

@app.route('/ver/<int:id>')
def ver(id):
    programa = Programa.query.get_or_404(id)
    return render_template('ver.html', programa=programa)

@app.route('/uploads/<filename>')
def descargar_archivo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# Manejo de errores HTTP

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    with app.app_context():        
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5001)


