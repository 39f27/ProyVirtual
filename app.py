import os
import hashlib
from datetime import datetime
from sqlalchemy.orm import joinedload

from flask import Flask, flash, render_template, request, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from werkzeug.utils import secure_filename
from wtforms import StringField, IntegerField, TextAreaField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from wtforms_alchemy import QuerySelectField
from sqlalchemy import Date, Index
from sqlalchemy.exc import IntegrityError
from decouple import config
from dotenv import load_dotenv

# ==========================================
# 1. INICIALIZACIÓN DE LA APP Y CONFIGURACIÓN DE BD
# ==========================================
load_dotenv()

app = Flask(__name__)

# Configuración de la base de datos (se asume que usas variables de entorno o decouple)
app.config['SECRET_KEY'] = config('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = config('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ==========================================
# 2. MODELOS DEL DIAGRAMA ER INSTITUCIONAL (UCLA)
# ==========================================

class UsuarioT(db.Model):
    __tablename__ = 'usuario_t'
    cod_usu = db.Column(db.String(50), primary_key=True)
    nom_usu = db.Column(db.String(100), nullable=True)
    cla_usu = db.Column(db.String(100), nullable=True)  # Hash de contraseña
    rol_usu = db.Column(db.String(50), nullable=True)

class DecanatoT(db.Model):
    __tablename__ = 'decanato_t'
    cod_dec = db.Column(db.String(50), primary_key=True)
    nom_dec = db.Column(db.String(150), nullable=True)
    carreras = db.relationship('CarreraT', backref='decanato', lazy=True)

class CarreraT(db.Model):
    __tablename__ = 'carrera_t'
    cod_car = db.Column(db.String(50), primary_key=True)
    nom_car = db.Column(db.String(150), nullable=True)
    cod_dec = db.Column(db.String(50), db.ForeignKey('decanato_t.cod_dec'), nullable=True)
    carreras_materias = db.relationship('CarreraMateriaM', backref='carrera', lazy=True)

class MateriasProgramasT(db.Model):
    __tablename__ = 'materias_programas_t'
    cod_mat = db.Column(db.String(50), primary_key=True)
    nom_mat = db.Column(db.String(150), nullable=True)
    materias_carreras = db.relationship('CarreraMateriaM', backref='materia', lazy=True)
    prelaciones = db.relationship('PrelacionM', backref='materia', lazy=True)

class CarreraMateriaM(db.Model):
    __tablename__ = 'carrera_materia_m'
    cod_car_mat = db.Column(db.String(50), primary_key=True)
    cod_car = db.Column(db.String(50), db.ForeignKey('carrera_t.cod_car'), nullable=True)
    cod_mat = db.Column(db.String(50), db.ForeignKey('materias_programas_t.cod_mat'), nullable=True)
    revisiones = db.relationship('RevisionProgramaM', backref='carrera_materia', lazy=True)

class PrelacionM(db.Model):
    __tablename__ = 'prelacion_m'
    cod_pre = db.Column(db.String(50), primary_key=True)
    cod_mat = db.Column(db.String(50), db.ForeignKey('materias_programas_t.cod_mat'), nullable=True)
    cod_mat_pre = db.Column(db.String(50), nullable=True)

class LapsoAcademicoT(db.Model):
    __tablename__ = 'lapso_academico_t'
    cod_lap = db.Column(db.String(50), primary_key=True)
    des_lap = db.Column(db.String(100), nullable=True)
    fec_ini = db.Column(db.Date, nullable=True)
    fec_fin = db.Column(db.Date, nullable=True)
    est_act = db.Column(db.String(1), nullable=True)
    revisiones = db.relationship('RevisionProgramaM', backref='lapso_academico', lazy=True)

class DocenteT(db.Model):
    __tablename__ = 'docente_t'
    cod_doc = db.Column(db.String(50), primary_key=True)
    nom_doc = db.Column(db.String(100), nullable=True)
    ape_doc = db.Column(db.String(100), nullable=True)
    ced_doc = db.Column(db.String(20), nullable=True)
    tel_doc = db.Column(db.String(50), nullable=True)
    cor_doc = db.Column(db.String(100), nullable=True)
    fec_doc = db.Column(db.String(50), nullable=True)
    nac_doc = db.Column(db.String(50), nullable=True)
    sex_doc = db.Column(db.String(20), nullable=True)
    revisiones = db.relationship('RevisionProgramaM', backref='docente_t', lazy=True)

class RevisionProgramaM(db.Model):
    __tablename__ = 'revision_programa_m'
    cod_pro = db.Column(db.String(50), primary_key=True)
    cod_doc = db.Column(db.String(50), db.ForeignKey('docente_t.cod_doc'), nullable=True)
    cod_car_mat = db.Column(db.String(50), db.ForeignKey('carrera_materia_m.cod_car_mat'), nullable=True)
    fec_rev = db.Column(db.Date, nullable=True)
    est_rev = db.Column(db.String(50), nullable=True)
    nom_arc = db.Column(db.String(255), nullable=True)
    obs_rev = db.Column(db.Text, nullable=True)
    cod_lap = db.Column(db.String(50), db.ForeignKey('lapso_academico_t.cod_lap'), nullable=True)

# ==========================================
# 3. TRUCO DE CONTEXTO ABSOLUTO PARA MIGRACIONES
# ==========================================
# Al referenciar explícitamente las clases aquí, garantizamos que Alembic las procese obligatoriamente.
_forzar_mapeo_ucla = [UsuarioT, DecanatoT, CarreraT, MateriasProgramasT, CarreraMateriaM, PrelacionM, LapsoAcademicoT, DocenteT, RevisionProgramaM]

# ==========================================
# 4. MODELOS OPERATIVOS DE SISTEMA
# ==========================================

class Docente(db.Model):
    __tablename__ = 'docentes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    programas = db.relationship('Programa', back_populates='docente')

    def __repr__(self):
        return f"<Docente {self.nombre} (id={self.id})>"

class Programa(db.Model):
    __tablename__ = 'programas'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    asignatura_unidad_Curricular = db.Column(db.String(150), nullable=False)
    area_curricular = db.Column(db.String(100), nullable=False)
    eje_curricular = db.Column(db.String(100), nullable=False)
    semestre = db.Column(db.String(20), nullable=False)
    coordinador_asignatura_unidad = db.Column(db.String(100), nullable=True)
    lapso_academico = db.Column(db.String(50), nullable=True)
    prelacion = db.Column(db.String(100), nullable=True)
    modalidad = db.Column(db.String(50), nullable=True)
    docentes = db.Column(db.Text, nullable=True)
    unidad_credito = db.Column(db.Integer, nullable=True)
    credito_academico = db.Column(db.Integer, nullable=True)
    ht = db.Column(db.Integer, nullable=True)
    hp = db.Column(db.Integer, nullable=True)
    htp = db.Column(db.Integer, nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    fecha_ultima_correcion = db.Column(db.Date, nullable=True)
    estado_actual = db.Column(db.String(30), default='En Revisión', nullable=False)
    archivo_word = db.Column(db.String(300), nullable=True)
    hash_archivo = db.Column(db.String(64), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    docente_id = db.Column(db.Integer, db.ForeignKey('docentes.id'), nullable=True)
    docente = db.relationship('Docente', back_populates='programas')
    versiones = db.relationship('ProgramaVersion', backref='programa', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_busqueda', 'semestre', 'area_curricular', 'eje_curricular'),
    )

    def __repr__(self):
        return f"<Programa {self.nombre} (id={self.id})>"

class ProgramaVersion(db.Model):
    __tablename__ = 'programa_versiones'
    id = db.Column(db.Integer, primary_key=True)
    programa_id = db.Column(db.Integer, db.ForeignKey('programas.id'), nullable=False)
    version_numero = db.Column(db.Integer, nullable=False)
    nombre_archivo_real = db.Column(db.String(255), nullable=False)
    archivo_binario = db.Column(db.LargeBinary(length=16777215), nullable=False)
    enviado_por = db.Column(db.String(20), nullable=False)
    observaciones = db.Column(db.Text, nullable=True)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)

# ==========================================
# HACIA ABAJO SIGUE TU CÓDIGO NORMAL:
# obtener_docentes(), ProgramaForm, rutas (@app.route), etc.
# ==========================================

# =================== FUNCIONES AUXILIARES ===================

def obtener_docentes():
    return Docente.query.all()

# =================== FORMULARIO ===================

class ProgramaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=200)])
    asignatura_unidad_Curricular = StringField('Asignatura Unidad Curricular', validators=[DataRequired(), Length(max=150)])
    area_curricular = StringField('Area Curricular', validators=[DataRequired(), Length(max=100)])
    eje_curricular = StringField('Eje Curricular', validators=[DataRequired(), Length(max=100)])
    semestre = StringField('Semestre / Lapso', validators=[DataRequired(), Length(max=20)]) 
    codigo = StringField('Codigo', validators=[DataRequired(), Length(max=20)])
    coordinador_asignatura_unidad = StringField('Coordinador', validators=[DataRequired(), Length(max=100)])
    lapso_academico = StringField('Lapso Academico', validators=[DataRequired(), Length(max=50)])
    prelacion = StringField('Prelacion', validators=[Optional(), Length(max=100)])
    modalidad = StringField('Modalidad', validators=[DataRequired(), Length(max=50)])
    
    docente = QuerySelectField(
        'Docente Responsable',
        query_factory=obtener_docentes,
        allow_blank=True,
        blank_text='-- Seleccione un Docente Maestro --',
        get_label='nombre'
    )
    
    unidad_credito = IntegerField('Unidad de Credito', validators=[DataRequired(), NumberRange(min=1, max=10)])
    credito_academico = IntegerField('Credito Academico', validators=[DataRequired(), NumberRange(min=1, max=10)])
    ht = IntegerField('HT', validators=[DataRequired(), NumberRange(min=0)])
    hp = IntegerField('HP', validators=[DataRequired(), NumberRange(min=0)])
    htp = IntegerField('HTP', validators=[DataRequired(), NumberRange(min=0)])
    descripcion = TextAreaField('Descripcion', validators=[DataRequired()])
    fecha_ultima_correcion = DateField('Fecha Ultima Correccion', validators=[Optional()])
    archivo_word = FileField('Documento Word', validators=[
        FileAllowed(['doc', 'docx', 'pdf'], 'Solo archivos Word o PDF')
    ])
    submit = SubmitField('Guardar')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'doc', 'docx', 'pdf'}

