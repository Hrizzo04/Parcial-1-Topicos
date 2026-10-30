"""Catálogo de consultas de lectura disponibles para el agente."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QueryDefinition:
    identificador: str
    descripcion: str
    sql: str


QUERIES: dict[str, QueryDefinition] = {
    # Consulta de utilería / exploración
    "listar_tablas": QueryDefinition(
        identificador="listar_tablas",
        descripcion="Listar tablas y vistas del Data Mart",
        sql=(
            'SELECT table_name AS tabla '
            'FROM information_schema.tables '
            'WHERE table_schema = :schema '
            "AND table_type IN ('BASE TABLE', 'VIEW') "
            'ORDER BY table_name'
        ),
    ),
    
    # 1. ¿Cuál fue el ingreso neto por mes?
    "Q1_INGRESO_NETO_POR_MES": QueryDefinition(
        identificador="Q1_INGRESO_NETO_POR_MES",
        descripcion="Ingreso neto agrupado por mes y año",
        sql=(
            'SELECT t."Año", t."Mes", t."NombreMes", '
            'SUM(f."IngresoNeto") AS "IngresoNetoTotal" '
            'FROM "FactVentas" f '
            'JOIN "DimTiempo" t ON f."TiempoSK" = t."TiempoSK" '
            'GROUP BY t."Año", t."Mes", t."NombreMes" '
            'ORDER BY t."Año", t."Mes";'
        ),
    ),

    # 2. ¿Cuáles son las cinco categorías con mayor margen bruto?
    "Q2_TOP_CATEGORIAS_MARGEN": QueryDefinition(
        identificador="Q2_TOP_CATEGORIAS_MARGEN",
        descripcion="Top N categorías ordenadas por margen bruto acumulado",
        sql=(
            'SELECT p."Categoria", '
            'SUM(f."MargenBruto") AS "MargenBrutoTotal", '
            'ROUND((SUM(f."MargenBruto") / NULLIF(SUM(f."IngresoNeto"), 0)) * 100, 2) AS "PorcentajeMargen" '
            'FROM "FactVentas" f '
            'JOIN "DimProducto" p ON f."ProductoSK" = p."ProductoSK" '
            'GROUP BY p."Categoria" '
            'ORDER BY "MargenBrutoTotal" DESC '
            'LIMIT :limite;'
        ),
    ),

    # 3. ¿Qué sucursal presenta el ticket promedio más alto?
    "Q3_TICKET_PROMEDIO_SUCURSAL": QueryDefinition(
        identificador="Q3_TICKET_PROMEDIO_SUCURSAL",
        descripcion="Sucursal con el mayor ticket promedio por transacción",
        sql=(
            'SELECT s."NombreSucursal", s."Ciudad", '
            'ROUND(SUM(f."IngresoNeto") / NULLIF(COUNT(DISTINCT f."NumeroTransaccion"), 0), 2) AS "TicketPromedio", '
            'COUNT(DISTINCT f."NumeroTransaccion") AS "TotalTransacciones" '
            'FROM "FactVentas" f '
            'JOIN "DimSucursal" s ON f."SucursalSK" = s."SucursalSK" '
            'GROUP BY s."NombreSucursal", s."Ciudad" '
            'ORDER BY "TicketPromedio" DESC '
            'LIMIT 1;'
        ),
    ),

    # 4. ¿Qué segmento de clientes redujo más su volumen de compra?
    "Q4_CAMBIO_VOLUMEN_SEGMENTO": QueryDefinition(
        identificador="Q4_CAMBIO_VOLUMEN_SEGMENTO",
        descripcion="Volumen total de unidades e ingresos por segmento de cliente",
        sql=(
            'SELECT c."Segmento", '
            'SUM(f."Cantidad") AS "VolumenTotal", '
            'SUM(f."IngresoNeto") AS "IngresoTotal" '
            'FROM "FactVentas" f '
            'JOIN "DimCliente" c ON f."ClienteSK" = c."ClienteSK" '
            'GROUP BY c."Segmento" '
            'ORDER BY "VolumenTotal" ASC;'
        ),
    ),

    # 5. ¿Qué canal concentra el mayor valor de ventas?
    "Q5_CANAL_MAYOR_VENTA": QueryDefinition(
        identificador="Q5_CANAL_MAYOR_VENTA",
        descripcion="Canal comercial con mayor total de ventas netas",
        sql=(
            'SELECT cn."NombreCanal", '
            'SUM(f."IngresoNeto") AS "VentaTotalNeto" '
            'FROM "FactVentas" f '
            'JOIN "DimCanal" cn ON f."CanalSK" = cn."CanalSK" '
            'GROUP BY cn."NombreCanal" '
            'ORDER BY "VentaTotalNeto" DESC '
            'LIMIT 1;'
        ),
    ),

    # 6. Compare el margen de dos canales durante los últimos tres meses disponibles
    "Q6_COMPARAR_MARGEN_CANALES": QueryDefinition(
        identificador="Q6_COMPARAR_MARGEN_CANALES",
        descripcion="Comparativa de margen bruto e ingreso entre canales en un rango de meses",
        sql=(
            'SELECT cn."NombreCanal", '
            'SUM(f."MargenBruto") AS "MargenBrutoTotal", '
            'SUM(f."IngresoNeto") AS "IngresoNetoTotal", '
            'ROUND((SUM(f."MargenBruto") / NULLIF(SUM(f."IngresoNeto"), 0)) * 100, 2) AS "PorcentajeMargen" '
            'FROM "FactVentas" f '
            'JOIN "DimCanal" cn ON f."CanalSK" = cn."CanalSK" '
            'JOIN "DimTiempo" t ON f."TiempoSK" = t."TiempoSK" '
            'WHERE t."Mes" BETWEEN :mes_inicio AND :mes_fin '
            'GROUP BY cn."NombreCanal" '
            'ORDER BY "MargenBrutoTotal" DESC;'
        ),
    ),

    # 7. ¿Qué producto lidera las ventas dentro de una categoría determinada?
    "Q7_PRODUCTO_LIDER_CATEGORIA": QueryDefinition(
        identificador="Q7_PRODUCTO_LIDER_CATEGORIA",
        descripcion="Producto con mayor facturación en una categoría específica",
        sql=(
            'SELECT p."NombreProducto", p."Categoria", '
            'SUM(f."IngresoNeto") AS "VentaTotal", '
            'SUM(f."Cantidad") AS "UnidadesVendidas" '
            'FROM "FactVentas" f '
            'JOIN "DimProducto" p ON f."ProductoSK" = p."ProductoSK" '
            'WHERE UPPER(p."Categoria") = UPPER(:categoria) '
            'GROUP BY p."NombreProducto", p."Categoria" '
            'ORDER BY "VentaTotal" DESC '
            'LIMIT 1;'
        ),
    ),
}


def get_query(query_id: str) -> QueryDefinition:
    """Obtiene una consulta del catálogo o informa que no está permitida."""
    try:
        return QUERIES[query_id]
    except KeyError as error:
        raise ValueError(f"Consulta no permitida: {query_id}") from error


# Mapeo plano para compatibilidad directa con el motor del agente
CATALOGO_CONSULTAS: dict[str, str] = {
    identificador: query.sql for identificador, query in QUERIES.items()
}