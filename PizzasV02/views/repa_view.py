import flet as ft
import asyncio
import flet_audio as fta # 1. Importamos el motor de audio igual que en cocina

from datos_negocio import (
    COLOR_FONDO, COLOR_PRIMARIO, COLOR_TEXTO, COLOR_ERROR,
    COLOR_EXITO, ESTADO_ENTREGADO, ESTADO_LIQUIDADO
)
from views.componentes.botones import BotonAnimado
from views.componentes.ayuditas import notificar_seguro
from modelos.pedido import Pedido


class TarjetaPedidoRepa(ft.Container):
    """Tarjeta específica para la vista del repartidor."""
    def __init__(self, pedido, al_entregar):
        super().__init__()
        self.al_entregar = al_entregar
        self.bgcolor = "#1E1E1E"
        self.padding = 20
        self.border_radius = 15
        self.content = ft.Column() # Contenedor vacío inicial
        self.actualizar(pedido) # Primera construcción

    def actualizar(self, nuevo_pedido):
        """Redibuja la tarjeta con los datos más recientes del pedido."""
        self.pedido = nuevo_pedido
        self.content.controls.clear()

        # Lógica para deshabilitar el botón si el pedido ya fue entregado
        es_entregado = self.pedido.estatus in (ESTADO_ENTREGADO, ESTADO_LIQUIDADO)
        texto_boton = "ENTREGADO" if es_entregado else "MARCAR ENTREGADO"
        color_boton = "#333333" if es_entregado else COLOR_EXITO
        icono_boton_nombre = ft.Icons.CHECK if es_entregado else None

        controles_tarjeta = [
            ft.Row([
                ft.Icon(ft.Icons.NUMBERS, color=COLOR_PRIMARIO),
                ft.Text(f"TICKET #{self.pedido.id}", weight="bold", size=20, color=ft.Colors.WHITE),
            ], spacing=10),
            ft.Divider(height=10, color=ft.Colors.GREY_800),
            ft.Row([
                ft.Icon(ft.Icons.PERSON_PIN, color=ft.Colors.CYAN_200),
                ft.Text(f"Cliente: {self.pedido.cliente_nombre}", color=COLOR_TEXTO, size=16),
            ]),
            ft.Row([
                ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.CYAN_200),
                ft.Text(f"Colonia: {self.pedido.cliente_colonia}", color=COLOR_TEXTO, size=16),
            ]),
            ft.Row([
                ft.Icon(ft.Icons.HOME, color=ft.Colors.CYAN_200),
                ft.Text(f"Dirección: {self.pedido.cliente_dir}", color=COLOR_TEXTO, size=16),
            ]),
            ft.Row([
                ft.Icon(ft.Icons.MAP, color=ft.Colors.AMBER_400),
                ft.Text(f"Ref: {self.pedido.cliente_ref}", color=ft.Colors.GREY_400, size=14, italic=True),
            ], wrap=True),
            ft.Row([
                ft.Icon(ft.Icons.PHONE, color=ft.Colors.CYAN_200),
                ft.Text(f"Teléfono: {self.pedido.cliente_tel}", color=COLOR_TEXTO, size=16),
            ]),
            ft.Divider(height=10, color=ft.Colors.GREY_800),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(f"TOTAL: ${self.pedido.total:.2f}", size=22, weight="bold", color=COLOR_EXITO),
                    BotonAnimado(
                        texto=texto_boton,
                        icono=icono_boton_nombre, # Usamos el nombre del icono directamente
                        bgcolor=color_boton,
                        on_click=None if es_entregado else lambda _: asyncio.create_task(self.al_entregar(self.pedido.id)),
                    )
                ]
            )
        ]
        self.content.controls.extend(controles_tarjeta)

        # --- NUEVO: Alerta visual para el repartidor sobre pagos pendientes ---
        # Si el pedido fue en efectivo y ya se entregó, se muestra el recordatorio.
        if self.pedido.esta_liquidado():
            distintivo_liquidado = ft.Container(
                bgcolor=ft.Colors.with_opacity(0.1, COLOR_EXITO),
                padding=ft.Padding.symmetric(vertical=4, horizontal=8),
                margin=ft.Margin.only(top=10),
                border_radius=8,
                content=ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=COLOR_EXITO, size=16),
                                ft.Text("PEDIDO LIQUIDADO", color=COLOR_EXITO, size=12, weight="bold")])
            )
            # Insertamos el distintivo ANTES de la fila del total
            self.content.controls.insert(-1, distintivo_liquidado)
        elif self.pedido.esta_pendiente_de_liquidacion():
            distintivo_pendiente = ft.Container(
                bgcolor=ft.Colors.with_opacity(0.1, COLOR_ERROR),
                padding=ft.Padding.symmetric(vertical=4, horizontal=8),
                margin=ft.Margin.only(top=10),
                border_radius=8,
                content=ft.Row([ft.Icon(ft.Icons.MONETIZATION_ON_OUTLINED, color=COLOR_ERROR, size=16),
                                ft.Text("PAGO PENDIENTE DE LIQUIDAR EN CAJA", color=COLOR_ERROR, size=12, weight="bold")])
            )
            # Insertamos el distintivo ANTES de la fila del total
            self.content.controls.insert(-1, distintivo_pendiente)



