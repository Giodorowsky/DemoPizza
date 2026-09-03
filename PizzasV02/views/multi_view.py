import flet as ft
# Importamos LocalStatsView directamente para eliminar las pestañas globales en el dashboard de sucursal
from views.stats.local_stats_view import LocalStatsView
from views.pos_view import PosView
from views.cocina_view import CocinaView
from views.gastos_view import GastosView
from views.corte_view import CorteView
from views.historial_view import HistorialView
from views.repa_view import RepaView 

class MultiViewContainer(ft.Container):
    """
    Contenedor principal que utiliza un PageView para permitir 
    el desplazamiento lateral (swipe) entre diferentes vistas.
    """
    def __init__(self, usuario, db, gestor_nav):
        super().__init__()
        self.usuario = usuario
        self.db = db
        self.gestor_nav = gestor_nav 
        self.expand = True
        
        self.page_view = ft.PageView(
            expand=True,
            controls=self._configurar_paginas_por_rol(),
            animate_size=ft.Animation(400, ft.AnimationCurve.DECELERATE),
        )
        
        self.content = self.page_view

    def _configurar_paginas_por_rol(self):
        paginas = []
        rol = self.usuario.get("rol", "") if self.usuario else ""
        sucursal_activa = self.gestor_nav.sucursal_actual

        if rol == "DUEÑO":
            # 1. Estadísticas exclusivas de la sucursal seleccionada (LocalStatsView)
            paginas.append(LocalStatsView(db=self.db, gestor_nav=self.gestor_nav))
            # 2. Historial de pedidos de la sucursal seleccionada
            paginas.append(HistorialView(self.db, self.gestor_nav))
            # 3. Vista del corte de caja por sucursal
            paginas.append(CorteView(self.db, self.gestor_nav, sucursal=sucursal_activa))
            
        elif rol == "CAJERA":
            paginas.append(PosView(self.gestor_nav, self.db))
            paginas.append(GastosView(self.db, self.usuario.get("nombre", "Usuario")))
            paginas.append(HistorialView(self.db, self.gestor_nav))
            
        elif rol == "COCINA":
            paginas.append(CocinaView(self.db, sucursal=sucursal_activa))
            
        elif rol == "REPARTIDOR":
            paginas.append(RepaView(self.db, self.usuario))
        
        return paginas

    async def ir_a_pagina(self, indice):
        self.page_view.page_index = indice
        self.update()