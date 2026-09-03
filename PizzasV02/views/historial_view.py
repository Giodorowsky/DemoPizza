import flet as ft
import asyncio
from datos_negocio import (
    COLOR_FONDO, COLOR_PRIMARIO, COLOR_TEXTO, COLOR_ERROR,
    COLOR_EXITO, COLOR_NUEVO, ESTADO_ENTREGADO, ESTADO_LIQUIDADO, ESTADO_EN_CAMINO,
    SERVICIO_DOMICILIO
)
from views.componentes.botones import BotonAnimado
from views.componentes.tarjetas import TarjetaPedidoHistorial
from views.componentes.ayuditas import notificar_seguro
from modelos.pedido import Pedido


class HistorialView(ft.Container):
    def __init__(self, db,gestor_nav=None):
        super().__init__()
        self.db = db
        self.gestor_nav = gestor_nav
        self.expand = True
        self.bgcolor = COLOR_FONDO
        self.padding = 20

        # --- BLINDAJE CONTRA EL ERROR 'super' object has no attribute '__getattr__' ---
        # Flet exige que todas las variables de instancia existan desde el inicio
        self.vista_activa = False
        self.config = None
        self.tarea_refresco = None

        # Lista de desplazamiento para los pedidos
        self.lista_pedidos = ft.ListView(expand=True, spacing=15)

        self.content = ft.Column(
            controls=[
                ft.Text("CONTROL DE PEDIDOS", size=26, weight="bold", color=COLOR_PRIMARIO),
                ft.Divider(height=20, color=ft.Colors.GREY_800),
                self.lista_pedidos, 
                ft.Container(height=10),
                BotonAnimado("ACTUALIZAR LISTA", on_click=self.cargar_pedidos_manualmente, width=250)
            ]
        )

    def will_unmount(self):
        """Se ejecuta automáticamente al salir de la pantalla para detener procesos."""
        self.vista_activa = False
        if self.tarea_refresco and not self.tarea_refresco.done():
            self.tarea_refresco.cancel()

    def did_mount(self):
        """Se inicia al entrar a la vista; activa el bucle de tiempo real."""
        self.vista_activa = True
        
        # Recuperamos la configuración de marca blanca de forma segura
        try:
            self.config = self.page.session.store.get("config")
        except Exception:
            self.config = None
        self.tarea_refresco = asyncio.create_task(self.bucle_refresco())
            
        

    async def bucle_refresco(self):
        """Mantiene la lista actualizada cada 10 segundos con protección anti-crash."""
        while self.vista_activa:
            try:
                await self.cargar_pedidos()
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break    
            except Exception:
                # Si la vista se destruye durante la espera, salimos del bucle en paz
                break

    async def cargar_pedidos_manualmente(self, e):
        """Disparador para el botón de actualización manual."""
        await self.cargar_pedidos()

    async def cargar_pedidos(self, e=None):
        self.lista_pedidos.controls.clear()
        
        # Recuperación estricta de sesión
        sucursal = self.page.session.store.get("sucursal_actual") if self.page else None
        
        # Validación Fail-Fast
        if not sucursal:
            self.lista_pedidos.controls.append(
                ft.Text("Error crítico: Pérdida de sesión de la sucursal.", color=ft.Colors.RED_500, weight="bold")
            )
            try:
                self.update()
            except Exception:
                pass
            return

        # Consulta de pedidos
        filas_pedidos = await self.db.obtener_historial_pedidos(sucursal)
        pedidos = [Pedido.desde_base_datos(p) for p in filas_pedidos]

        colores = self.config.obtener("tema") if self.config else {}

        if not pedidos:
            self.lista_pedidos.controls.append(
                ft.Text("No hay pedidos registrados en este turno.", color=ft.Colors.GREY_500, italic=True)
            )
        else:
            for pedido in pedidos:
                tarjeta = TarjetaPedidoHistorial(pedido, self.abrir_modal_detalle, colores)
                self.lista_pedidos.controls.append(tarjeta)

        try:
            self.update()
        except Exception:
            pass

    def abrir_modal_detalle(self, pedido, e):
        """Abre el diálogo de gestión delegando los flujos de estado al modelo Pedido."""
        page = e.page if e else self.page
        if not page: return

        # 1. Obtenemos la lista de productos formateada directamente desde el modelo
        lista_productos_ui = [ft.Text(linea, color=COLOR_TEXTO, size=16) for linea in pedido.obtener_lineas_detalle_producto()]

        # 2. Construcción de la información del cliente
        contenido_modal = [
            ft.Text("PRODUCTOS:", weight="bold", color=COLOR_PRIMARIO),
            *lista_productos_ui,
            ft.Divider(color=ft.Colors.GREY_800),
            
            ft.Text("INFORMACIÓN DEL CLIENTE:", weight="bold", color=COLOR_PRIMARIO),
            ft.Text(f"Nombre: {pedido.cliente_nombre}", color=COLOR_TEXTO),
            ft.Text(f"Teléfono: {pedido.cliente_tel}", color=COLOR_TEXTO),
            ft.Text(f"Colonia: {pedido.cliente_colonia}", color=COLOR_TEXTO),
            ft.Text(f"Dirección: {pedido.cliente_dir}", color=COLOR_TEXTO),
            ft.Text(f"Repartidor: {pedido.repartidor or 'No asignado'}", color=COLOR_NUEVO, weight="bold"),
            
            ft.Divider(color=ft.Colors.GREY_800),
            ft.Text(f"TOTAL: ${pedido.total:.2f}", size=24, weight="bold", color=COLOR_EXITO),
        ]

        if pedido.esta_pendiente_de_liquidacion():
            distintivo_pendiente = ft.Container(
                bgcolor=ft.Colors.with_opacity(0.1, COLOR_ERROR),
                padding=ft.Padding.symmetric(vertical=4, horizontal=8),
                border_radius=8,
                content=ft.Row([ft.Icon(ft.Icons.MONETIZATION_ON_OUTLINED, color=COLOR_ERROR, size=16),
                                ft.Text("PAGO PENDIENTE DE LIQUIDAR", color=COLOR_ERROR, size=12, weight="bold")])
            )
            contenido_modal.append(distintivo_pendiente)
            
        # --- NUEVO CÓDIGO A INSERTAR AQUÍ ---
        elif pedido.esta_liquidado():
            distintivo_liquidado = ft.Container(
                bgcolor=ft.Colors.with_opacity(0.1, COLOR_EXITO),
                padding=ft.Padding.symmetric(vertical=4, horizontal=8),
                border_radius=8,
                content=ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=COLOR_EXITO, size=16),
                                ft.Text("PEDIDO LIQUIDADO EN CAJA", color=COLOR_EXITO, size=12, weight="bold")])
            )
            contenido_modal.append(distintivo_liquidado)
            
        # 4. Creación del Diálogo
        dialogo = ft.AlertDialog(
            bgcolor=COLOR_FONDO,
            title=ft.Text(f"TICKET #{pedido.id}", color=COLOR_PRIMARIO, weight="bold"),
            content=ft.Column(contenido_modal, tight=True, spacing=5, scroll=ft.ScrollMode.ADAPTIVE),
        )

        def cerrar_modal(e):
            dialogo.open = False
            page.update()

        # 5. Lógica de botones de acción delegada limpiamente al modelo
        acciones = []
        # Menú de repartidores (Solo para pedidos a domicilio)
        if pedido.tipo_servicio == SERVICIO_DOMICILIO:
            menu_items = []
            for i in range(1, 4): # Genera "Repartidor 1", "Repartidor 2", "Repartidor 3"
                nombre_repartidor = f"Repartidor {i}"
                menu_items.append(
                    ft.PopupMenuItem(
                        content=ft.Text(nombre_repartidor),
                        on_click=lambda _, r=nombre_repartidor: asyncio.create_task(self.asignar_repartidor_db(pedido.id, r, dialogo, page))
                    )
                )
            
            boton_asignar = ft.PopupMenuButton(
                content=ft.Row([ft.Icon(ft.Icons.MOTORCYCLE), ft.Text("ASIGNAR REPARTIDOR")]),
                items=menu_items
            )
            acciones.append(boton_asignar)

        # Consultamos directamente al objeto pedido las capacidades de transición
        siguiente_estatus = pedido.obtener_siguiente_estatus()
        texto_boton = pedido.obtener_texto_boton_accion()
        
        if texto_boton and siguiente_estatus:
            es_liquidacion = (siguiente_estatus == ESTADO_LIQUIDADO)
            color_icono = COLOR_EXITO if es_liquidacion else COLOR_NUEVO
            icono_boton = ft.Icons.CHECK_CIRCLE if es_liquidacion else ft.Icons.MOTORCYCLE

            acciones.insert(0, ft.TextButton(
                texto_boton, 
                icon=icono_boton, 
                icon_color=color_icono,
                on_click=lambda _: asyncio.create_task(self.actualizar_estatus(pedido.id, siguiente_estatus, dialogo, page))
            ))

        acciones.append(ft.TextButton("Cerrar", icon_color=ft.Colors.RED, on_click=cerrar_modal))
        dialogo.actions = acciones
        
        page.overlay.append(dialogo)
        dialogo.open = True
        page.update()


    async def actualizar_estatus(self, pedido_id, nuevo_estatus, dialogo, page):
        """Actualiza la base de datos y refresca la interfaz."""
        await self.db.actualizar_estatus_pedido(pedido_id, nuevo_estatus)
        dialogo.open = False
        page.update()
        await self.cargar_pedidos()
        
        notificar_seguro(page, f"✅ Ticket #{pedido_id} actualizado", COLOR_EXITO)
            
    async def asignar_repartidor_db(self, pedido_id, nombre_repartidor, dialogo, page):
        """Vincula un repartidor y pone el pedido 'EN CAMINO' automáticamente."""
        if not nombre_repartidor: return
        
        # 1. Asignar repartidor
        await self.db.actualizar_repartidor_pedido(pedido_id, nombre_repartidor)
        # 2. Actualizar estatus a "EN CAMINO" para que aparezca en la vista del repartidor
        await self.db.actualizar_estatus_pedido(pedido_id, ESTADO_EN_CAMINO) # <-- CORRECCIÓN: Esta línea estaba ausente.
        
        dialogo.open = False
        page.update()
        await self.cargar_pedidos()
        notificar_seguro(page, f"🛵 Repartidor asignado: {nombre_repartidor}", COLOR_NUEVO)