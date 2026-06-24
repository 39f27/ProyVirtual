BEGIN TRANSACTION;
CREATE TABLE docentes (
	id INTEGER NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	email VARCHAR(120), 
	PRIMARY KEY (id), 
	UNIQUE (email)
);
CREATE TABLE programa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    codigo TEXT NOT NULL UNIQUE,
    asignatura_unidad_curricular TEXT NOT NULL,
    area_curricular TEXT NOT NULL,
    eje_curricular TEXT NOT NULL,
    semestre INTEGER NOT NULL,
    coordinador_asignatura_unidad TEXT NOT NULL,
    lapso_academico TEXT NOT NULL,
    prelacion TEXT NOT NULL,
    modalidad TEXT NOT NULL,
    docentes TEXT NOT NULL,
    unidad_credito INTEGER NOT NULL,
    credito_academico INTEGER NOT NULL,
    ht INTEGER NOT NULL,
    hp INTEGER NOT NULL,
    htp INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    fecha_ultima_correcion TEXT NOT NULL,
    archivo_word TEXT,
    hash_archivo TEXT
);
INSERT INTO "programa" VALUES(1,'Programación Básica','PRG101','Introducción a la Programación','Informática','Software',1,'Juan Perez','2025-1','Ninguna','Presencial','Juan Perez, Maria Lopez',3,4,30,20,10,'Curso introductorio de programación','2025-07-01',NULL,NULL);
CREATE TABLE programas (
	id INTEGER NOT NULL, 
	nombre VARCHAR(200) NOT NULL, 
	"asignatura_unidad_Curricular" VARCHAR(100) NOT NULL, 
	area_curricular VARCHAR(100) NOT NULL, 
	eje_curricular VARCHAR(100) NOT NULL, 
	semestre INTEGER NOT NULL, 
	codigo VARCHAR(20) NOT NULL, 
	coordinador_asignatura_unidad VARCHAR(100) NOT NULL, 
	lapso_academico VARCHAR(50) NOT NULL, 
	prelacion VARCHAR(50), 
	modalidad VARCHAR(50) NOT NULL, 
	docentes VARCHAR(200) NOT NULL, 
	unidad_credito INTEGER NOT NULL, 
	credito_academico INTEGER NOT NULL, 
	ht INTEGER NOT NULL, 
	hp INTEGER NOT NULL, 
	htp INTEGER NOT NULL, 
	descripcion TEXT NOT NULL, 
	fecha_ultima_correcion DATE, 
	archivo_word VARCHAR(300), 
	hash_archivo VARCHAR(64), 
	docente_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(docente_id) REFERENCES docentes (id)
);
INSERT INTO "programas" VALUES(1,'Gavidia José Luis ','Metodología de la Investigación I ','Estudios Generales','Formación General',1,'LPS113','Prof. Zorely Silva','2023-2','Ninguna','Presencial y Semipresencial','Prof. Jhoanelda Sánchez',2,4,2,1,3,'Programa para ser revisado y autorizado','2025-07-25','programa_1_2466cd93.docx','2466cd93a1cca614204c4e312449022267c5b44bd671d8daf72d31ef9cdd6981',NULL);
CREATE INDEX idx_busqueda ON programas (semestre, area_curricular, eje_curricular);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('programa',1);
COMMIT;