class RepaView(ft.Container):
    def __init__(self, db, usuario):
        super().__init__()
        self.db = db
        self.usuario = usuario
        self.expand = True
        self.bgcolor = COLOR_FONDO
        self.padding = 20

        self.vista_activa = True
        self.ultimo_id_visto = 0 # 2. Control de estado para detonar alertas
        
        # 3. Configuración del audio replicada de CocinaView
        self.audio_notificacion = fta.Audio(
            src="campana.mp3",
            autoplay=False,
            volume=1,
            balance=0,
            release_mode=fta.ReleaseMode.STOP,
        )

        # 4. Cambiamos ListView por Column con ScrollMode para mayor fluidez, igual que en cocina
        self.lista_pedidos = ft.Column(expand=True, spacing=15, scroll=ft.ScrollMode.AUTO)

        nombre_repartidor = self.usuario.get("nombre", "Repartidor") if isinstance(self.usuario, dict) else getattr(self.usuario, 'nombre', 'Repartidor')

        self.content = ft.Column(
            expand=True,
            controls=[
                ft.Text(f"MIS ENTREGAS - {nombre_repartidor}", size=26, weight="bold", color=COLOR_PRIMARIO),
                ft.Text("Pedidos a domicilio asignados a tu nombre", color=ft.Colors.GREY_400),
                ft.Divider(height=20, color=ft.Colors.GREY_800),
                self.lista_pedidos,
            ]
        )

    def did_mount(self):
        self.vista_activa = True
        if self.page and self.audio_notificacion not in self.page.services:
            self.page.services.append(self.audio_notificacion)
            self.page.update()
        asyncio.create_task(self.bucle_actualizacion())

    def will_unmount(self):
        self.vista_activa = False

    async def tocar_campana(self):
        try:
            await self.audio_notificacion.play()
        except Exception as e:
            print(f"Error audio repa: {e}")

    async def bucle_actualizacion(self):
        # 5. Bucle optimizado a 5 segundos y separado del renderizado visual
        while self.vista_activa:
            try:
                nombre_repartidor = self.usuario.get("nombre") if isinstance(self.usuario, dict) else getattr(self.usuario, 'nombre', None)
                sucursal_actual = "MATRIZ" # Valor por defecto
                if self.page and self.page.session and self.page.session.store:
                    sucursal_actual = self.page.session.store.get("sucursal_actual") or "MATRIZ"
                
                # Ahora la consulta requiere la sucursal, aislando los datos.
                filas_pedidos = await self.db.obtener_pedidos_repartidor(nombre_repartidor, sucursal_actual)
                pedidos = [Pedido.desde_base_datos(fila) for fila in filas_pedidos]
                
                if pedidos:
                    max_id_actual = max([p.id for p in pedidos])
                    
                    if self.ultimo_id_visto == 0:
                        self.ultimo_id_visto = max_id_actual
                    elif max_id_actual > self.ultimo_id_visto:
                        await self.tocar_campana()
                        notificar_seguro(self.page, f"🛵 ¡NUEVO PEDIDO ASIGNADO! Ticket #{max_id_actual}", COLOR_PRIMARIO)
                        self.ultimo_id_visto = max_id_actual

                await self.dibujar_pedidos(pedidos)
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Error bucle repa: {e}")
                await asyncio.sleep(5)

    async def dibujar_pedidos(self, pedidos):
        """Renderiza las tarjetas independientemente del ciclo de consulta."""
        # Mapeo de tarjetas existentes por ID para una actualización eficiente
        tarjetas_existentes = {t.pedido.id: t for t in self.lista_pedidos.controls if isinstance(t, TarjetaPedidoRepa)}
        ids_pedidos_actuales = {p.id for p in pedidos}

        # Eliminar tarjetas de pedidos que ya no están en la lista
        self.lista_pedidos.controls = [t for t in self.lista_pedidos.controls if not isinstance(t, TarjetaPedidoRepa) or t.pedido.id in ids_pedidos_actuales]

        if not pedidos:
            self.lista_pedidos.controls.clear()
            self.lista_pedidos.controls.append(
                ft.Column([
                    ft.Icon(ft.Icons.MOTORCYCLE, size=80, color=ft.Colors.GREY_600),
                    ft.Text("No tienes entregas pendientes.", color=ft.Colors.GREY_500, size=18, italic=True)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True)
            )
        else:
            for pedido in pedidos:
                if pedido.id in tarjetas_existentes:
                    # Si la tarjeta ya existe, solo actualizamos sus datos
                    tarjetas_existentes[pedido.id].actualizar(pedido)
                else:
                    # Si es un pedido nuevo, creamos una nueva tarjeta
                    tarjeta = TarjetaPedidoRepa(pedido, self.marcar_como_entregado)
                    self.lista_pedidos.controls.append(tarjeta)

        try:
            self.update()
        except Exception:
            pass

    async def marcar_como_entregado(self, pedido_id):
        """Actualiza la DB y fuerza la recarga visual inmediata."""
        try:
            await self.db.actualizar_estatus_pedido(pedido_id, ESTADO_ENTREGADO)
            notificar_seguro(self.page, f"✅ Pedido #{pedido_id} marcado como entregado.", COLOR_EXITO)
            
            # Recarga dinámica instantánea
            nombre_repartidor = self.usuario.get("nombre") if isinstance(self.usuario, dict) else getattr(self.usuario, 'nombre', None)
            sucursal_actual = self.page.session.store.get("sucursal_actual") or "MATRIZ"
            filas_pedidos = await self.db.obtener_pedidos_repartidor(nombre_repartidor, sucursal_actual)
            pedidos = [Pedido.desde_base_datos(fila) for fila in filas_pedidos]
            await self.dibujar_pedidos(pedidos)
        except Exception as e:
            notificar_seguro(self.page, f"❌ Error al actualizar: {e}", "red")