from datetime import date, datetime
from sqlalchemy import text
from app import app, db

def ejecutar_seeder():
    print("\n" + "=" * 60)
    print("CARGANDO CATÁLOGO MAESTRO CURRICULAR (UCLA - programas_ucla)")
    print("=" * 60)

    with app.app_context():
        with db.engine.begin() as conn:
            # 1. Decanatos (decanato_t)
            decanatos = [
                ("DCYT", "Decanato de Ciencias y Tecnología"),
                ("DEHA", "Decanato de Humanidades y Artes"),
            ]
            for cod, nom in decanatos:
                conn.execute(
                    text("INSERT IGNORE INTO decanato_t (cod_dec, nom_dec) VALUES (:c, :n)"),
                    {"c": cod, "n": nom},
                )

            # 2. Carreras (carrera_t)
            carreras = [
                ("ING-INF", "Ingeniería en Informática", "DCYT"),
                ("ANA-SIS", "Análisis de Sistemas", "DCYT"),
                ("LIC-MAT", "Licenciatura en Matemáticas", "DCYT"),
            ]
            for cod, nom, dec in carreras:
                conn.execute(
                    text("INSERT IGNORE INTO carrera_t (cod_car, nom_car, cod_dec) VALUES (:c, :n, :d)"),
                    {"c": cod, "n": nom, "d": dec},
                )

            # 3. Materias Maestras (materias_programas_t)
            materias = [
                ("MAT-101", "Matemática I"),
                ("PRG-102", "Algoritmos y Programación I"),
                ("BDD-301", "Bases de Datos I"),
                ("ING-401", "Ingeniería de Software I"),
                ("SIS-405", "Sistemas Operativos"),
                ("RED-502", "Redes de Computadoras"),
                ("AUD-508", "Auditoría de Sistemas"),
            ]
            for cod, nom in materias:
                conn.execute(
                    text("INSERT IGNORE INTO materias_programas_t (cod_mat, nom_mat) VALUES (:c, :n)"),
                    {"c": cod, "n": nom},
                )

            # 4. Relación Carrera - Pensum - Materia (carrera_materia_m)
            # Aquí se amarra qué materias pertenecen a cada carrera y pensum
            carrera_materias = [
                ("CM-INF22-MAT101", "ING-INF", "MAT-101", "Pensum 2022", "I"),
                ("CM-INF22-PRG102", "ING-INF", "PRG-102", "Pensum 2022", "I"),
                ("CM-INF22-BDD301", "ING-INF", "BDD-301", "Pensum 2022", "V"),
                ("CM-INF22-ING401", "ING-INF", "ING-401", "Pensum 2022", "VI"),
                ("CM-INF22-SIS405", "ING-INF", "SIS-405", "Pensum 2022", "VI"),
                ("CM-INF12-BDD301", "ING-INF", "BDD-301", "Pensum 2012", "V"),
                ("CM-INF12-RED502", "ING-INF", "RED-502", "Pensum 2012", "VII"),
                ("CM-ANA20-PRG102", "ANA-SIS", "PRG-102", "Pensum 2020", "I"),
                ("CM-ANA20-BDD301", "ANA-SIS", "BDD-301", "Pensum 2020", "IV"),
                ("CM-ANA20-AUD508", "ANA-SIS", "AUD-508", "Pensum 2020", "VI"),
            ]
            for ccm, cc, cm, pen, sem in carrera_materias:
                conn.execute(
                    text("""
                        INSERT IGNORE INTO carrera_materia_m (cod_car_mat, cod_car, cod_mat, pensum, semestre)
                        VALUES (:ccm, :cc, :cm, :pen, :sem)
                    """),
                    {"ccm": ccm, "cc": cc, "cm": cm, "pen": pen, "sem": sem},
                )

            # 5. Docentes Maestros (docente_t)
            docentes = [
                ("DOC-001", "Alejandro", "Silva", "V-12456789", "0414-5550101", "asilva@ucla.edu.ve"),
                ("DOC-002", "María Elena", "Rodríguez", "V-11987654", "0412-5550202", "merodriguez@ucla.edu.ve"),
                ("DOC-003", "Carlos", "Mendoza", "V-14321654", "0416-5550303", "cmendoza@ucla.edu.ve"),
                ("DOC-004", "Beatriz", "Torrealba", "V-13654987", "0424-5550404", "btorrealba@ucla.edu.ve"),
                ("DOC-005", "Luis Javier", "Gómez", "V-10789456", "0414-5550505", "ljgomez@ucla.edu.ve"),
                ("DOC-006", "José Luis", "Gavidia", "V-9876543", "0414-5550606", "jgavidia@ucla.edu.ve"),
            ]
            for cod, nom, ape, ced, tel, cor in docentes:
                conn.execute(
                    text("""
                        INSERT IGNORE INTO docente_t (cod_doc, nom_doc, ape_doc, ced_doc, tel_doc, cor_doc)
                        VALUES (:c, :n, :a, :ced, :t, :cor)
                    """),
                    {"c": cod, "n": nom, "a": ape, "ced": ced, "t": tel, "cor": cor},
                )

            # 6. Lapsos Académicos (lapso_academico_t)
            lapsos = [
                ("2026-1", "Lapso Académico 2026-I", date(2026, 3, 1), date(2026, 7, 31), "N"),
                ("2026-2", "Lapso Académico 2026-II", date(2026, 9, 15), date(2027, 2, 15), "S"),
            ]
            for cod, des, fi, ff, act in lapsos:
                conn.execute(
                    text("""
                        INSERT IGNORE INTO lapso_academico_t (cod_lap, des_lap, fec_ini, fec_fin, est_act)
                        VALUES (:c, :d, :fi, :ff, :act)
                    """),
                    {"c": cod, "d": des, "fi": fi, "ff": ff, "act": act},
                )

        print("Catálogo maestro cargado exitosamente en programas_ucla.")
        print("=" * 60 + "\n")

if __name__ == "__main__":
    ejecutar_seeder()