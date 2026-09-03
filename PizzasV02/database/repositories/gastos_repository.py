import logging
from datetime import datetime  # <-- Importación correcta de la CLASE datetime
from datos_negocio import DB_COLUMNS

logger = logging.getLogger(__name__)

class GastosRepository:
    def __init__(self, db_conn):
        self.db_conn = db_conn

    @property
    def pool(self):
        return self.db_conn.pool

    @property
    def modo_offline(self):
        return self.db_conn.modo_offline

    async def guardar_gasto(self, gasto):
        if self.modo_offline or not self.pool:
            logger.warning("⚠️ Modo Offline: Gasto omitido en la nube.")
            return False

        # Formateo seguro de la fecha: si es una instancia de la clase datetime, la convierte a ISO string
        if isinstance(gasto.fecha, datetime):
            fecha_str = gasto.fecha.isoformat()
        else:
            fecha_str = str(gasto.fecha)

        query = "INSERT INTO gastos (descripcion, monto, sucursal, cajero, fecha) VALUES ($1, $2, $3, $4, $5);"
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    query,
                    gasto.descripcion,
                    gasto.monto,
                    gasto.sucursal,
                    gasto.cajero,
                    fecha_str,  # Enviamos la fecha formateada como texto ISO compatible con asyncpg
                )
            return True
        except Exception as e:
            logger.error(f"Error al guardar gasto: {e}")
            return False

    async def cerrar_dia_operativo(self, sucursal):
        if self.modo_offline or not self.pool:
            logger.warning("⚠️ Modo Offline: No se puede realizar el cierre de día en la nube.")
            return False

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # 1. Cerrar ventas activas de la sucursal
                    await conn.execute(
                        f"UPDATE ventas SET corte = 1 WHERE corte = 0 AND UPPER(TRIM({DB_COLUMNS['SUCURSAL']})) = UPPER(TRIM($1))",
                        sucursal,
                    )
                    # 2. Cerrar gastos de la sucursal o huérfanos sin sucursal asignada
                    await conn.execute(
                        "UPDATE gastos SET corte = 1 WHERE corte = 0 AND (UPPER(TRIM(sucursal)) = UPPER(TRIM($1)) OR sucursal IS NULL OR TRIM(sucursal) = '')",
                        sucursal,
                    )
            return True
        except Exception as e:
            logger.error(f"Error al cerrar día operativo: {e}")
            return False