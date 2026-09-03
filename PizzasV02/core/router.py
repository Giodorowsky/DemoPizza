import flet as ft
import traceback
from datos_negocio import COLOR_FONDO
from views.login_view import LoginView
from views.multi_view import MultiViewContainer
from views.repa_view import RepaView
from views.cocina_view import CocinaView
from views.admin_view import AdminView
from views.componentes.ayuditas import GestorConfiguracion, notificar_seguro
from views.componentes.app_bar_builder import crear_app_bar_personalizada
from core.session_manager import SessionManager
from services.sync_service import SyncService

class GestorNavegacion:
    def __init__(self, page: ft.Page, db, vistas_registro=None):
        self.page = page
        self.db = db
        self.vistas_registro = vistas_registro or {}

        self.session = SessionManager(page)
        self.sync_service = SyncService(db, page)

        self.page.on_error = self.manejar_error_global
        self.page.on_route_change = self.manejador_rutas
        self.page.on_view_pop = self.manejador_pop
        
        # Suscripción al canal de notificaciones global
        self.page.pubsub.subscribe_topic("notificaciones", self.mostrar_notificacion_global)

    def mostrar_notificacion_global(self, topic, mensaje_data=None):
        # Si se llama con un solo parámetro de datos (compatibilidad)
        if mensaje_data is None and isinstance(topic, dict):
            mensaje_data = topic

        if not isinstance(mensaje_data, dict):
            return

        # Maneja la notificación sin importar qué vista la disparó
        snack = ft.SnackBar(
            content=ft.Text(mensaje_data.get("mensaje", ""), color=ft.Colors.WHITE),
            bgcolor=mensaje_data.get("color", ft.Colors.GREEN)
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    @property
    def usuario_actual(self):
        return self.session.usuario_actual

    @property
    def sucursal_actual(self):
        return self.session.sucursal_actual

    async def iniciar_app(self):
        # 1. Inyección de dependencias global
        self.page.session.store.set("db_manager", self.db)
        self.page.session.store.set("gestor_nav", self)
        
        # 2. Configuración del tema global
        self.page.theme = ft.Theme(
            color_scheme_seed="#B026FF",
            visual_density=ft.VisualDensity.ADAPTIVE_PLATFORM_DENSITY
        )
        self.page.update()

        config_manager = GestorConfiguracion()
        await config_manager.cargar_configuracion()
        self.page.session.store.set("config", config_manager)

        await self.sync_service.iniciar()
        await self.manejador_rutas(None)

    async def procesar_login_exitoso(self, sesion, sucursal=None):
        self.session.iniciar_sesion(sesion, sucursal=sucursal)
        rol_a_ruta = {
            "CAJERA": "/pos",
            "COCINA": "/cocina",
            "REPARTIDOR": "/repartidor"
        }

        if self.session.usuario_actual["rol"] == "DUEÑO":
            self.page.go("/seleccionar_sucursal")
        else:
            self.page.go(rol_a_ruta.get(self.session.usuario_actual["rol"], "/login"))

    async def procesar_seleccion_sucursal(self, sucursal):
        self.session.establecer_sucursal(sucursal)
        self.page.go("/dashboard_dueno")

    async def cambiar_sucursal_y_recargar(self, nueva_sucursal):
        """Actualiza la sucursal en SessionManager y en el Store de Flet directamente, luego recarga."""
        self.session.establecer_sucursal(nueva_sucursal)
        self.page.session.store.set("sucursal_actual", str(nueva_sucursal)) # Guardado redundante de seguridad
        await self.manejador_rutas(None)

    async def cerrar_sesion_y_redirigir(self):
        self.sync_service.detener()
        self.session.cerrar_sesion()
        self.page.go("/login")

    def _actualizar_historial(self, nueva_ruta):
        historial = self.page.session.store.get("historial_navegacion") or []
        if not historial or historial[-1] != nueva_ruta:
            if nueva_ruta == "/login":
                historial = ["/login"]
            else:
                historial.append(nueva_ruta)
        self.page.session.store.set("historial_navegacion", historial)

    async def manejador_pop(self, e):
        historial = self.page.session.store.get("historial_navegacion") or []
        if len(historial) > 1:
            historial.pop()
            ruta_anterior = historial[-1]
            self.page.session.store.set("historial_navegacion", historial)
            self.page.go(ruta_anterior)
        else:
            await self.cerrar_sesion_y_redirigir()

    async def manejador_rutas(self, e):
        try:
            ruta_actual = self.page.route

            if not self.session.usuario_actual and ruta_actual != "/login":
                self.page.route = "/login"
                ruta_actual = "/login"

            self.page.views.clear()

            if ruta_actual in ["/login", "/"]:
                config = self.page.session.store.get("config")
                self.page.views.append(
                    ft.View(
                        route="/login",
                        controls=[LoginView(al_ingresar=self.procesar_login_exitoso, config=config)],
                        padding=0,
                        bgcolor=COLOR_FONDO
                    )
                )

            elif ruta_actual == "/seleccionar_sucursal":
                self.page.views.append(
                    ft.View(
                        route="/seleccionar_sucursal",
                        bgcolor=COLOR_FONDO,
                        padding=0,
                        controls=[AdminView(self.db, self)]
                    )
                )

            elif ruta_actual in ["/pos", "/dashboard_dueno"]:
                titulo = "PIZZERÍA" if ruta_actual == "/pos" else "DASHBOARD SUCURSAL"
                self.page.views.append(
                    ft.View(
                        route=ruta_actual,
                        appbar=crear_app_bar_personalizada(self.page, self.session, titulo, self.cambiar_sucursal_y_recargar),
                        controls=[MultiViewContainer(self.session.usuario_actual, self.db, self)],
                        bgcolor=COLOR_FONDO,
                        padding=0
                    )
                )

            elif ruta_actual == "/cocina":
                self.page.views.append(
                    ft.View(
                        route="/cocina",
                        appbar=crear_app_bar_personalizada(self.page, self.session, "COCINA", self.cambiar_sucursal_y_recargar),
                        controls=[CocinaView(self.db, sucursal=self.session.sucursal_actual)],
                        bgcolor=COLOR_FONDO,
                        padding=0
                    )
                )

            elif ruta_actual == "/repartidor":
                self.page.views.append(
                    ft.View(
                        route="/repartidor",
                        appbar=crear_app_bar_personalizada(self.page, self.session, "REPARTIDOR", self.cambiar_sucursal_y_recargar),
                        controls=[RepaView(self.db, self.session.usuario_actual)],
                        bgcolor=COLOR_FONDO,
                        padding=0
                    )
                )
            
            self._actualizar_historial(ruta_actual)
            self.page.update() 
            
        except Exception as ex:
            traza = traceback.format_exc()
            self.page.views.append(
                ft.View(
                    bgcolor=ft.Colors.BLACK,
                    padding=20,
                    controls=[
                        ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED, size=60),
                        ft.Text("ERROR DE VISTA (ARQUITECTURA)", color=ft.Colors.RED, size=24, weight="bold"),
                        ft.Text(str(ex), color=ft.Colors.WHITE, size=18),
                        ft.Container(height=20),
                        ft.Text("Rastro para el desarrollador:", color=ft.Colors.GREY),
                        ft.Text(traza, color=ft.Colors.YELLOW_ACCENT, size=12, selectable=True)
                    ]
                )
            )
            self.page.update()

    def _notificar(self, mensaje: str, color: str):
        # Ahora usamos Pub/Sub incluso desde aquí para unificar todo el sistema
        if hasattr(self.page, 'pubsub'):
            color_res = ft.Colors.GREEN if color == "green" else (ft.Colors.RED if color == "red" else color)
            self.page.pubsub.send_all_on_topic("notificaciones", {"mensaje": mensaje, "color": color_res})
        else:
            notificar_seguro(self.page, mensaje, color)

    async def manejar_error_global(self, e):
        print("--- ERROR GLOBAL CAPTURADO ---")
        print(f"Error: {e.data}")
        self._notificar("Ocurrió un error inesperado.", "red")