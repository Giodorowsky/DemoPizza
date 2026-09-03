import flet as ft
import asyncio
import inspect
from datos_negocio import COLOR_PRIMARIO, COLOR_TEXTO


class BotonAnimado(ft.Container):
    def __init__(self, texto, on_click, bgcolor=COLOR_PRIMARIO, color_texto=COLOR_TEXTO, width=None, height=50, icono=None):
        super().__init__()
        self.bgcolor = bgcolor
        self.border_radius = 12
        self.width = width
        self.height = height
        self.alignment = ft.Alignment.CENTER
        self.animate_scale = ft.Animation(150, "decelerate")
        
        self.shadow = ft.BoxShadow(
            blur_radius=8, 
            color=ft.Colors.with_opacity(0.4, bgcolor), 
            offset=ft.Offset(0, 4)
        )

        if icono:
            self.content = ft.Row(
                [ft.Icon(icono, color=color_texto), ft.Text(texto, color=color_texto, weight="bold")], 
                alignment=ft.MainAxisAlignment.CENTER, 
                spacing=10
            )
        else:
            self.content = ft.Text(texto, color=color_texto, weight="bold")

        self._accion_original = on_click
        self.on_click = self._animar_y_ejecutar

    async def _animar_y_ejecutar(self, e):
        if not self.page:
            return
        
        self.scale = 0.95
        self.shadow.offset = ft.Offset(0, 1)
        self.update()
        
        await asyncio.sleep(0.1) 
        if getattr(self, "page", None):
            self.scale = 1.0
            self.shadow.offset = ft.Offset(0, 4)
            self.update()
        
        self.scale = 1.0
        self.shadow.offset = ft.Offset(0, 4)
        self.update()
        
        if self._accion_original:
            if inspect.iscoroutinefunction(self._accion_original):
                await self._accion_original(e)
            else:
                resultado = self._accion_original(e)
                if inspect.isawaitable(resultado):
                    await resultado


async def on_click_animado(self, e):
    # Lógica de animación inicial (ej. cambio de color, escala)
    if getattr(self, "page", None):
        self.update()
    
    await asyncio.sleep(0.1) # Espera de la animación
    
    # Lógica de retorno de animación
    # Validación crucial antes de actualizar para evitar Detached Control
    if getattr(self, "page", None):
        self.update()
        
    # Ejecutar función pasada por el usuario
    if self.on_click:
        await self.on_click(e)                    

class BarraNavegacion(ft.AppBar): 
    def __init__(self, titulo, page, usuario =None): 
        super().__init__() 
        self.pagina_actual = page 
        self.bgcolor = COLOR_PRIMARIO 

        self.title = titulo
        self.center_title = True 
        
        self.leading = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW, 
            icon_color=COLOR_TEXTO, 
            on_click=self._retroceder,
            tooltip="Retroceder"
        )

        self.actions = [
            ft.IconButton(
                icon=ft.Icons.LOGOUT,
                icon_color=COLOR_TEXTO,
                on_click=self._cerrar_sesion,
                tooltip="Cerrar Sesión"
            )
        ]

    async def _retroceder(self, e):
        try:
            historial = self.pagina_actual.session.store.get("historial_navegacion") or []
            if len(historial) > 1:
                historial.pop()
                ruta_anterior = historial[-1]
                self.pagina_actual.session.store.set("historial_navegacion", historial)
                self.pagina_actual.go(ruta_anterior)
            else:
                await self._cerrar_sesion(e)
        except Exception as ex:
            print(f"Error al retroceder: {ex}")
            self.pagina_actual.go("/login")

    async def _cerrar_sesion(self, e):
        if hasattr(self.pagina_actual, 'gestor_nav'):
            await self.pagina_actual.gestor_nav.cerrar_sesion_y_redirigir()
        else:
            self.pagina_actual.go("/login")