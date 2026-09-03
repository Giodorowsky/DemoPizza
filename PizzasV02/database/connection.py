import socket
import ssl
import asyncpg
import logging
from datos_negocio import DB_COLUMNS

logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.connection_string = None
        self.pool = None
        self.modo_offline = False

    async def inicializar(self):
        if not self.pool:
            self.connection_string = self.config_manager.obtener("database_url")
            if not self.connection_string:
                logger.warning("⚠️ ADVERTENCIA: 'database_url' no encontrada. Iniciando en modo offline.")
                self.modo_offline = True
                return

            ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            try:
                self.pool = await asyncpg.create_pool(
                    self.connection_string,
                    min_size=2,
                    max_size=10,
                    ssl=ctx,
                    command_timeout=15,
                    timeout=15.0,
                    statement_cache_size=0
                )
                self.modo_offline = False
                logger.info("✅ Pool de conexiones a Supabase iniciado correctamente.")

            except (socket.gaierror, OSError, asyncpg.PostgresError, asyncpg.InterfaceError) as e:
                self.pool = None
                self.modo_offline = True
                logger.warning(f"⚠️ Sin conexión a la base de datos remota. Activando Modo Offline. Error: {e}")
                return

        if self.pool and not self.modo_offline:
            try:
                async with self.pool.acquire() as conn:
                    query_ventas = f"""
                        CREATE TABLE IF NOT EXISTS ventas (
                            {DB_COLUMNS["ID"]} TEXT PRIMARY KEY,
                            {DB_COLUMNS["FECHA"]} TIMESTAMPTZ,
                            {DB_COLUMNS["CLIENTE"]} TEXT,
                            {DB_COLUMNS["TEL"]} TEXT,
                            {DB_COLUMNS["DIR"]} TEXT,
                            colonia TEXT,
                            {DB_COLUMNS["DETALLE"]} TEXT,
                            {DB_COLUMNS["TOTAL"]} REAL,
                            {DB_COLUMNS["METODO"]} TEXT,
                            {DB_COLUMNS["SERVICIO"]} TEXT,
                            {DB_COLUMNS["ESTATUS"]} TEXT,
                            {DB_COLUMNS["REPARTIDOR"]} TEXT,
                            {DB_COLUMNS["SUCURSAL"]} TEXT,
                            cajero TEXT,
                            {DB_COLUMNS["REF"]} TEXT,
                            corte INTEGER DEFAULT 0 
                        );
                    """
                    await conn.execute(query_ventas)

                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS gastos (
                            id SERIAL PRIMARY KEY,
                            descripcion TEXT,
                            monto REAL,
                            cajero TEXT,
                            fecha TIMESTAMPTZ,
                            sucursal TEXT,
                            corte INTEGER DEFAULT 0
                        );
                    """)

                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS contadores_folios (
                            sucursal TEXT PRIMARY KEY,
                            ultimo_folio INTEGER NOT NULL DEFAULT 0
                        );
                    """)
                    logger.info("Base de datos de Supabase sincronizada correctamente.")
            except Exception as e:
                logger.exception(f"⚠️ Error al verificar esquema DDL. Cambiando a Modo Offline: {e}")
                self.modo_offline = True

    async def cerrar(self):
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Pool de conexiones cerrado.")