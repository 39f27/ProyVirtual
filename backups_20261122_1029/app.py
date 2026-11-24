from datetime import datetime, date
import csv
import hashlib
import io
from flask import (
    Flask,
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    make_response,
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, TextAreaField, IntegerField, SubmitField, DateField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_secreta_proyvirtual_ucla_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Botella.0101@localhost/programas_ucla'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==========================================
# 1. MODELOS DE LA ARQUITECTURA MAESTRA UCLA (_t y _m)
# ==========================================

class UsuarioT(db.Model):
    __tablename__ = 'usuario_t'
    cod_usu = db.Column(db.String(50), primary_key=True)
    nom_usu = db.Column(db.String(100), nullable=True)
    cla_usu = db.Column(db.String(100), nullable=True)
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
    pensum = db.Column(db.String(50), nullable=False, default='Pensum 2022')
    semestre = db.Column(db.String(20), nullable=True)
    revisiones = db.relationship('RevisionProgramaM', backref='carrera_materia', lazy=True)
    programas = db.relationship('Programa', backref='carrera_materia_rel', lazy=True)


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
    programas = db.relationship('Programa', backref='lapso_academico_rel', lazy=True)


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
    programas = db.relationship('Programa', backref='docente_t_rel', lazy=True)


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


_forzar_mapeo_ucla = [
    UsuarioT, DecanatoT, CarreraT, MateriasProgramasT,
    CarreraMateriaM, PrelacionM, LapsoAcademicoT, DocenteT, RevisionProgramaM
]

# ==========================================
# 2. MODELOS OPERATIVOS Y VERSIONAMIENTO
# ==========================================

class Docente(db.Model):
    __tablename__ = 'docentes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)


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

    cod_doc = db.Column(db.String(50), db.ForeignKey('docente_t.cod_doc'), nullable=True)
    docente_maestro = db.relationship(
        'DocenteT',
        foreign_keys=[cod_doc],
        overlaps="docente_t_rel,programas",
    )

    cod_car_mat = db.Column(db.String(50), db.ForeignKey('carrera_materia_m.cod_car_mat'), nullable=True)
    carrera_materia = db.relationship(
        'CarreraMateriaM',
        foreign_keys=[cod_car_mat],
        overlaps="carrera_materia_rel,programas",
    )

    cod_lap = db.Column(db.String(50), db.ForeignKey('lapso_academico_t.cod_lap'), nullable=True)
    lapso_maestro = db.relationship(
        'LapsoAcademicoT',
        foreign_keys=[cod_lap],
        overlaps="lapso_academico_rel,programas",
    )
    versiones = db.relationship('ProgramaVersion', backref='programa', lazy=True, cascade="all, delete-orphan")


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
# 3. FORMULARIOS WTFORMS Y UTILIDADES
# ==========================================

class ProgramaForm(FlaskForm):
    nombre = StringField('Nombre del Programa', validators=[DataRequired(), Length(max=200)])
    asignatura_unidad_Curricular = StringField('Asignatura / Unidad Curricular', validators=[Optional(), Length(max=150)])
    semestre = StringField('Semestre', validators=[Optional(), Length(max=20)])
    lapso_academico = StringField('Lapso Académico', validators=[Optional(), Length(max=50)])
    area_curricular = StringField('Área Curricular', validators=[DataRequired(), Length(max=100)])
    eje_curricular = StringField('Eje Curricular', validators=[DataRequired(), Length(max=100)])
    docente = SelectField('Docente', coerce=str, validators=[DataRequired()])
    codigo = StringField('Código', validators=[DataRequired(), Length(max=20)])
    coordinador_asignatura_unidad = StringField('Coordinador', validators=[DataRequired(), Length(max=100)])
    modalidad = StringField('Modalidad', validators=[DataRequired(), Length(max=50)])
    prelacion = StringField('Prelación', validators=[Optional(), Length(max=100)])

    unidad_credito = IntegerField('Unidad de Crédito', validators=[DataRequired(), NumberRange(min=1, max=10)])
    credito_academico = IntegerField('Crédito Académico', validators=[DataRequired(), NumberRange(min=1, max=10)])
    ht = IntegerField('HT', validators=[DataRequired(), NumberRange(min=0)])
    hp = IntegerField('HP', validators=[DataRequired(), NumberRange(min=0)])
    htp = IntegerField('HTP', validators=[DataRequired(), NumberRange(min=0)])
    descripcion = TextAreaField('Descripción', validators=[DataRequired()])
    fecha_ultima_correcion = DateField('Fecha Última Corrección', validators=[Optional()])
    archivo_word = FileField('Documento Word', validators=[Optional()])
    submit = SubmitField('Guardar Programa')


ALLOWED_EXTENSIONS = {'doc', 'docx', 'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def mensaje_error_integridad(err):
    detalle = str(getattr(err, 'orig', err)).lower()
    if 'duplicate entry' in detalle:
        return "Ya existe un registro con ese código o combinación única en la base de datos.", "warning"
    if 'foreign key constraint fails' in detalle:
        return "Error de integridad referencial: verifique carrera, materia, docente o lapso.", "danger"
    return "No se pudo guardar por una restricción de integridad en la base de datos.", "danger"


def construir_query_programas():
    """Construye la consulta base de programas con los filtros de la URL."""
    q_docente = request.args.get('docente', '').strip()
    q_carrera = request.args.get('carrera', '').strip()
    q_materia = request.args.get('materia', '').strip()
    q_estatus = request.args.get('estatus', '').strip()
    q_desde = request.args.get('desde', '').strip()
    q_hasta = request.args.get('hasta', '').strip()

    query = Programa.query.options(
        joinedload(Programa.versiones),
        joinedload(Programa.docente_maestro),
        joinedload(Programa.carrera_materia).joinedload(CarreraMateriaM.materia),
        joinedload(Programa.carrera_materia).joinedload(CarreraMateriaM.carrera)
    )

    if q_docente:
        patron_doc = f"%{q_docente}%"
        query = query.outerjoin(Programa.docente_maestro).filter(
            or_(
                DocenteT.nom_doc.ilike(patron_doc),
                DocenteT.ape_doc.ilike(patron_doc),
                DocenteT.ced_doc.ilike(patron_doc),
                DocenteT.cod_doc.ilike(patron_doc),
            )
        )

    if q_carrera or q_materia:
        query = query.outerjoin(Programa.carrera_materia)
        if q_carrera:
            query = query.filter(CarreraMateriaM.cod_car == q_carrera)
        if q_materia:
            patron_mat = f"%{q_materia}%"
            query = query.outerjoin(
                MateriasProgramasT,
                CarreraMateriaM.cod_mat == MateriasProgramasT.cod_mat
            ).filter(
                or_(
                    Programa.codigo.ilike(patron_mat),
                    Programa.asignatura_unidad_Curricular.ilike(patron_mat),
                    CarreraMateriaM.cod_mat.ilike(patron_mat),
                    MateriasProgramasT.nom_mat.ilike(patron_mat),
                )
            )

    if q_estatus:
        query = query.filter(Programa.estado_actual == q_estatus)

    if q_desde:
        try:
            fecha_desde = datetime.strptime(q_desde, "%Y-%m-%d")
            query = query.filter(Programa.fecha_creacion >= fecha_desde)
        except ValueError:
            flash("Formato de fecha 'Desde' no válido. Use AAAA-MM-DD.", "warning")

    if q_hasta:
        try:
            fecha_hasta = datetime.strptime(q_hasta, "%Y-%m-%d")
            fin_de_dia = datetime.combine(fecha_hasta.date(), datetime.max.time())
            query = query.filter(Programa.fecha_creacion <= fin_de_dia)
        except ValueError:
            flash("Formato de fecha 'Hasta' no válido. Use AAAA-MM-DD.", "warning")

    filtros_activos = {
        "docente": q_docente,
        "carrera": q_carrera,
        "materia": q_materia,
        "estatus": q_estatus,
        "desde": q_desde,
        "hasta": q_hasta,
    }
    return query.order_by(Programa.fecha_creacion.desc()), filtros_activos

# ==========================================
# 4. BLUEPRINT API Y RUTAS DE CONSULTA DINÁMICA
# ==========================================

api_bp = Blueprint("api_proyvirtual", __name__, url_prefix="/api")


@api_bp.get("/docentes/buscar")
def api_buscar_docentes():
    termino = request.args.get("q", "", type=str).strip()
    if len(termino) < 2:
        return jsonify([])

    patron = f"%{termino}%"
    docentes = (
        DocenteT.query.filter(
            or_(
                DocenteT.cod_doc.ilike(patron),
                DocenteT.ced_doc.ilike(patron),
                DocenteT.nom_doc.ilike(patron),
                DocenteT.ape_doc.ilike(patron),
            )
        )
        .order_by(DocenteT.ape_doc.asc(), DocenteT.nom_doc.asc())
        .limit(20)
        .all()
    )

    resultados = [
        {
            "cod_doc": d.cod_doc,
            "cedula": d.ced_doc or "",
            "nombre_completo": f"{d.nom_doc or ''} {d.ape_doc or ''}".strip(),
            "etiqueta": f"{d.ced_doc or d.cod_doc} - {d.nom_doc or ''} {d.ape_doc or ''}".strip(),
        }
        for d in docentes
    ]
    return jsonify(resultados)


@api_bp.get("/materias/filtrar")
def api_filtrar_materias():
    cod_car = request.args.get("cod_car", "", type=str).strip()
    pensum = request.args.get("pensum", "", type=str).strip()
    termino = request.args.get("q", "", type=str).strip()

    if not cod_car and len(termino) < 2:
        return jsonify([])

    consulta = (
        db.session.query(
            CarreraMateriaM.cod_car_mat,
            CarreraMateriaM.cod_car,
            CarreraMateriaM.cod_mat,
            CarreraMateriaM.pensum,
            CarreraMateriaM.semestre,
            MateriasProgramasT.nom_mat,
        )
        .join(
            MateriasProgramasT,
            CarreraMateriaM.cod_mat == MateriasProgramasT.cod_mat,
        )
    )

    if cod_car:
        consulta = consulta.filter(CarreraMateriaM.cod_car == cod_car)
    if pensum:
        consulta = consulta.filter(CarreraMateriaM.pensum == pensum)
    if termino:
        patron = f"%{termino}%"
        consulta = consulta.filter(
            or_(
                CarreraMateriaM.cod_mat.ilike(patron),
                CarreraMateriaM.cod_car_mat.ilike(patron),
                MateriasProgramasT.nom_mat.ilike(patron),
            )
        )

    filas = (
        consulta.order_by(
            CarreraMateriaM.semestre.asc(),
            MateriasProgramasT.nom_mat.asc(),
        )
        .limit(50)
        .all()
    )

    resultados = [
        {
            "cod_car_mat": f.cod_car_mat,
            "cod_car": f.cod_car,
            "cod_mat": f.cod_mat,
            "nom_mat": f.nom_mat or "",
            "pensum": f.pensum or "",
            "semestre": f.semestre or "",
            "etiqueta": f"[{f.cod_mat}] {f.nom_mat} ({f.pensum} - Sem. {f.semestre or 'N/A'})",
        }
        for f in filas
    ]
    return jsonify(resultados)


@api_bp.get("/carreras/<cod_dec>")
def api_carreras_por_decanato(cod_dec):
    carreras = (
        CarreraT.query.filter_by(cod_dec=cod_dec)
        .order_by(CarreraT.nom_car.asc())
        .all()
    )
    return jsonify([
        {"cod_car": c.cod_car, "nom_car": c.nom_car}
        for c in carreras
    ])

@api_bp.get("/pensums/<cod_car>")
def api_pensums(cod_car):
    pensums = db.session.query(CarreraMateriaM.pensum).filter_by(cod_car=cod_car).distinct().all()
    return jsonify([p[0] for p in pensums])


@api_bp.get("/materias-por-carrera/<cod_car>")
def api_materias_por_carrera(cod_car):
    filas = (
        db.session.query(
            CarreraMateriaM.cod_car_mat,
            CarreraMateriaM.cod_mat,
            CarreraMateriaM.pensum,
            CarreraMateriaM.semestre,
            MateriasProgramasT.nom_mat,
        )
        .join(
            MateriasProgramasT,
            CarreraMateriaM.cod_mat == MateriasProgramasT.cod_mat,
        )
        .filter(CarreraMateriaM.cod_car == cod_car)
        .order_by(CarreraMateriaM.semestre.asc(), MateriasProgramasT.nom_mat.asc())
        .all()
    )
    return jsonify([
        {
            "cod_car_mat": f.cod_car_mat,
            "cod_mat": f.cod_mat,
            "nom_mat": f.nom_mat or "",
            "pensum": f.pensum or "",
            "semestre": f.semestre or "",
        }
        for f in filas
    ])
    return jsonify(materias)


app.register_blueprint(api_bp)

# ==========================================
# 5. RUTAS PRINCIPALES (PANEL, CRUD Y EXPORTACIÓN)
# ==========================================

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 15

    query, filtros_activos = construir_query_programas()
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    programas = pagination.items
    carreras = CarreraT.query.order_by(CarreraT.nom_car.asc()).all()

    return render_template(
        'index.html',
        programas=programas,
        pagination=pagination,
        carreras=carreras,
        filtros=filtros_activos,
    )


@app.route('/exportar/csv')
def exportar_csv():
    query, _ = construir_query_programas()
    programas = query.all()

    salida = io.StringIO()
    escritor = csv.writer(salida, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    escritor.writerow([
        "ID",
        "Código",
        "Nombre del Programa",
        "Asignatura / Unidad Curricular",
        "Carrera",
        "Pensum",
        "Semestre",
        "Lapso",
        "Docente Responsable",
        "Estado Actual",
        "U.C.",
        "Créditos Acad.",
        "H.T.",
        "H.P.",
        "H.T.P.",
        "Archivo Adjunto",
        "Fecha Creación"
    ])

    for p in programas:
        docente_nombre = ""
        if p.docente_maestro:
            docente_nombre = f"{p.docente_maestro.nom_doc or ''} {p.docente_maestro.ape_doc or ''}".strip()

        cod_car = p.carrera_materia.cod_car if p.carrera_materia else ""
        pensum = p.carrera_materia.pensum if p.carrera_materia else ""
        lapso = p.cod_lap or p.lapso_academico or ""
        fecha_str = p.fecha_creacion.strftime("%Y-%m-%d %H:%M") if p.fecha_creacion else ""

        escritor.writerow([
            p.id,
            p.codigo or "",
            p.nombre or "",
            p.asignatura_unidad_Curricular or "",
            cod_car,
            pensum,
            p.semestre or "",
            lapso,
            docente_nombre,
            p.estado_actual or "",
            p.unidad_credito if p.unidad_credito is not None else "",
            p.credito_academico if p.credito_academico is not None else "",
            p.ht if p.ht is not None else "",
            p.hp if p.hp is not None else "",
            p.htp if p.htp is not None else "",
            p.archivo_word or "",
            fecha_str
        ])

    contenido_csv = salida.getvalue().encode("utf-8-sig")
    nombre_archivo = f"programas_ucla_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    respuesta = make_response(contenido_csv)
    respuesta.headers["Content-Type"] = "text/csv; charset=utf-8"
    respuesta.headers["Content-Disposition"] = f"attachment; filename={nombre_archivo}"
    return respuesta


@app.route('/agregar_docente', methods=['POST'])
def agregar_docente():
    cod_doc = (request.form.get('cod_doc') or request.form.get('codigo') or '').strip()
    ced_doc = (request.form.get('ced_doc') or request.form.get('cedula') or '').strip()
    nom_doc = (request.form.get('nom_doc') or request.form.get('nombre') or '').strip()
    ape_doc = (request.form.get('ape_doc') or request.form.get('apellido') or '').strip()
    cor_doc = (request.form.get('cor_doc') or request.form.get('correo') or '').strip()

    if not cod_doc and ced_doc:
        cod_doc = ced_doc

    if not cod_doc or not nom_doc:
        flash("Debe indicar al menos el código/cédula y el nombre del docente.", "warning")
        return redirect(url_for('index'))

    try:
        nuevo_docente = DocenteT(
            cod_doc=cod_doc,
            ced_doc=ced_doc or None,
            nom_doc=nom_doc,
            ape_doc=ape_doc or None,
            cor_doc=cor_doc or None,
        )
        db.session.add(nuevo_docente)
        db.session.commit()
        flash("Docente registrado exitosamente en docente_t.", "success")
    except IntegrityError as e:
        db.session.rollback()
        msg, categoria = mensaje_error_integridad(e)
        flash(msg, categoria)
    except Exception as e:
        db.session.rollback()
        flash(f"Error al registrar docente: {str(e)}", "danger")

    return redirect(url_for('index'))


@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    form = ProgramaForm()

    try:
        form.docente.choices = [
            (str(d.cod_doc).strip(), f"{(d.nom_doc or '').strip()} {(d.ape_doc or '').strip()}".strip())
            for d in DocenteT.query.all()
        ]
    except Exception:
        form.docente.choices = []

    decanatos = DecanatoT.query.order_by(DecanatoT.nom_dec.asc()).all()
    carreras = CarreraMateriaM.query.all()
    lapsos = LapsoAcademicoT.query.all()
    valid_cods = {val for val, _ in form.docente.choices}

    if request.method == 'POST':
        candidato = (request.form.get('cod_doc') or request.form.get('docente') or '').strip()
        if candidato in valid_cods:
            form.docente.data = candidato

    if form.validate_on_submit():
        cod_doc = (form.docente.data or '').strip()
        cod_car_mat = (request.form.get('cod_car_mat') or '').strip()
        cod_lap = (request.form.get('cod_lap') or '').strip()

        if not cod_doc or not cod_car_mat or not cod_lap:
            flash('Debe seleccionar obligatoriamente un Docente, una Materia del Pensum y un Lapso Académico.', 'danger')
            return render_template(
                'agregar.html',
                form=form,
                carreras=carreras,
                lapsos=lapsos,
                decanatos=decanatos,
            )

        car_mat = db.session.get(CarreraMateriaM, cod_car_mat)
        if not car_mat:
            flash('La asignación carrera-materia-pensum seleccionada no es válida.', 'danger')
            return render_template(
                'agregar.html',
                form=form,
                carreras=carreras,
                lapsos=lapsos,
                decanatos=decanatos,
            )

        if not db.session.get(DocenteT, cod_doc):
            flash('El docente seleccionado no existe en docente_t.', 'danger')
            return render_template(
                'agregar.html',
                form=form,
                carreras=carreras,
                lapsos=lapsos,
                decanatos=decanatos,
            )

        materia_maestra = db.session.get(MateriasProgramasT, car_mat.cod_mat)
        nombre_asignatura = materia_maestra.nom_mat if materia_maestra else "Asignatura Oficial UCLA"
        semestre_asignado = car_mat.semestre or 'I'

        try:
            nuevo_programa = Programa(
                nombre=form.nombre.data.strip(),
                asignatura_unidad_Curricular=nombre_asignatura,
                area_curricular=form.area_curricular.data.strip(),
                eje_curricular=form.eje_curricular.data.strip(),
                semestre=semestre_asignado,
                codigo=form.codigo.data.strip(),
                coordinador_asignatura_unidad=form.coordinador_asignatura_unidad.data.strip(),
                lapso_academico=cod_lap,
                prelacion=(form.prelacion.data or '').strip() or None,
                modalidad=form.modalidad.data.strip(),
                unidad_credito=form.unidad_credito.data,
                credito_academico=form.credito_academico.data,
                ht=form.ht.data,
                hp=form.hp.data,
                htp=form.htp.data,
                descripcion=form.descripcion.data.strip(),
                fecha_ultima_correcion=form.fecha_ultima_correcion.data,
                estado_actual='En Revisión',
                cod_doc=cod_doc,
                cod_car_mat=cod_car_mat,
                cod_lap=cod_lap,
            )
            db.session.add(nuevo_programa)
            db.session.flush()

            file = form.archivo_word.data or request.files.get('archivo_word')
            if file and file.filename != '' and allowed_file(file.filename):
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
                    observaciones="Carga inicial del programa académico.",
                )
                db.session.add(nueva_version)
                nuevo_programa.archivo_word = nombre_original
                nuevo_programa.hash_archivo = hash_sha256

            nueva_revision = RevisionProgramaM(
                cod_pro=f"PROG-{nuevo_programa.id}",
                cod_doc=cod_doc,
                cod_car_mat=cod_car_mat,
                fec_rev=date.today(),
                est_rev='En Revisión',
                nom_arc=nuevo_programa.archivo_word or 'Sin Archivo',
                obs_rev=(form.descripcion.data or '')[:200],
                cod_lap=cod_lap,
            )
            db.session.add(nueva_revision)
            db.session.commit()

            flash("Programa académico registrado exitosamente con integridad curricular.", "success")
            return redirect(url_for('index'))

        except IntegrityError as e:
            db.session.rollback()
            msg, categoria = mensaje_error_integridad(e)
            flash(msg, categoria)
        except Exception as e:
            db.session.rollback()
            flash(f"Error inesperado: {str(e)}", "danger")

    return render_template(
        'agregar.html',
        form=form,
        carreras=carreras,
        lapsos=lapsos,
        decanatos=decanatos,
    )


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    programa = db.session.get(Programa, id) or Programa.query.get_or_404(id)
    form = ProgramaForm(obj=programa)

    try:
        form.docente.choices = [
            (str(d.cod_doc).strip(), f"{(d.nom_doc or '').strip()} {(d.ape_doc or '').strip()}".strip())
            for d in DocenteT.query.all()
        ]
    except Exception:
        form.docente.choices = []

    decanatos = DecanatoT.query.order_by(DecanatoT.nom_dec.asc()).all()
    carreras = CarreraMateriaM.query.all()
    lapsos = LapsoAcademicoT.query.all()
    valid_cods = {val for val, _ in form.docente.choices}
    docente_actual = str(programa.cod_doc or '').strip()

    if request.method == 'GET':
        if docente_actual in valid_cods:
            form.docente.data = docente_actual
    elif request.method == 'POST':
        candidato = (request.form.get('cod_doc') or request.form.get('docente') or '').strip()
        if candidato in valid_cods:
            form.docente.data = candidato
        elif docente_actual in valid_cods:
            form.docente.data = docente_actual

    if form.validate_on_submit():
        cod_doc = (form.docente.data or '').strip()
        cod_car_mat = (request.form.get('cod_car_mat') or '').strip()
        cod_lap = (request.form.get('cod_lap') or '').strip()
        estado_seleccionado = (request.form.get('estado_actual') or programa.estado_actual or 'En Revisión').strip()
        observacion_rev = (request.form.get('observaciones_revision') or '').strip()

        if not cod_doc or not cod_car_mat or not cod_lap:
            flash('Debe seleccionar obligatoriamente un Docente, una Materia del Pensum y un Lapso Académico.', 'danger')
            return render_template(
                'editar.html',
                form=form,
                programa=programa,
                carreras=carreras,
                lapsos=lapsos,
                decanatos=decanatos,
                estado_seleccionado=estado_seleccionado,
                observacion_rev=observacion_rev,
            )
        car_mat = db.session.get(CarreraMateriaM, cod_car_mat)
        if not car_mat:
            flash('La asignación carrera-materia-pensum seleccionada no es válida.', 'danger')
            return render_template(
                'editar.html',
                form=form,
                programa=programa,
                carreras=carreras,
                lapsos=lapsos,
                decanatos=decanatos,
            )

        if not db.session.get(DocenteT, cod_doc):
            flash('El docente seleccionado no existe en docente_t.', 'danger')
            return render_template(
                'editar.html',
                form=form,
                programa=programa,
                carreras=carreras,
                lapsos=lapsos,
                decanatos=decanatos,
            )

        materia_maestra = db.session.get(MateriasProgramasT, car_mat.cod_mat)
        programa.asignatura_unidad_Curricular = materia_maestra.nom_mat if materia_maestra else form.nombre.data.strip()
        programa.semestre = car_mat.semestre or programa.semestre
        programa.cod_car_mat = cod_car_mat

        try:
            programa.nombre = form.nombre.data.strip()
            programa.area_curricular = form.area_curricular.data.strip()
            programa.eje_curricular = form.eje_curricular.data.strip()
            programa.codigo = form.codigo.data.strip()
            programa.coordinador_asignatura_unidad = form.coordinador_asignatura_unidad.data.strip()
            programa.lapso_academico = cod_lap
            programa.prelacion = (form.prelacion.data or '').strip() or None
            programa.modalidad = form.modalidad.data.strip()
            programa.unidad_credito = form.unidad_credito.data
            programa.credito_academico = form.credito_academico.data
            programa.ht = form.ht.data
            programa.hp = form.hp.data
            programa.htp = form.htp.data
            programa.descripcion = form.descripcion.data.strip()
            programa.fecha_ultima_correcion = form.fecha_ultima_correcion.data
            programa.cod_doc = cod_doc
            programa.cod_lap = cod_lap
            programa.estado_actual = estado_seleccionado
               
            file = request.files.get('archivo_word')
            if file and file.filename != '' and allowed_file(file.filename):
                nombre_original = secure_filename(file.filename)
                file.stream.seek(0)
                bytes_archivo = file.stream.read()
                hash_sha256 = hashlib.sha256(bytes_archivo).hexdigest()

                ultima_version = (
                    ProgramaVersion.query.filter_by(programa_id=programa.id)
                    .order_by(ProgramaVersion.version_numero.desc())
                    .first()
                )
                nuevo_num_version = (ultima_version.version_numero + 1) if ultima_version else 1

                nueva_version = ProgramaVersion(
                    programa_id=programa.id,
                    version_numero=nuevo_num_version,
                    nombre_archivo_real=nombre_original,
                    archivo_binario=bytes_archivo,
                    enviado_por='Profesor',
                    observaciones="Actualización del programa académico.",
                )
                db.session.add(nueva_version)
                programa.archivo_word = nombre_original
                programa.hash_archivo = hash_sha256
                
            # Actualiza o registra la traza vigente en revision_programa_m (clave: PROG-<id>)
            obs_final = observacion_rev or (
                "Devuelto al docente responsable para correcciones en el documento."
                if estado_seleccionado == 'Devuelto al Profesor'
                else (form.descripcion.data or '')
            )
            codigo_revision = f"PROG-{programa.id}"
            revision_existente = RevisionProgramaM.query.filter_by(cod_pro=codigo_revision).first()

            if revision_existente:
                revision_existente.cod_doc = cod_doc
                revision_existente.cod_car_mat = cod_car_mat
                revision_existente.fec_rev = date.today()
                revision_existente.est_rev = estado_seleccionado
                revision_existente.nom_arc = programa.archivo_word or 'Sin Archivo'
                revision_existente.obs_rev = obs_final
                revision_existente.cod_lap = cod_lap
            else:
                nueva_revision = RevisionProgramaM(
                    cod_pro=codigo_revision,
                    cod_doc=cod_doc,
                    cod_car_mat=cod_car_mat,
                    fec_rev=date.today(),
                    est_rev=estado_seleccionado,
                    nom_arc=programa.archivo_word or 'Sin Archivo',
                    obs_rev=obs_final,
                    cod_lap=cod_lap,
                )
                db.session.add(nueva_revision)
            
            db.session.commit()
            flash("Programa académico actualizado exitosamente.", "success")
            return redirect(url_for('index'))

        except IntegrityError as e:
            db.session.rollback()
            msg, categoria = mensaje_error_integridad(e)
            flash(msg, categoria)
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar: {str(e)}", "danger")

    return render_template(
        'editar.html',
        form=form,
        programa=programa,
        carreras=carreras,
        lapsos=lapsos,
        decanatos=decanatos,
    )
@app.route('/eliminar/<int:id>', methods=['POST', 'GET'])
def eliminar(id):
    programa = Programa.query.get_or_404(id)
    try:
        db.session.delete(programa)
        db.session.commit()
        flash("Programa y su historial eliminados correctamente.", "success")
    except IntegrityError as e:
        db.session.rollback()
        msg, categoria = mensaje_error_integridad(e)
        flash(msg, categoria)
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar: {str(e)}", "danger")
    return redirect(url_for('index'))


@app.route('/ver/<int:id>')
def ver(id):
    programa = Programa.query.options(joinedload(Programa.versiones)).get_or_404(id)
    return render_template('ver.html', programa=programa)


@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}


if __name__ == '__main__':
    app.run(debug=True)