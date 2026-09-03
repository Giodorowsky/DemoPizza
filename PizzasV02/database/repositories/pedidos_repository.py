import json
import ssl
import asyncpg
import logging
from datetime import datetime
from datos_negocio import DB_COLUMNS, ESTADO_PREPARANDO

logger = logging.getLogger(__name__)

class PedidosRepository:
    def __init__(self, db_conn, offline_manager):
        self.db_conn = db_conn
        self.offline_manager = offline_manager

    @property
    def pool(self):
        return self.db_conn.pool

    @property
    def modo_offline(self):
        return self.db_conn.modo_offline

    async def guardar_pedido(self, pedido, usuario_nombre="Sistema"):
        if self.modo_offline or not self.pool:
            logger.warning("⚠️ Modo Offline: Guardando venta en disco local...")
            self.offline_manager.guardar_pedido_offline(pedido, usuario_nombre)
            return False

        fecha_db = pedido.fecha
        if isinstance(fecha_db, str):
            try:
                fecha_db = datetime.fromisoformat(fecha_db)
            except ValueError:
                fecha_db = datetime.now()

        productos_serializables = []
        for p in pedido.productos:
            if hasattr(p, "to_dict"):
                productos_serializables.append(p.to_dict())
            elif isinstance(p, dict):
                productos_serializables.append(p)
            else:
                productos_serializables.append(str(p))

        detalle_texto = json.dumps(productos_serializables, ensure_ascii=False)
        columnas = DB_COLUMNS

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    prefijo = "01" if pedido.sucursal == "MATRIZ" else "02"

                    await conn.execute(
                        "INSERT INTO contadores_folios (sucursal, ultimo_folio) VALUES ($1, 0) ON CONFLICT (sucursal) DO NOTHING",
                        pedido.sucursal,
                    )

                    fila_folio = await conn.fetchrow(
                        "UPDATE contadores_folios SET ultimo_folio = ultimo_folio + 1 WHERE sucursal = $1 RETURNING ultimo_folio",
                        pedido.sucursal,
                    )
                    nuevo_folio_num = fila_folio["ultimo_folio"]
                    id_ticket_final = f"{prefijo}-{nuevo_folio_num}"

                    query_insert = f"""
                        INSERT INTO ventas (
                            {columnas["ID"]}, {columnas["FECHA"]}, {columnas["CLIENTE"]}, {columnas["TEL"]}, 
                            {columnas["DIR"]}, colonia, {columnas["DETALLE"]}, {columnas["TOTAL"]}, 
                            {columnas["METODO"]}, {columnas["SERVICIO"]}, {columnas["ESTATUS"]}, {columnas["REPARTIDOR"]}, 
                            {columnas["SUCURSAL"]}, cajero, {columnas["REF"]}
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15);
                    """
                    await conn.execute(
                        query_insert,
                        id_ticket_final,
                        fecha_db,
                        pedido.cliente_nombre,
                        pedido.cliente_tel,
                        pedido.cliente_dir,
                        pedido.cliente_colonia,
                        detalle_texto,
                        pedido.total,
                        pedido.metodo_pago,
                        pedido.tipo_servicio,
                        pedido.estatus,
                        pedido.repartidor,
                        pedido.sucursal,
                        usuario_nombre,
                        pedido.cliente_ref,
                    )

                    try:
                        pedido.id = id_ticket_final
                    except Exception:
                        pass

            return True

        except (asyncpg.exceptions.ConnectionDoesNotExistError, OSError, ssl.SSLError, asyncpg.PostgresError) as e:
            logger.warning(f"⚠️ Error de red/DB detectado. Guardando pedido offline. Error: {e}")
            self.offline_manager.guardar_pedido_offline(pedido, usuario_nombre)
            return False
        except Exception as e:
            logger.exception(f"❌ Error inesperado al guardar pedido en la DB: {e}")
            raise

    async def obtener_pedidos_cocina(self, sucursal):
        if self.modo_offline or not self.pool:
            logger.warning("⚠️ Modo Offline: Omitiendo 'obtener_pedidos_cocina'")
            return []

        pedidos_cocina = []
        query = f"""
            SELECT * FROM ventas 
            WHERE {DB_COLUMNS['ESTATUS']} = $1 AND UPPER(TRIM({DB_COLUMNS['SUCURSAL']})) = UPPER(TRIM($2))
            ORDER BY {DB_COLUMNS["FECHA"]} ASC
        """
        try:
            async with self.pool.acquire() as conn:
                filas = await conn.fetch(query, ESTADO_PREPARANDO, sucursal)
                for fila in filas:
                    detalle_raw = fila.get(DB_COLUMNS["DETALLE"]) if hasattr(fila, 'get') else fila[DB_COLUMNS["DETALLE"]]
                    detalle = []
                    if isinstance(detalle_raw, (str, bytes)):
                        try:
                            detalle = json.loads(detalle_raw)
                        except Exception:
                            detalle = []
                    elif isinstance(detalle_raw, (list, dict)):
                        detalle = detalle_raw

                    pedidos_cocina.append({
                        "id": fila[DB_COLUMNS["ID"]],
                        "fecha": fila[DB_COLUMNS["FECHA"]],
                        "servicio": fila[DB_COLUMNS["SERVICIO"]],
                        "detalle": detalle,
                    })
            return pedidos_cocina
        except Exception as e:
            logger.error(f"Error al obtener pedidos de cocina: {e}")
            return []

    async def actualizar_estatus_pedido(self, id_ticket, nuevo_estatus):
        if self.modo_offline or not self.pool:
            logger.warning(f"⚠️ Modo Offline: No se pudo actualizar estatus de ticket {id_ticket} en la nube.")
            return False

        query = f"UPDATE ventas SET {DB_COLUMNS['ESTATUS']} = $1 WHERE {DB_COLUMNS['ID']} = $2"
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query, nuevo_estatus, id_ticket)
            return True
        except Exception as e:
            logger.error(f"Error al actualizar estatus: {e}")
            return False

    async def actualizar_repartidor_pedido(self, id_ticket, repartidor):
        if self.modo_offline or not self.pool:
            logger.warning(f"⚠️ Modo Offline: No se pudo asignar repartidor a ticket {id_ticket} en la nube.")
            return False

        query = f"UPDATE ventas SET {DB_COLUMNS['REPARTIDOR']} = $1 WHERE {DB_COLUMNS['ID']} = $2"
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query, repartidor, id_ticket)
            return True
        except Exception as e:
            logger.error(f"Error al actualizar repartidor: {e}")
            return False

    async def obtener_historial_pedidos(self, sucursal):
        if self.modo_offline or not self.pool:
            logger.warning("⚠️ Modo Offline: Omitiendo 'obtener_historial_pedidos'")
            return []

        historial = []
        query = f"SELECT * FROM ventas WHERE corte = 0 AND UPPER(TRIM({DB_COLUMNS['SUCURSAL']})) = UPPER(TRIM($1)) ORDER BY {DB_COLUMNS['ID']} DESC LIMIT 50"

        try:
            async with self.pool.acquire() as conn:
                filas = await conn.fetch(query, sucursal)
                for fila in filas:
                    detalle_raw = fila.get(DB_COLUMNS["DETALLE"]) if hasattr(fila, 'get') else fila[DB_COLUMNS["DETALLE"]]
                    detalle = []
                    if isinstance(detalle_raw, (str, bytes)):
                        try:
                            detalle = json.loads(detalle_raw)
                        except Exception:
                            detalle = []
                    elif isinstance(detalle_raw, (list, dict)):
                        detalle = detalle_raw

                    historial.append({
                        "id": fila[DB_COLUMNS["ID"]],
                        "fecha": fila[DB_COLUMNS["FECHA"]],
                        "cliente": fila[DB_COLUMNS["CLIENTE"]],
                        "total": fila[DB_COLUMNS["TOTAL"]],
                        "estatus": fila[DB_COLUMNS["ESTATUS"]],
                        "detalle": detalle,
                        "tipo": fila[DB_COLUMNS["SERVICIO"]],
                        "tel": fila[DB_COLUMNS["TEL"]],
                        "dir": fila[DB_COLUMNS["DIR"]],
                        "colonia": fila.get("colonia") if hasattr(fila, 'get') else fila["colonia"],
                        "repartidor": fila[DB_COLUMNS["REPARTIDOR"]],
                        "sucursal": fila[DB_COLUMNS["SUCURSAL"]],
                        "metodo": fila[DB_COLUMNS["METODO"]],
                    })
            return historial
        except Exception as e:
            logger.error(f"Error al obtener historial: {e}")
            return []

    async def obtener_pedidos_repartidor(self, nombre_repartidor, sucursal):
        if self.modo_offline or not self.pool:
            logger.warning("⚠️ Modo Offline: Omitiendo 'obtener_pedidos_repartidor'")
            return []

        query = f"""
            SELECT * FROM ventas
            WHERE {DB_COLUMNS['REPARTIDOR']} = $1
            AND UPPER(TRIM({DB_COLUMNS['SUCURSAL']})) = UPPER(TRIM($2))
            AND corte = 0
            ORDER BY {DB_COLUMNS['ESTATUS']} ASC, {DB_COLUMNS['ID']} DESC
        """
        try:
            async with self.pool.acquire() as conn:
                filas = await conn.fetch(query, nombre_repartidor, sucursal)
                return [dict(fila) for fila in filas]
        except Exception as e:
            logger.error(f"Error al obtener pedidos de repartidor: {e}")
            return []