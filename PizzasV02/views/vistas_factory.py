import flet as ft
from views.componentes.tarjetas import SelectorGrid
from views.componentes.botones import BotonAnimado
from datos_negocio import (
    COLOR_ERROR, COLOR_EXITO, COLOR_FONDO, 
    COLOR_SECUNDARIO, COLOR_PRIMARIO, COLOR_CONTRASTE, COLOR_TEXTO
)

class VistasFactory:
    """Clase encargada de construir la interfaz gráfica (UI) de forma desacoplada."""

    @staticmethod
    def crear_vista_servicio(al_seleccionar):
        from datos_negocio import SERVICIO_LOCAL, SERVICIO_DOMICILIO, COLOR_NUEVO
        opciones = [
            ["LOCAL", ft.Icons.RESTAURANT, SERVICIO_LOCAL, None, COLOR_NUEVO],
            ["DOMICILIO", ft.Icons.DELIVERY_DINING, SERVICIO_DOMICILIO, None, ft.Colors.RED_600]
        ]
        return SelectorGrid(
            titulo="TIPO DE SERVICIO",
            opciones=opciones,
            al_seleccionar=al_seleccionar,
            columnas=1
        )

    @staticmethod
    def crear_vista_tamano(opciones, al_seleccionar, al_cancelar, al_clic_especial=None):
        controls = [
            SelectorGrid(titulo="TAMAÑO", opciones=opciones, al_seleccionar=al_seleccionar),
        ]
        
        # Si se define un botón especial rectangular (para Mega y Barra / Promociones)
        if al_clic_especial:
            controls.append(
                BotonAnimado(
                    "PIZZAS MEGA, BARRA Y REFRESCOS", 
                    on_click=al_clic_especial, 
                    bgcolor=COLOR_SECUNDARIO, 
                    width=380, 
                    height=55
                )
            )
            
        controls.append(BotonAnimado("CANCELAR", on_click=al_cancelar, bgcolor=COLOR_ERROR))
        
        return ft.Column(
            alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15,
            controls=controls
        )

    @staticmethod
    def crear_vista_promociones(opciones, al_seleccionar, al_volver):
        return ft.Column(
            alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15,
            controls=[
                SelectorGrid("PROMOCIONES", opciones, al_seleccionar),
                ft.Text("¡Estas pizzas incluyen refresco gratis!", size=16, color=COLOR_EXITO, italic=True),
                ft.Container(height=10),
                BotonAnimado("VOLVER A TAMAÑOS", on_click=al_volver, bgcolor=COLOR_SECUNDARIO)
            ]
        )

    @staticmethod
    def crear_vista_sabores(titulo, opciones, al_seleccionar, al_cancelar):
        return ft.Column(
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.ADAPTIVE,
            controls=[
                SelectorGrid(titulo=titulo, opciones=opciones, al_seleccionar=al_seleccionar, columnas=2),
                ft.Container(height=20),
                BotonAnimado("CANCELAR PIZZA", on_click=al_cancelar, bgcolor=COLOR_ERROR, width=300)
            ]
        )

    @staticmethod
    def crear_vista_refresco(opciones, al_seleccionar):
        return SelectorGrid("REFRESCO GRATIS", opciones, al_seleccionar, 2)

    @staticmethod
    def crear_vista_resumen(total, al_agregar, al_finalizar):
        return ft.Column(
            alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20,
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=COLOR_EXITO, size=80),
                ft.Text("¡AGREGADO!", size=28, weight="bold"),
                ft.Text(f"Total Carrito: ${total}", size=22, color=COLOR_TEXTO),
                ft.Container(height=10),
                BotonAnimado("AGREGAR OTRA PIZZA", on_click=al_agregar, bgcolor=COLOR_CONTRASTE, width=300),
                BotonAnimado("FINALIZAR Y PAGAR", on_click=al_finalizar, bgcolor=COLOR_PRIMARIO, width=300)
            ]
        )

    @staticmethod
    def crear_vista_pago(total, al_seleccionar_efectivo, al_seleccionar_tarjeta, al_guardar, al_corregir, metodo_actual=None):
        def _boton_pago(metodo, icono, accion):
            # Verificamos si este botón es el seleccionado actualmente
            es_seleccionado = (metodo == metodo_actual)
            
            # Aplicamos colores dinámicos
            color_bg = COLOR_PRIMARIO if es_seleccionado else COLOR_CONTRASTE
            color_borde = ft.Colors.GREEN_400 if es_seleccionado else ft.Colors.TRANSPARENT

            return ft.Container(
                content=ft.Column([
                    ft.Icon(icono, size=40, color=COLOR_TEXTO), 
                    ft.Text(metodo, weight="bold")
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=150, height=120, bgcolor=color_bg, border_radius=15,
                border=ft.Border.all(3, color_borde), # Borde para resaltar
                on_click=lambda e: accion(e),
                animate_scale=ft.Animation(150, "bounceOut")
            )
            
        return ft.Column(
            alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=25,
            controls=[
                ft.Text("PAGO Y FINALIZACIÓN", size=28, weight="bold", color=COLOR_PRIMARIO),
                ft.Text(f"TOTAL: ${total}", size=36, weight="bold", color=ft.Colors.GREEN_400),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER, spacing=20,
                    controls=[
                        _boton_pago("EFECTIVO", ft.Icons.MONEY, al_seleccionar_efectivo),
                        _boton_pago("TARJETA", ft.Icons.CREDIT_CARD, al_seleccionar_tarjeta),
                    ]
                ),
                ft.Container(height=10),
                BotonAnimado("GUARDAR VENTA", on_click=al_guardar, bgcolor=COLOR_PRIMARIO, width=350, height=60),
                ft.TextButton("CORREGIR DATOS", on_click=al_corregir, style=ft.ButtonStyle(color=ft.Colors.GREY_400))
            ]
        )