# =================== RUTAS ===================

@app.route('/')
def index():
    # Con joinedload traemos los programas junto con sus versiones en una sola consulta SQL eficiente
    programas = Programa.query.options(joinedload(Programa.versiones)).all()
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
                docentes="",  
                docente=form.docente.data,  
                unidad_credito=form.unidad_credito.data,
                credito_academico=form.credito_academico.data,
                ht=form.ht.data,
                hp=form.hp.data,
                htp=form.htp.data,
                descripcion=form.descripcion.data,
                fecha_ultima_correcion=form.fecha_ultima_correcion.data,
                estado_actual='En Revisión'
            )
            
            db.session.add(nuevo_programa)
            db.session.flush()

            file = form.archivo_word.data
            if file and allowed_file(file.filename):
                nombre_original = secure_filename(file.filename)
                file.stream.seek(0)
                bytes_archivo = file.stream.read()
                hash_sha256 = hashlib.sha256(bytes_archivo).hexdigest()
                
                nueva_version = ProgramaVersion(
                    programa_id=nuevo_programa.id,
                    version_numero=1,
                    nombre_archivo_real=nombre_original,
                    archivo_binario=bytes_archivo,
                    enviado_por='Profesor',
                    observaciones="Carga inicial del programa académico."
                )
                db.session.add(nueva_version)
                
                nuevo_programa.archivo_word = nombre_original
                nuevo_programa.hash_archivo = hash_sha256
                
            elif file:
                flash('Archivo no permitido. Solo .doc, .docx y .pdf', 'danger')
                return render_template('agregar.html', form=form)

            db.session.commit()
            flash("Programa académico y archivo registrados exitosamente.", "success")
            return redirect(url_for('index'))

        except IntegrityError as e:
            db.session.rollback()
            flash(f"Error de integridad (Código ya registrado): {str(e)}", "danger")
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
            # 1. Guardamos los cambios de los campos de texto
            form.populate_obj(programa)
            programa.docente = form.docente.data

            # 2. Extrayemos el archivo directamente del objeto del formulario
            file = form.archivo_word.data
            
            # Verificación blindada de tipos y existencia
            if file and hasattr(file, 'filename') and file.filename != '':
                if allowed_file(file.filename):
                    nombre_original = secure_filename(file.filename)
                    file.stream.seek(0)
                    bytes_archivo = file.stream.read()
                    hash_sha256 = hashlib.sha256(bytes_archivo).hexdigest()
                    
                    # Calcular el número de la siguiente versión
                    num_versiones = ProgramaVersion.query.filter_by(programa_id=programa.id).count()
                    nueva_version_num = num_versiones + 1
                    
                    nueva_version = ProgramaVersion(
                        programa_id=programa.id,
                        version_numero=nueva_version_num,
                        nombre_archivo_real=nombre_original,
                        archivo_binario=bytes_archivo,
                        enviado_por='Profesor',
                        observaciones=request.form.get('observaciones', 'Nueva versión cargada desde edición.')
                    )
                    db.session.add(nueva_version)
                    
                    # Actualizamos los metadatos en el registro principal
                    programa.archivo_word = nombre_original
                    programa.hash_archivo = hash_sha256
                    programa.estado_actual = 'Reenviado'
                else:
                    flash('Archivo no permitido. Solo .doc, .docx y .pdf', 'danger')
                    return render_template('editar.html', form=form, programa=programa)

            db.session.commit()
            flash("Programa académico actualizado correctamente.", "success")
            return redirect(url_for('index'))

        except IntegrityError as e:
            db.session.rollback()
            flash(f"Error de integridad al actualizar: {str(e)}", "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Error inesperado: {str(e)}", "danger")

    return render_template('editar.html', form=form, programa=programa)

