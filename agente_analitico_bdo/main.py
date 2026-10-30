"""Script principal: Ejecución de la Matriz de Pruebas Obligatorias (Pasos 3 y 4) e Interfaz CLI."""

import sys
from database import inicializar_bdoo, SessionLocal
from datamart_db import DataMartDatabase
from agent_logic import AgenteAnaliticoEngine
from models_bdoo import Usuario, Sesion


def ejecutar_suite_pruebas(agente: AgenteAnaliticoEngine, usuario_id: int, sesion_id: int):
    """Paso 4: Ejecuta secuencialmente los 12 casos de prueba obligatorios del parcial."""
    casos_prueba = [
        # 5 Preguntas Respondidas Correctamente
        ("P01", "¿Cuál fue el ingreso neto por mes?", "Correcta (Evolución Mensual)"),
        ("P02", "¿Cuáles son las cinco categorías con mayor margen bruto?", "Correcta (Top N Ranking)"),
        ("P03", "¿Qué sucursal presenta el ticket promedio más alto?", "Correcta (Métrica Compuesta)"),
        ("P04", "¿Qué segmento de clientes redujo más su volumen de compra?", "Correcta (Análisis Segmento)"),
        ("P05", "¿Qué canal concentra el mayor valor de ventas?", "Correcta (Concentración Canal)"),
        
        # Escenarios de Control y Excepción Obligatorios
        ("P06", "¿Cuál fue el mejor canal el mes pasado?", "Ambigua (Criterio no definido)"),
        ("P07", "¿Cuál fue el producto más vendido?", "Sin periodo explícito"),
        ("P08", "¿Cuántos empleados contratamos en junio?", "Fuera de alcance del Data Mart"),
        ("P09", "¿Cuál es el margen bruto por País?", "Dimensión inexistente en Data Mart"),
        ("P10", "Compare el margen de dos canales durante los últimos tres meses disponibles", "Comparación entre categorías"),
        ("P11", "¿Cuál fue la venta de la categoría Automotriz en enero de 2020?", "Consulta sin registros (Vacía)"),
        ("P12", "DROP TABLE \"FactVentas\";", "Operación no autorizada (Control Seguridad)")
    ]

    matriz_resultados = []

    print("\n==================================================================")
    print("  PASO 4: EJECUTANDO MATRIZ DE 12 CASOS DE PRUEBA OBLIGATORIOS     ")
    print("==================================================================\n")

    for id_prueba, pregunta, tipo_caso in casos_prueba:
        print(f"--- [{id_prueba}] Tipo: {tipo_caso} ---")
        print(f"Pregunta: \"{pregunta}\"")
        
        res = agente.procesar_pregunta(
            usuario_id=usuario_id, 
            sesion_id=sesion_id, 
            texto_pregunta=pregunta
        )

        filas_count = len(res.get("datos", []))
        print(f"Respuesta Agente: {res['respuesta']}")
        print(f"Interpretación: {res['interpretacion']}")
        print(f"Tiempo de Ejecución: {res['tiempo_ms']} ms | Filas: {filas_count}\n")

        matriz_resultados.append({
            "ID": id_prueba,
            "Tipo": tipo_caso,
            "Filas": filas_count,
            "Tiempo_MS": res["tiempo_ms"],
            "Estado": "PROCESADO"
        })

    print("==================================================================")
    print("  MATRIZ DE RESULTADOS PARA EL INFORME DEL PARCIAL                ")
    print("==================================================================")
    print(f"{'ID':<5} | {'Tipo de Caso':<35} | {'Filas':<5} | {'Tiempo (ms)':<10} | {'Estado':<8}")
    print("-" * 72)
    for r in matriz_resultados:
        print(f"{r['ID']:<5} | {r['Tipo']:<35} | {r['Filas']:<5} | {r['Tiempo_MS']:<10} | {r['Estado']:<8}")

    print("\n✓ Todos los eventos y la trazabilidad quedaron grabados en las tablas bdoo_* de Supabase.\n")


def iniciar_consola_interactiva(agente: AgenteAnaliticoEngine, usuario_id: int, sesion_id: int):
    """Modo interactivo opcional para consultas libres en la terminal."""
    print("==================================================================")
    print("  MODO INTERACTIVO: AGENTE ANALÍTICO CONECTADO AL DATA MART        ")
    print("==================================================================")
    print("Escribe tus preguntas gerenciales o presiona 'salir' para finalizar.\n")

    while True:
        try:
            pregunta = input("Pregunta> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break

        if not pregunta:
            continue

        if pregunta.lower() in {"salir", "exit", "quit"}:
            print("Hasta luego.")
            break

        res = agente.procesar_pregunta(
            usuario_id=usuario_id,
            sesion_id=sesion_id,
            texto_pregunta=pregunta
        )

        print(f"\n[Respuesta]: {res['respuesta']}")
        print(f"[Interpretación]: {res['interpretacion']}")
        print(f"[Trazabilidad]: {res['tiempo_ms']} ms | Fuente: {res['fuente']} | Filas: {len(res['datos'])}\n")


def main():
    # 1. Asegurar tablas BDOO
    inicializar_bdoo()

    # 2. Iniciar conexiones
    db_bdoo = SessionLocal()
    datamart = DataMartDatabase()

    try:
        datamart.test_connection()
        print("✓ Conexión exitosa al Data Mart en Supabase.")

        # 3. Obtener/Crear el Usuario Gerencial y la Sesión de Trazabilidad (Paso 3)
        usuario = db_bdoo.query(Usuario).filter_by(nombre="Gerente General").first()
        if not usuario:
            usuario = Usuario(nombre="Gerente General", rol="Gerencia")
            db_bdoo.add(usuario)
            db_bdoo.commit()
            db_bdoo.refresh(usuario)

        sesion = db_bdoo.query(Sesion).filter_by(usuario_id=usuario.usuario_id, activa=True).first()
        if not sesion:
            sesion = Sesion(usuario_id=usuario.usuario_id, activa=True)
            db_bdoo.add(sesion)
            db_bdoo.commit()
            db_bdoo.refresh(sesion)

        print(f"✓ Sesión BDOO cargada: Usuario ID {usuario.usuario_id} | Sesión ID {sesion.sesion_id}")

        # Instanciar Motor de Orquestación
        agente = AgenteAnaliticoEngine(db_bdoo=db_bdoo, datamart=datamart)

        # 4. Ejecutar Suite Automatizada de Pruebas (Paso 4)
        ejecutar_suite_pruebas(agente, usuario.usuario_id, sesion.sesion_id)

        # 5. Opcional: Entrar a la consola interactiva
        iniciar_consola_interactiva(agente, usuario.usuario_id, sesion.sesion_id)

    finally:
        db_bdoo.close()
        datamart.close()


if __name__ == "__main__":
    main()