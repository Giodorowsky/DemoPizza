import asyncio
import flet as ft
from datos_negocio import (
    COLOR_FONDO,
    COLOR_PRIMARIO,
    COLOR_CONTRASTE,
    COLOR_TEXTO,
    COLOR_EXITO,
    COLOR_ERROR,
    COLOR_SECUNDARIO
)
from views.componentes.botones import BotonAnimado


class CorteView(ft.Container):
    """
    Vista responsable de mostrar la información financiera del turno actual
    y procesar el cierre de caja (corte) de la sucursal activa.
    """
    def __init__(self, db, gestor_nav, sucursal=None):
        super().__init__(expand=True, bgcolor=COLOR_FONDO, padding=20)
        self.db = db
        self.gestor_nav = gestor_nav
        
        # 1. Resolución segura de la sucursal activa
        self.sucursal = (
        sucursal 
        or (self.gestor_nav.sucursal_actual if self.gestor_nav else None)
        or (self.page.session.store.get("sucursal_actual") if self.page else None)
        or "MATRIZ"
    )

        # 2. Controles de UI para valores métricos
        self.lbl_efectivo = ft.Text("$0.00", size=22, weight="bold", color=COLOR_TEXTO)
        self.lbl_tarjeta = ft.Text("$0.00", size=22, weight="bold", color=COLOR_TEXTO)
        self.lbl_total_ventas = ft.Text("$0.00", size=24, weight="bold", color=COLOR_EXITO)
        self.lbl_gastos = ft.Text("$0.00", size=22, weight="bold", color=COLOR_ERROR)
        self.lbl_neto = ft.Text("$0.00", size=28, weight="bold", color=ft.Colors.GREEN_400)
        self.lbl_local = ft.Text("0 tickets", size=16, color=ft.Colors.GREY_400)
        self.lbl_domicilio = ft.Text("0 tickets", size=16, color=ft.Colors.GREY_400)

        # Indicador de carga
        self.loader = ft.ProgressRing(visible=False, width=24, height=24, stroke_width=3)
        self.dialogo_confirmacion = None

        # 3. Construcción del layout de la vista
        self.content = self._construir_interfaz()

    def did_mount(self):
        """Lifecycle de Flet: Inicia la carga asíncrona segura al montar la vista."""
        if getattr(self, "page", None):
            self.page.run_task(self.cargar_datos_corte)

    def _crear_tarjeta_metrica(self, titulo, control_valor, icono, color_icono, subtexto=None):
        """Genera tarjetas de resumen con estilo unificado y adaptabilidad."""
        elementos = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(titulo, size=14, weight="bold", color=ft.Colors.GREY_400),
                    ft.Icon(icono, color=color_icono, size=24),
                ]
            ),
            ft.Container(height=5),
            control_valor
        ]

        if subtexto:
            elementos.append(subtexto)

        return ft.Container(
            expand=True,
            padding=15,
            bgcolor=COLOR_CONTRASTE,
            border_radius=12,
            content=ft.Column(controls=elementos, spacing=2)
        )

    def _construir_interfaz(self):
        """Ensambla el encabezado, tarjetas de métricas y botón de acción."""
        # Encabezado con título de la sucursal y botón de recarga manual
        encabezado = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text("CORTE DE CAJA", size=26, weight="bold", color=COLOR_PRIMARIO),
                        ft.Text(f"SUCURSAL: {self.sucursal.upper()}", size=14, color=ft.Colors.GREY_400, weight="bold"),
                    ]
                ),
                ft.Row([
                    self.loader,
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        icon_color=COLOR_TEXTO,
                        tooltip="Recargar Datos",
                        on_click=lambda _: self.page.run_task(self.cargar_datos_corte)
                    )
                ])
            ]
        )

        # Filas de métricas financieras
        fila_ventas = ft.Row(
            spacing=15,
            controls=[
                self._crear_tarjeta_metrica("EFECTIVO EN VENTAS", self.lbl_efectivo, ft.Icons.MONEY, COLOR_EXITO),
                self._crear_tarjeta_metrica("TARJETA EN VENTAS", self.lbl_tarjeta, ft.Icons.CREDIT_CARD, COLOR_PRIMARIO),
                self._crear_tarjeta_metrica("TOTAL VENTAS BRUTAS", self.lbl_total_ventas, ft.Icons.POINT_OF_SALE, COLOR_EXITO),
            ]
        )

        fila_balance = ft.Row(
            spacing=15,
            controls=[
                self._crear_tarjeta_metrica("GASTOS DEL TURNO", self.lbl_gastos, ft.Icons.MONEY_OFF, COLOR_ERROR),
                self._crear_tarjeta_metrica("PEDIDOS / TICKETS", self.lbl_local, ft.Icons.RECEIPT_LONG, COLOR_SECUNDARIO, subtexto=self.lbl_domicilio),
                self._crear_tarjeta_metrica("NETO EFECTIVO EN CAJA", self.lbl_neto, ft.Icons.ACCOUNT_BALANCE_WALLET, ft.Colors.GREEN_400),
            ]
        )

        # Botón para ejecutar el corte de caja
        boton_corte = BotonAnimado(
            "REALIZAR CORTE DE CAJA",
            on_click=self.solicitar_confirmacion_corte,
            bgcolor=COLOR_ERROR,
            width=360,
            height=55
        )

        return ft.Column(
            expand=True,
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                encabezado,
                ft.Divider(color=ft.Colors.GREY_800),
                fila_ventas,
                fila_balance,
                ft.Container(height=20),
                boton_corte,
                ft.Text(
                    "Al realizar el corte, los registros actuales cambiarán de estado a 'Cerrado' y la caja reiniciará en $0.00.",
                    size=12, color=ft.Colors.GREY_500, italic=True, text_align=ft.TextAlign.CENTER
                )
            ]
        )

    def mostrar_cargando(self, estado: bool):
        """Activa o desactiva el spinner de carga de forma segura."""
        self.loader.visible = estado
        if getattr(self, "page", None):
            self.update()

    async def cargar_datos_corte(self):
        """Consulta los datos del turno actual a la BD acotados por la sucursal."""
        self.mostrar_cargando(True)
        try:
            # Consulta a la base de datos aplicando el filtro de sucursal
            resumen = await self.db.obtener_resumen_dia(sucursal=self.sucursal)
            
            # Asignación segura de variables
            efectivo = resumen.get("efectivo", 0.0)
            tarjeta = resumen.get("tarjeta", 0.0)
            total = resumen.get("total", 0.0)
            gastos = resumen.get("gastos", 0.0)
            neto = resumen.get("neto_efectivo", 0.0)
            t_local = resumen.get("local", 0)
            t_domicilio = resumen.get("domicilio", 0)

            # Actualización de la UI
            self.lbl_efectivo.value = f"${efectivo:,.2f}"
            self.lbl_tarjeta.value = f"${tarjeta:,.2f}"
            self.lbl_total_ventas.value = f"${total:,.2f}"
            self.lbl_gastos.value = f"${gastos:,.2f}"
            self.lbl_neto.value = f"${neto:,.2f}"
            self.lbl_local.value = f"Local: {t_local} pedidos"
            self.lbl_domicilio.value = f"Domicilio: {t_domicilio} pedidos"

        except Exception as ex:
            print(f"Error al cargar datos del corte ({self.sucursal}): {ex}")
            if hasattr(self.gestor_nav, "_notificar"):
                self.gestor_nav._notificar(f"Error cargando corte: {ex}", "red")
        finally:
            self.mostrar_cargando(False)

    def solicitar_confirmacion_corte(self, e):
        """Abre un diálogo modal para solicitar la confirmación del usuario."""
        def cerrar_dialogo(e_dialog):
            self.dialogo_confirmacion.open = False
            self.page.update()

        def confirmar_y_ejecutar(e_dialog):
            self.dialogo_confirmacion.open = False
            self.page.update()
            self.page.run_task(self.ejecutar_corte)

        self.dialogo_confirmacion = ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Confirmar Corte de Caja?"),
            content=ft.Text(f"Se procesará el cierre definitivo del turno para la sucursal {self.sucursal.upper()}."),
            actions=[
                ft.TextButton("CANCELAR", on_click=cerrar_dialogo),
                ft.ElevatedButton("CONFIRMAR Y CERRAR", on_click=confirmar_y_ejecutar, style=ft.ButtonStyle(bgcolor=COLOR_ERROR, color=ft.Colors.WHITE)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(self.dialogo_confirmacion)
        self.dialogo_confirmacion.open = True
        self.page.update()

    async def ejecutar_corte(self):
        """Procesa el arqueo/cierre en la BD y fuerza la recarga limpia de vistas."""
        self.mostrar_cargando(True)
        try:
            # 1. Ejecutar el corte en la base de datos invocando el método real del manager
            exito = await self.db.cerrar_dia_operativo(self.sucursal)

            if exito:
                # 2. Notificación global de éxito
                if hasattr(self.gestor_nav, "_notificar"):
                    self.gestor_nav._notificar(f"¡Corte de caja completado para {self.sucursal.upper()}!", "green")

                # 3. Forzar reconstrucción completa de vistas para limpiar datos fantasma
                await self.gestor_nav.cambiar_sucursal_y_recargar(self.sucursal)
            else:
                if hasattr(self.gestor_nav, "_notificar"):
                    self.gestor_nav._notificar("No se pudo completar el cierre en la base de datos", "red")

        except Exception as ex:
            print(f"Error al procesar el corte: {ex}")
            if hasattr(self.gestor_nav, "_notificar"):
                self.gestor_nav._notificar(f"Error al realizar el corte: {ex}", "red")
            self.mostrar_cargando(False)