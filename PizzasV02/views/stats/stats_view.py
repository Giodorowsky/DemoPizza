import flet as ft
from datos_negocio import COLOR_FONDO, COLOR_PRIMARIO, COLOR_CONTRASTE
from views.stats.local_stats_view import LocalStatsView
from views.stats.global_stats_view import GlobalStatsView

class StatsView(ft.Container):
    def __init__(self, db, gestor_nav=None):
        super().__init__()
        self.db = db
        self.gestor_nav = gestor_nav
        self.expand = True
        self.bgcolor = COLOR_FONDO

        # Instanciación de las sub-vistas
        self.vista_local = LocalStatsView(db=self.db, gestor_nav=self.gestor_nav)
        self.vista_global = GlobalStatsView(db=self.db)

        # Estructura oficial de Flet según la documentación actual
        self.tabs = ft.Tabs(
            length=2,
            selected_index=0,
            expand=True,
            on_change=self.al_cambiar_pestana,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        indicator_color=COLOR_CONTRASTE,
                        label_color=COLOR_PRIMARIO,
                        unselected_label_color=ft.Colors.GREY_500,
                        tabs=[
                            ft.Tab(label="Sucursal Actual", icon=ft.Icons.STORE),
                            ft.Tab(label="Central Global", icon=ft.Icons.QUERY_STATS),
                        ],
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            self.vista_local,
                            self.vista_global,
                        ],
                    ),
                ],
            ),
        )

        self.content = self.tabs

    def al_cambiar_pestana(self, e):
        # Refresca las métricas de la sucursal local al seleccionar la primera pestaña (índice 0)
        if e.control.selected_index == 0 and hasattr(self.vista_local, "cargar_datos_financieros"):
            self.page.run_task(self.vista_local.cargar_datos_financieros)