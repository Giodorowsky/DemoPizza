import asyncio
import json
import os
import traceback
from modelos.pedido import Pedido
from datos_negocio import COLOR_CONTRASTE
from views.componentes.ayuditas import notificar_seguro

class SyncService:
    def __init__(self, db, page):
        self.db = db
        self.page = page
        self.tarea_sincronizacion = None

    async def iniciar(self):
        await self.sincronizar_pedidos_offline()
        self.tarea_sincronizacion = asyncio.create_task(self.bucle_sincronizacion_offline())

    def detener(self):
        if self.tarea_sincronizacion and not self.tarea_sincronizacion.done():
            self.tarea_sincronizacion.cancel()

    async def sincronizar_pedidos_offline(self):
        if self.db.modo_offline or not self.db.pool:
            return

        archivos_pendientes = self.db.offline_manager.obtener_pedidos_offline()
        if not archivos_pendientes:
            return

        for ruta_archivo in archivos_pendientes:
            try:
                with open(ruta_archivo, "r", encoding="utf-8") as f:
                    datos_pedido = json.load(f)

                pedido_obj = Pedido(
                    id=datos_pedido.get("id"),
                    fecha=datos_pedido.get("fecha"),
                    cliente_nombre=datos_pedido.get("cliente_nombre", ""),
                    cliente_tel=datos_pedido.get("cliente_tel", ""),
                    cliente_dir=datos_pedido.get("cliente_dir", ""),
                    cliente_colonia=datos_pedido.get("cliente_colonia", ""),
                    cliente_ref=datos_pedido.get("cliente_ref", ""),
                    tipo_servicio=datos_pedido.get("tipo_servicio", "LOCAL"),
                    productos=datos_pedido.get("productos", []),
                    total=datos_pedido.get("total", 0.0),
                    metodo_pago=datos_pedido.get("metodo_pago", "EFECTIVO"),
                    estatus=datos_pedido.get("estatus", "PREPARANDO"),
                    repartidor=datos_pedido.get("repartidor"),
                    sucursal=datos_pedido.get("sucursal", "MATRIZ"),
                    corte=datos_pedido.get("corte", 0),
                )

                usuario = datos_pedido.get("usuario_responsable", "Sistema Offline")
                guardado_exitoso = await self.db.guardar_pedido(pedido_obj, usuario_nombre=usuario)

                if guardado_exitoso:
                    os.remove(ruta_archivo)
                    notificar_seguro(self.page, "✅ Pedidos offline sincronizados con la nube.", COLOR_CONTRASTE)
            except Exception as e:
                print(f"Error al sincronizar el archivo {ruta_archivo}: {e}")
                traceback.print_exc()

    async def bucle_sincronizacion_offline(self):
        while True:
            try:
                await asyncio.sleep(60)
                await self.sincronizar_pedidos_offline()
            except asyncio.CancelledError:
                break