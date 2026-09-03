import logging
from datos_negocio import DB_COLUMNS

logger = logging.getLogger(__name__)

class StatsRepository:
    def __init__(self, db_conn):
        self.db_conn = db_conn

    @property
    def pool(self):
        return self.db_conn.pool

    @property
    def modo_offline(self):
        return self.db_conn.modo_offline

    async def obtener_resumen_dia(self, sucursal=None):
        resumen = {"total": 0.0, "efectivo": 0.0, "tarjeta": 0.0, "local": 0, "domicilio": 0, "gastos": 0.0, "neto_efectivo": 0.0}
        if self.modo_offline or not self.pool:
            return resumen

        try:
            async with self.pool.acquire() as conn:
                col_estatus = DB_COLUMNS.get('ESTATUS', 'estado_pedido')
                col_fecha = DB_COLUMNS.get('FECHA', 'fecha')
                
                # FILTRO CORREGIDO: Filtrar prioritariamente por turno activo (corte = 0)
                where_gastos = "WHERE corte = 0"
                where_ventas = f"WHERE corte = 0 AND ({col_estatus} IS NULL OR UPPER({col_estatus}::text) != 'CANCELADO')"
                params = []

                if sucursal:
                    where_gastos += " AND UPPER(TRIM(sucursal)) = UPPER(TRIM($1))"
                    where_ventas += " AND UPPER(TRIM(sucursal)) = UPPER(TRIM($1))"
                    params.append(sucursal)

                # 1. Obtener Gastos activos de la sucursal (corte = 0)
                rg = await conn.fetchrow(f"SELECT SUM(monto) AS tg FROM gastos {where_gastos}", *params)
                if rg and rg["tg"]:
                    resumen["gastos"] = float(rg["tg"])

                # 2. Sumar ventas por método de pago del turno activo
                col_metodo = DB_COLUMNS.get('METODO', 'metodo')
                col_total = DB_COLUMNS.get('TOTAL', 'total')

                filas_dinero = await conn.fetch(
                    f"SELECT {col_metodo} AS metodo, SUM({col_total}) AS suma "
                    f"FROM ventas {where_ventas} GROUP BY {col_metodo}", *params
                )
                for row in filas_dinero:
                    suma = float(row["suma"] or 0)
                    metodo_str = str(row["metodo"] or "").upper().strip()
                    if "EFECTIVO" in metodo_str:
                        resumen["efectivo"] += suma
                    elif "TARJETA" in metodo_str:
                        resumen["tarjeta"] += suma
                    resumen["total"] += suma

                # 3. Contar tickets por servicio (Local vs Domicilio)
                col_servicio = DB_COLUMNS.get('SERVICIO', 'servicio')
                filas_servicio = await conn.fetch(
                    f"SELECT {col_servicio} AS servicio, COUNT(*) AS cantidad "
                    f"FROM ventas {where_ventas} GROUP BY {col_servicio}", *params
                )
                for row in filas_servicio:
                    srv_str = str(row["servicio"] or "").upper().strip()
                    if "LOCAL" in srv_str:
                        resumen["local"] += row["cantidad"]
                    elif "DOMICILIO" in srv_str:
                        resumen["domicilio"] += row["cantidad"]

                resumen["neto_efectivo"] = resumen["efectivo"] - resumen["gastos"]
            return resumen
        except Exception as e:
            logger.error(f"Error al obtener resumen: {e}")
            return resumen

    async def obtener_resumen_global_dia(self):
        return await self.obtener_resumen_dia(sucursal=None)

    async def obtener_ventas_por_dia(self, sucursal=None, dias=7):
        if self.modo_offline or not self.pool:
            return []

        where_clause = "AND UPPER(TRIM(sucursal)) = UPPER(TRIM($1))" if sucursal else ""
        query = f"""
            SELECT
                DATE({DB_COLUMNS["FECHA"]}) as dia,
                SUM({DB_COLUMNS["TOTAL"]}) as total_ventas
            FROM ventas
            WHERE {DB_COLUMNS["FECHA"]} >= (NOW() - INTERVAL '{dias} days')::date
            {where_clause}
            GROUP BY dia
            ORDER BY dia ASC;
        """
        params = [sucursal] if sucursal else []
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetch(query, *params)
        except Exception as e:
            logger.error(f"Error en obtener_ventas_por_dia: {e}")
            return []

    async def obtener_ventas_comparativas_sucursales(self, dias=7):
        if self.modo_offline or not self.pool:
            return {}

        col_estatus = DB_COLUMNS.get('ESTATUS', 'estado_pedido')
        query = f"""
            SELECT
                UPPER(TRIM(sucursal)) as sucursal,
                DATE({DB_COLUMNS["FECHA"]}) as dia,
                SUM({DB_COLUMNS["TOTAL"]}) as total_ventas
            FROM ventas
            WHERE {DB_COLUMNS["FECHA"]} >= (NOW() - INTERVAL '{dias} days')::date
            AND ({col_estatus} IS NULL OR UPPER({col_estatus}::text) != 'CANCELADO')
            GROUP BY UPPER(TRIM(sucursal)), dia
            ORDER BY sucursal, dia ASC;
        """
        resultado_final = {}
        try:
            async with self.pool.acquire() as conn:
                filas = await conn.fetch(query)
                for fila in filas:
                    raw_suc = fila.get("sucursal")
                    suc = (str(raw_suc).strip().upper()) if raw_suc is not None else "DESCONOCIDA"
                    if suc not in resultado_final:
                        resultado_final[suc] = []
                    resultado_final[suc].append({"dia": fila["dia"], "total_ventas": fila["total_ventas"]})
            return resultado_final
        except Exception as e:
            logger.error(f"Error en obtener_ventas_comparativas_sucursales: {e}")
            return {}

    async def obtener_ventas_semanales_comparativas(self, semanas=4):
        if self.modo_offline or not self.pool:
            return {}

        col_estatus = DB_COLUMNS.get('ESTATUS', 'estado_pedido')
        query = f"""
            SELECT
                UPPER(TRIM(sucursal)) as sucursal,
                DATE_TRUNC('week', {DB_COLUMNS["FECHA"]}) as semana,
                SUM({DB_COLUMNS["TOTAL"]}) as total_ventas
            FROM ventas
            WHERE {DB_COLUMNS["FECHA"]} >= (NOW() - INTERVAL '{semanas} weeks')::date
            AND ({col_estatus} IS NULL OR UPPER({col_estatus}::text) != 'CANCELADO')
            GROUP BY UPPER(TRIM(sucursal)), semana
            ORDER BY sucursal, semana ASC;
        """
        resultado_final = {}
        try:
            async with self.pool.acquire() as conn:
                filas = await conn.fetch(query)
                for fila in filas:
                    raw_suc = fila.get("sucursal")
                    suc = (str(raw_suc).strip().upper()) if raw_suc is not None else "DESCONOCIDA"
                    if suc not in resultado_final:
                        resultado_final[suc] = []
                    resultado_final[suc].append({"semana": fila["semana"], "total_ventas": fila["total_ventas"]})
            return resultado_final
        except Exception as e:
            logger.error(f"Error en obtener_ventas_semanales_comparativas: {e}")
            return {}

    async def obtener_ranking_pizzas(self, sucursal=None, limite=5):
        if self.modo_offline or not self.pool:
            return []

        where_clause = "AND sucursal = $1" if sucursal else ""
        query = f"""
            SELECT
                elem->>'nombre' as pizza_nombre,
                COUNT(*) as cantidad
            FROM ventas,
            json_array_elements({DB_COLUMNS["DETALLE"]}::json) as elem
            WHERE {DB_COLUMNS["FECHA"]} >= (NOW() - INTERVAL '1 day')::date AND corte = 0 AND {DB_COLUMNS["DETALLE"]} IS NOT NULL AND {DB_COLUMNS["DETALLE"]} != '[]' {where_clause}
            AND elem->>'nombre' IS NOT NULL
            GROUP BY pizza_nombre
            ORDER BY cantidad DESC
            LIMIT {limite};
        """
        params = [sucursal] if sucursal else []
        ranking = []
        try:
            async with self.pool.acquire() as conn:
                filas = await conn.fetch(query, *params)
                for fila in filas:
                    if fila["pizza_nombre"]:
                        ranking.append({"nombre": fila["pizza_nombre"], "cantidad": fila["cantidad"]})
            return ranking
        except Exception as e:
            logger.error(f"Error al obtener ranking de pizzas: {e}")
            return []

    async def obtener_ranking_sabores(self, sucursal=None, limite=5):
        if self.modo_offline or not self.pool:
            return []

        where_clause = "WHERE UPPER(TRIM(v.sucursal)) = UPPER(TRIM($1))" if sucursal else ""
        params = [sucursal] if sucursal else []
        query = f"""
            SELECT sabor, COUNT(*) as cantidad
            FROM (
                SELECT json_array_elements_text(p.value->'sabores_elegidos') as sabor
                FROM ventas v, json_array_elements(v.{DB_COLUMNS["DETALLE"]}::json) p
                {where_clause}
            ) as sabores_desglosados
            WHERE sabor IS NOT NULL
            GROUP BY sabor ORDER BY cantidad DESC LIMIT {limite};
        """
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetch(query, *params)
        except Exception as e:
            logger.error(f"Error en ranking de sabores: {e}")
            return []