@app.route('/eliminar/<int:id>', methods=['POST', 'GET'])
def eliminar(id):
    programa = Programa.query.get_or_404(id)
    try:
        db.session.delete(programa)
        db.session.commit()
        flash("Programa y todo su historial de versiones eliminados de MySQL.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el programa: {str(e)}", "danger")
    return redirect(url_for('index'))

@app.route('/descargar/<filename>')
def descargar_archivo(filename):
    try:
        # Buscamos directamente el archivo por su nombre real en el historial de versiones
        version_archivo = ProgramaVersion.query.filter_by(nombre_archivo_real=filename).first_or_404()
            
        if not version_archivo or not version_archivo.archivo_binario:
            flash("El archivo solicitado no se encuentra en el repositorio de la base de datos.", "danger")
            return redirect(url_for('index'))
            
        # Retornamos los bytes exactos de la versión seleccionada (sea V1, V2 o V3)
        return Response(
            version_archivo.archivo_binario,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={version_archivo.nombre_archivo_real}"}
        )
    except Exception as e:
        flash(f"Error al descargar el documento: {str(e)}", "danger")
        return redirect(url_for('index'))

@app.route('/ver/<int:id>')
def ver(id):
    programa = Programa.query.get_or_404(id)
    
    # Buscamos las versiones de este programa ordenadas de la última (más reciente) a la primera
    versiones = ProgramaVersion.query.filter_by(programa_id=id).order_by(ProgramaVersion.version_numero.desc()).all()
    
    # Enviamos tanto el programa como su historial de versiones a la plantilla
    return render_template('ver.html', programa=programa, versiones=versiones)

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