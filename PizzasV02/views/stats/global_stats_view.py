import flet as ft
import flet_charts as fch
import asyncio
from datetime import datetime, timedelta
from datos_negocio import COLOR_FONDO
from views.componentes.botones import BotonAnimado
from views.stats.components.kpi_card import KpiCard
from views.stats.components.chart_card import crear_tarjeta_grafica

class GlobalStatsView(ft.Container):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.expand = True
        self.bgcolor = COLOR_FONDO 
        self.padding = 30
        self.running = False

        self.grid_stats = ft.ResponsiveRow(spacing=20, run_spacing=20)

        # 1. Gráfica de Líneas
        self.grafica_lineas = fch.LineChart(
            horizontal_grid_lines=fch.ChartGridLines(interval=1000, color=ft.Colors.with_opacity(0.1, ft.Colors.CYAN_ACCENT), width=1, dash_pattern=[4, 4]),
            vertical_grid_lines=fch.ChartGridLines(interval=1, color=ft.Colors.with_opacity(0.05, ft.Colors.CYAN_ACCENT), width=1, dash_pattern=[4, 4]),
            interactive=True,
            height=260,
            bgcolor=ft.Colors.TRANSPARENT,
            border=ft.Border(
                bottom=ft.BorderSide(2, ft.Colors.with_opacity(0.6, ft.Colors.CYAN_ACCENT)),
                left=ft.BorderSide(2, ft.Colors.with_opacity(0.6, ft.Colors.CYAN_ACCENT))
            ),
            data_series=[]
        )
        self.tarjeta_grafica_lineas = crear_tarjeta_grafica(
            "PROYECCIÓN COMPARATIVA DE SUCURSALES", "FLUJO DE INGRESOS - ÚLTIMOS 7 DÍAS",
            ft.Icons.MULTILINE_CHART, ft.Colors.CYAN_ACCENT, self.grafica_lineas, {"xs": 12, "sm": 12}
        )

        # 2. Gráfica Circular
        self.grafica_pastel = fch.PieChart(
            center_space_radius=45,
            center_space_color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
            sections_space=5,
            sections=[]
        )
        self.tarjeta_ranking_productos = crear_tarjeta_grafica(
            "TOP 5 PRODUCTOS", "MATRIZ DE DEMANDA GLOBAL",
            ft.Icons.DONUT_LARGE, ft.Colors.PURPLE_ACCENT, self.grafica_pastel, {"xs": 12, "sm": 6, "md": 5}
        )

        # 3. Gráfica de Barras
        self.grafica_barras = fch.BarChart(
            height=240,
            bgcolor=ft.Colors.TRANSPARENT,
            border=ft.Border(bottom=ft.BorderSide(2, ft.Colors.with_opacity(0.6, ft.Colors.AMBER_ACCENT))),
            groups=[],
            interactive=True
        )
        self.tarjeta_ventas_semana = crear_tarjeta_grafica(
            "MATRIZ VS SUCURSAL2", "VENTAS ÚLTIMAS 4 SEMANAS",
            ft.Icons.BAR_CHART, ft.Colors.AMBER_ACCENT, self.grafica_barras, {"xs": 12, "sm": 6, "md": 7}
        )

        self.content = ft.Column(
            scroll=ft.ScrollMode.ADAPTIVE,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(height=10),
                ft.Text("CENTRAL DE ESTADÍSTICAS GLOBAL", size=32, weight="w900", color=ft.Colors.WHITE, font_family="monospace", 
                        spans=[ft.TextSpan(" v3.0", ft.TextStyle(color=ft.Colors.CYAN_ACCENT, size=18, italic=True))]),
                ft.Text("ANÁLISIS DE RENDIMIENTO EN TIEMPO REAL", color=ft.Colors.CYAN_400, size=14, font_family="monospace", weight="bold"),
                ft.Divider(height=40, color=ft.Colors.with_opacity(0.2, ft.Colors.CYAN_ACCENT)),
                
                self.tarjeta_grafica_lineas,
                ft.Container(height=10),

                ft.ResponsiveRow([
                    self.tarjeta_ranking_productos,
                    self.tarjeta_ventas_semana
                ], spacing=20, run_spacing=20),
                
                ft.Container(height=15),
                self.grid_stats,
                
                ft.Container(height=35),
                BotonAnimado(
                    "SINCRONIZAR NÚCLEO DE DATOS", 
                    on_click=self.actualizar_metricas_manualmente, 
                    width=320, 
                    bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.CYAN_700)
                ),
                ft.Container(height=30),
            ]
        )

    def did_mount(self):
        self.running = True
        self.page.run_task(self.cargar_datos_globales)

    def will_unmount(self):
        self.running = False

    async def actualizar_metricas_manualmente(self, e):
        await self.cargar_datos_globales(e)

    async def cargar_datos_globales(self, *args):
        if not getattr(self, "running", False):
            return

        try:
            self.grid_stats.controls = [ft.ProgressRing(color=ft.Colors.CYAN_ACCENT)]
            self.update()

            datos_globales, ventas_comparativas, ranking_productos, ventas_semanales = await asyncio.gather(
                self.db.obtener_resumen_global_dia(),
                self.db.obtener_ventas_comparativas_sucursales(dias=7),
                self.db.obtener_ranking_pizzas(sucursal=None, limite=5),
                self.db.obtener_ventas_semanales_comparativas(semanas=4)
            )

            if not self.running:
                return

            # --- 1. KPIs ---
            self.grid_stats.controls = [
                KpiCard("NETO EN CAJA (GLOBAL)", f"${datos_globales.get('neto_efectivo', 0.0):,.2f}", ft.Icons.ACCOUNT_BALANCE_WALLET, ft.Colors.CYAN_ACCENT, col_size=12, estilo_global=True),
                KpiCard("VENTAS TOTALES (GLOBAL)", f"${datos_globales.get('total', 0.0):,.2f}", ft.Icons.MONETIZATION_ON, ft.Colors.GREEN_ACCENT, estilo_global=True),
                KpiCard("GASTOS (GLOBAL)", f"${datos_globales.get('gastos', 0.0):,.2f}", ft.Icons.OUTBOUND, ft.Colors.PINK_ACCENT, estilo_global=True),
            ]
            
            # --- 2. Gráfica de Líneas ---
            colores_sucursal_neon = [ft.Colors.GREEN_ACCENT, ft.Colors.RED_ACCENT, ft.Colors.CYAN_ACCENT]
            series_lineas = []
            max_venta_lineas = 1000
            
            # Construir eje X usando las fechas realmente presentes en los datos para evitar desfases por zonas horarias
            hoy = datetime.now().date()
            all_dates = set()
            for ventas_lista in ventas_comparativas.values():
                for v in ventas_lista:
                    d = (v['dia'].date() if hasattr(v['dia'], 'date') else v['dia'])
                    all_dates.add(d)

            if all_dates:
                fechas_eje_x = sorted(list(all_dates))
                # Normalizar a ventana de 7 días: si hay más, tomar los últimos 7; si hay menos, completar desde hoy hacia atrás
                if len(fechas_eje_x) >= 7:
                    fechas_eje_x = fechas_eje_x[-7:]
                else:
                    fechas_eje_x = [(hoy - timedelta(days=i)) for i in range(6, -1, -1)]
            else:
                fechas_eje_x = [(hoy - timedelta(days=i)) for i in range(6, -1, -1)]

            for idx, (sucursal, ventas) in enumerate(ventas_comparativas.items()):
                puntos = []
                ventas_dict = {(v['dia'].date() if hasattr(v['dia'], 'date') else v['dia']): float(v['total_ventas']) for v in ventas}
                for i, fecha in enumerate(fechas_eje_x):
                    venta_dia = ventas_dict.get(fecha, 0.0)
                    puntos.append(fch.LineChartDataPoint(i, venta_dia))
                    if venta_dia > max_venta_lineas: 
                        max_venta_lineas = venta_dia

                color_glow = colores_sucursal_neon[idx % len(colores_sucursal_neon)]
                series_lineas.append(fch.LineChartData(
                    points=puntos, stroke_width=3, color=color_glow, curved=False,
                    point=fch.ChartCirclePoint(radius=5, color=color_glow, stroke_color=ft.Colors.WHITE, stroke_width=1.5),
                    selected_point=fch.ChartCirclePoint(radius=7, color=color_glow, stroke_color=ft.Colors.WHITE, stroke_width=2),
                    below_line_gradient=ft.LinearGradient(
                        begin=ft.Alignment.TOP_CENTER, end=ft.Alignment.BOTTOM_CENTER,
                        colors=[ft.Colors.with_opacity(0.3, color_glow), ft.Colors.TRANSPARENT]
                    )
                ))
            
            self.grafica_lineas.data_series = series_lineas
            self.grafica_lineas.max_y = max(max_venta_lineas * 1.1, 100.0)
            self.grafica_lineas.min_x = 0
            self.grafica_lineas.max_x = 6
            self.grafica_lineas.left_axis = fch.ChartAxis(
                labels=[fch.ChartAxisLabel(value=i, label=ft.Text(f"${int(i/1000)}k", color=ft.Colors.WHITE, size=10)) 
                        for i in range(0, int(self.grafica_lineas.max_y) + 1000, 2000)]
            )
            self.grafica_lineas.bottom_axis = fch.ChartAxis(
                labels=[fch.ChartAxisLabel(value=i, label=ft.Text(fecha.strftime("%d/%m"), color=ft.Colors.WHITE, size=10)) 
                        for i, fecha in enumerate(fechas_eje_x)]
            )

            # --- 3. Gráfica Circular ---
            colores_pastel = [ft.Colors.PURPLE_ACCENT, ft.Colors.CYAN_ACCENT, ft.Colors.AMBER_ACCENT, ft.Colors.PINK_ACCENT, ft.Colors.LIGHT_GREEN_ACCENT]
            secciones_pastel = []
            if ranking_productos:
                for i, producto in enumerate(ranking_productos):
                    radio_simulado = 55 + (i * 3)
                    color_seccion = colores_pastel[i % len(colores_pastel)]
                    nombre_producto = producto.get('nombre') or producto.get('pizza_nombre') or producto.get('sabor') or 'Producto'
                    secciones_pastel.append(fch.PieChartSection(
                        value=float(producto['cantidad']),
                        title=f"{nombre_producto}\n({int(producto['cantidad'])})",
                        color=ft.Colors.with_opacity(0.9, color_seccion),
                        radius=radio_simulado,
                        title_style=ft.TextStyle(size=10, color=ft.Colors.WHITE, weight="bold")
                    ))
            self.grafica_pastel.sections = secciones_pastel

            # --- 4. Gráfica de Barras ---
            semanas_eje_x = [(hoy - timedelta(weeks=i)) for i in range(3, -1, -1)]
            semanas_dict = {s.isocalendar()[1]: i for i, s in enumerate(semanas_eje_x)}

            ventas_procesadas = {"MATRIZ": [0.0] * 4, "SUCURSAL2": [0.0] * 4}
            max_venta_barras = 1000

            for sucursal, ventas in ventas_semanales.items():
                if sucursal in ventas_procesadas:
                    for venta in ventas:
                        semana_iso = venta['semana'].isocalendar()[1]
                        if semana_iso in semanas_dict:
                            idx = semanas_dict[semana_iso]
                            total = float(venta['total_ventas'])
                            ventas_procesadas[sucursal][idx] = total
                            if total > max_venta_barras:
                                max_venta_barras = total

            grupos_barras = []
            for i in range(4):
                grupos_barras.append(
                    fch.BarChartGroup(
                        x=i,
                        rods=[
                            fch.BarChartRod(from_y=0, to_y=ventas_procesadas["MATRIZ"][i], width=18, color=ft.Colors.CYAN_ACCENT, border_radius=6),
                            fch.BarChartRod(from_y=0, to_y=ventas_procesadas["SUCURSAL2"][i], width=18, color=ft.Colors.PINK_ACCENT, border_radius=6),
                        ]
                    )
                )
            
            self.grafica_barras.groups = grupos_barras
            self.grafica_barras.max_y = max(max_venta_barras * 1.1, 100.0)
            self.grafica_barras.bottom_axis = fch.ChartAxis(
                labels=[fch.ChartAxisLabel(value=i, label=ft.Text(f"Sem {i+1}", color=ft.Colors.WHITE, size=11, weight="bold")) for i in range(4)]
            )

            self.grafica_lineas.update()
            self.grafica_pastel.update()
            self.grafica_barras.update()
            self.update()
            
        except Exception as ex:
            print(f"Error en GlobalStatsView: {ex}")
            if self.running:
                self.grid_stats.controls = [ft.Text("Error en el núcleo de datos.", color=ft.Colors.RED_ACCENT, font_family="monospace")]
                try:
                    self.update()
                except Exception:
                    pass