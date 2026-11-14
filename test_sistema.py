import hashlib
from datetime import datetime
from sqlalchemy.orm import joinedload
from app import app, db, Docente, Programa, ProgramaVersion

def ejecutar_diagnostico():
    print("=" * 60)
    print("🔬 SISTEMA DE GESTIÓN DE PROGRAMAS - DIAGNÓSTICO DE CONSOLA")
    print("=" * 60)

    with app.app_context():
        # 1. Limpieza previa para la prueba
        print("\n🔹 [1/5] Inicializando entorno de prueba...")
        db.create_all()
        
        # 💡 NUEVA LIMPIEZA BLINDADA: Eliminamos el programa viejo si existe
        programa_test = Programa.query.filter_by(codigo="COMP-101").first()
        if programa_test:
            db.session.delete(programa_test)
            db.session.commit()
            print("   - Programa 'COMP-101' de prueba previo eliminado.")
        
        # Limpiamos docente de prueba anteriores para evitar conflictos de integridad
        docente_test = Docente.query.filter_by(nombre="Dr. Manuel Anzola (Prueba)").first()
        if docente_test:
            db.session.delete(docente_test)
            db.session.commit()
            print("   - Registros de prueba previos eliminados.")

        # 2. Creación del Docente
        print("\n🔹 [2/5] Insertando Docente de prueba...")
        nuevo_docente = Docente(
            nombre="Dr. Manuel Anzola (Prueba)",
            email="manzola.prueba@ucla.edu.ve"
        )
        db.session.add(nuevo_docente)
        db.session.commit()
        print(f"   ✅ Docente registrado exitosamente (ID: {nuevo_docente.id})")

        # 3. Creación del Programa Inicial (Versión 1)
        print("\n🔹 [3/5] Creando Programa Analítico Inicial (V1)...")
        codigo_materia = "COMP-101"
        
        # Simulamos la lectura de un archivo Word de prueba en memoria
        contenido_archivo_v1 = b"Contenido binario simulado del archivo Word original de Computacion I."
        hash_v1 = hashlib.sha256(contenido_archivo_v1).hexdigest()
        nombre_doc_v1 = "programa_computacion_i_v1.docx"

        nuevo_programa = Programa(
            codigo=codigo_materia,
            nombre="Computación I",
            asignatura_unidad_Curricular="Algoritmos y Programación",
            area_curricular="Formación Profesional Especializada",
            eje_curricular="Sistemas de Información",
            semestre="I Semestre",
            coordinador_asignatura_unidad="Ing. Juana Pérez",
            lapso_academico="2026-1",
            modalidad="Presencial",
            docente_id=nuevo_docente.id,
            unidad_credito=4,
            credito_academico=4,
            ht=2,
            hp=4,
            htp=6,
            descripcion="Introducción al desarrollo de algoritmos y estructuras de datos utilizando Python.",
            estado_actual="En Revisión",
            archivo_word=nombre_doc_v1,
            hash_archivo=hash_v1
        )
        db.session.add(nuevo_programa)
        db.session.flush() # Flush para obtener el ID generado por MySQL

        # Registramos la versión 1 en el historial
        v1 = ProgramaVersion(
            programa_id=nuevo_programa.id,
            version_numero=1,
            nombre_archivo_real=nombre_doc_v1,
            archivo_binario=contenido_archivo_v1,
            enviado_por="Profesor",
            observaciones="Carga inicial del programa de Computación I."
        )
        db.session.add(v1)
        db.session.commit()
        print(f"   ✅ Programa {codigo_materia} registrado con Versión 1 en el repositorio BLOB.")

        # 4. Simulación de Modificación / Segunda Versión (Versión 2)
        print("\n🔹 [4/5] Simulando una corrección del evaluador (Generando V2)...")
        
        # Buscamos el programa recién creado
        programa_a_editar = Programa.query.filter_by(codigo=codigo_materia).first()
        
        # Simulamos el nuevo archivo corregido por el docente
        contenido_archivo_v2 = b"Contenido binario corregido. Se agregaron unidades de Flask y SQLAlchemy."
        hash_v2 = hashlib.sha256(contenido_archivo_v2).hexdigest()
        nombre_doc_v2 = "programa_computacion_i_v2_corregido.docx"

        # Calculamos dinámicamente la nueva versión
        num_versiones = ProgramaVersion.query.filter_by(programa_id=programa_a_editar.id).count()
        nueva_version_num = num_versiones + 1

        v2 = ProgramaVersion(
            programa_id=programa_a_editar.id,
            version_numero=nueva_version_num,
            nombre_archivo_real=nombre_doc_v2,
            archivo_binario=contenido_archivo_v2,
            enviado_por="Profesor",
            observaciones="Se incorporaron las observaciones sugeridas del módulo de persistencia de datos."
        )
        db.session.add(v2)

        # Actualizamos la cabecera principal del programa
        programa_a_editar.archivo_word = nombre_doc_v2
        programa_a_editar.hash_archivo = hash_v2
        programa_a_editar.estado_actual = "Reenviado"
        db.session.commit()
        print(f"   ✅ Versión {nueva_version_num} inyectada con éxito. Estado actualizado a 'Reenviado'.")

        # 5. Verificación Final del Control de Cambios
        print("\n🔹 [5/5] Consultando el historial completo desde MySQL...")
        prog_final = Programa.query.options(joinedload(Programa.versiones)).filter_by(codigo=codigo_materia).first()
        
        print("-" * 60)
        print(f" Materia: {prog_final.nombre} ({prog_final.codigo})")
        print(f" Estado Actual en Flujo: {prog_final.estado_actual}")
        print(f" Último Archivo Activo: {prog_final.archivo_word}")
        print(f" Hash SHA-256 de Integridad: {prog_final.hash_archivo}")
        print("-" * 60)
        print(" HISTORIAL DE CONTROL DE CAMBIOS DETECTADO:")
        
        # Ordenamos de mayor a menor número de versión
        versiones_ordenadas = sorted(prog_final.versiones, key=lambda x: x.version_numero, reverse=True)
        for v in versiones_ordenadas:
            print(f"   • [V{v.version_numero}] Archivo: {v.nombre_archivo_real} | Por: {v.enviado_por} | Fecha: {v.fecha_subida.strftime('%H:%M:%S')}")
            print(f"     Nota: \"{v.observaciones}\"")
        print("-" * 60)
        print("\n🎉 ¡DIAGNÓSTICO COMPLETADO CON ÉXITO! El backend responde por los cuatro costados.")
        print("=" * 60)

if __name__ == "__main__":
    ejecutar_diagnostico()