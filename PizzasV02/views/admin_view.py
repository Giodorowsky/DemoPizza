import flet as ft
from datos_negocio import COLOR_FONDO, COLOR_PRIMARIO, COLOR_CONTRASTE, COLOR_TEXTO, SUCURSALES_CATALOGO
from views.stats.global_stats_view import GlobalStatsView
from views.componentes.botones import BotonAnimado

class AdminView(ft.PageView):
    """Vista principal para el rol de Administrador/Dueño antes de seleccionar sucursal."""
    def __init__(self, db, gestor_nav):
        super().__init__(expand=True)
        self.db = db
        self.gestor_nav = gestor_nav

        opciones_sucursal = [
            BotonAnimado(
                f"INGRESAR A {suc}",
                on_click=lambda _, s=suc: self.gestor_nav.page.run_task(self.gestor_nav.procesar_seleccion_sucursal, s),
                width=300,
                bgcolor=COLOR_PRIMARIO if suc == "MATRIZ" else COLOR_CONTRASTE
            ) for suc in SUCURSALES_CATALOGO
        ]

        vista_seleccion = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Text("ACCESO DE ADMINISTRADOR", size=16, color=ft.Colors.GREY_500),
                    ft.Text("Desliza a la izquierda para estadísticas", size=12, color=ft.Colors.GREY_600, italic=True),
                    ft.Container(height=10),
                    ft.Text("Selecciona una Sucursal", size=28, weight="bold", color=COLOR_TEXTO),
                    ft.Column(opciones_sucursal, spacing=15, alignment=ft.MainAxisAlignment.CENTER)
                ]
            )
        )

        self.controls = [
            GlobalStatsView(self.db),
            vista_seleccion
        ]