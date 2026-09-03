import flet as ft
from datos_negocio import COLOR_FONDO, COLOR_PRIMARIO, COLOR_TEXTO, COLOR_CONTRASTE
from views.componentes.botones import BotonAnimado
from views.stats.components.kpi_card import KpiCard

class LocalStatsView(ft.Container):
    def __init__(self, db, gestor_nav=None):
        super().__init__()
        self.db = db
        self.gestor_nav = gestor_nav
        self.expand = True
        self.bgcolor = COLOR_FONDO
        self.padding = 20
        self.running = False

        self.grid_stats = ft.ResponsiveRow(spacing=15, run_spacing=15)

        self.content = ft.Column(
            scroll=ft.ScrollMode.ADAPTIVE,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(height=10),
                ft.Text("DASHBOARD EMPRESARIAL", size=26, weight="bold", color=COLOR_PRIMARIO),
                ft.Text("Rendimiento del turno actual", color=ft.Colors.GREY_400, size=14),
                ft.Divider(height=30, color=ft.Colors.GREY_800),
                
                self.grid_stats,
                
                ft.Container(height=30),
                BotonAnimado(
                    "ACTUALIZAR MÉTRICAS", 
                    on_click=self.actualizar_metricas_manualmente, 
                    width=280, 
                    bgcolor=COLOR_CONTRASTE
                ),
                ft.Container(height=20),
            ]
        )

    def did_mount(self):
        self.running = True 
        self.page.run_task(self.cargar_datos_financieros)

    def will_unmount(self):
        self.running = False

    async def actualizar_metricas_manualmente(self, e):
        await self.cargar_datos_financieros()

    async def cargar_datos_financieros(self, *args):
        if not getattr(self, "running", False):
            return 
            
        try:
            self.grid_stats.controls = [ft.ProgressRing(color=COLOR_PRIMARIO)]
            self.update() 

            # 1. Recuperación resiliente de la sucursal desde la sesión de Flet o el gestor
            sucursal_actual = None
            if self.page and self.page.session.store.get("sucursal_actual"):
                sucursal_actual = self.page.session.store.get("sucursal_actual")
            elif self.gestor_nav and hasattr(self.gestor_nav, "sucursal_actual"):
                sucursal_actual = self.gestor_nav.sucursal_actual

            # Normalizar string (p. ej. "SUCURSAL2")
            if sucursal_actual:
                sucursal_actual = str(sucursal_actual).strip()

            # Validación Fail-Fast
            if not sucursal_actual:
                self.grid_stats.controls = [
                    ft.Text("❌ Error de contexto: Sucursal no identificada. Inicie sesión nuevamente.", color=ft.Colors.RED)
                ]
                self.update()
                return

            # 2. Consulta a la base de datos
            data = await self.db.obtener_resumen_dia(sucursal=sucursal_actual) 
            
            if not self.running:
                return

            self.grid_stats.controls = [
                KpiCard("NETO EN CAJA", f"${data.get('neto_efectivo', 0.0):,.2f}", ft.Icons.ACCOUNT_BALANCE_WALLET, ft.Colors.GREEN_ACCENT, col_size=12),
                KpiCard("VENTAS TOTALES", f"${data.get('total', 0.0):,.2f}", ft.Icons.MONETIZATION_ON, ft.Colors.GREEN),
                KpiCard("GASTOS", f"${data.get('gastos', 0.0):,.2f}", ft.Icons.OUTBOUND, ft.Colors.RED),
                KpiCard("EFECTIVO BRUTO", f"${data.get('efectivo', 0.0):,.2f}", ft.Icons.PAYMENTS_OUTLINED, ft.Colors.BLUE),
                KpiCard("TARJETA", f"${data.get('tarjeta', 0.0):,.2f}", ft.Icons.CREDIT_CARD, ft.Colors.PURPLE),
                KpiCard("LOCAL", f"{data.get('local', 0)} tickets", ft.Icons.RESTAURANT, ft.Colors.AMBER),
                KpiCard("DOMICILIO", f"{data.get('domicilio', 0)} tickets", ft.Icons.DELIVERY_DINING, ft.Colors.ORANGE),
            ]
            self.update()
        except Exception as ex:
            print(f"Error en LocalStatsView: {ex}")
            if self.running:
                self.grid_stats.controls = [ft.Text(f"Error al cargar datos: {ex}", color=ft.Colors.RED)]
                try:
                    self.update()
                except Exception:
                    pass