from services.offline_manager import OfflineManager
from database.connection import DatabaseConnection
from database.repositories.pedidos_repository import PedidosRepository
from database.repositories.gastos_repository import GastosRepository
from database.repositories.stats_repository import StatsRepository

class DatabaseManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.offline_manager = OfflineManager()
        self.conn = DatabaseConnection(config_manager)

        # Repositorios
        self.pedidos = PedidosRepository(self.conn, self.offline_manager)
        self.gastos = GastosRepository(self.conn)
        self.stats = StatsRepository(self.conn)

    @property
    def pool(self):
        return self.conn.pool

    @property
    def modo_offline(self):
        return self.conn.modo_offline

    @modo_offline.setter
    def modo_offline(self, valor):
        self.conn.modo_offline = valor

    # --- Conexión ---
    async def inicializar_db(self):
        await self.conn.inicializar()

    async def cerrar_pool(self):
        await self.conn.cerrar()

    # --- Delegación Pedidos ---
    async def guardar_pedido(self, pedido, usuario_nombre="Sistema"):
        return await self.pedidos.guardar_pedido(pedido, usuario_nombre)

    async def obtener_pedidos_cocina(self, sucursal):
        return await self.pedidos.obtener_pedidos_cocina(sucursal)

    async def actualizar_estatus_pedido(self, id_ticket, nuevo_estatus):
        return await self.pedidos.actualizar_estatus_pedido(id_ticket, nuevo_estatus)

    async def actualizar_repartidor_pedido(self, id_ticket, repartidor):
        return await self.pedidos.actualizar_repartidor_pedido(id_ticket, repartidor)

    async def obtener_historial_pedidos(self, sucursal):
        return await self.pedidos.obtener_historial_pedidos(sucursal)

    async def obtener_pedidos_repartidor(self, nombre_repartidor, sucursal):
        return await self.pedidos.obtener_pedidos_repartidor(nombre_repartidor, sucursal)

    # --- Delegación Gastos y Operaciones ---
    async def guardar_gasto(self, gasto):
        return await self.gastos.guardar_gasto(gasto)

    async def cerrar_dia_operativo(self, sucursal):
        return await self.gastos.cerrar_dia_operativo(sucursal)

    # --- Delegación Estadísticas y Métricas ---
    async def obtener_resumen_dia(self, sucursal=None):
        return await self.stats.obtener_resumen_dia(sucursal)

    async def obtener_resumen_global_dia(self):
        return await self.stats.obtener_resumen_global_dia()

    async def obtener_ventas_por_dia(self, sucursal=None, dias=7):
        return await self.stats.obtener_ventas_por_dia(sucursal, dias)

    async def obtener_ventas_comparativas_sucursales(self, dias=7):
        return await self.stats.obtener_ventas_comparativas_sucursales(dias)

    async def obtener_ventas_semanales_comparativas(self, semanas=4):
        return await self.stats.obtener_ventas_semanales_comparativas(semanas)

    async def obtener_ranking_pizzas(self, sucursal=None, limite=5):
        return await self.stats.obtener_ranking_pizzas(sucursal, limite)

    async def obtener_ranking_sabores(self, sucursal=None, limite=5):
        return await self.stats.obtener_ranking_sabores(sucursal, limite)

    # Alias para compatibilidad con la vista de corte
    async def procesar_corte_caja(self, sucursal):
        return await self.cerrar_dia_operativo(sucursal)

    async def realizar_corte_caja(self, sucursal):
        return await self.cerrar_dia_operativo(sucursal)