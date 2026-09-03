import flet as ft

class KpiCard(ft.Container):
    def __init__(
        self, 
        titulo: str, 
        valor: str, 
        icono: str, 
        color_icono: str, 
        col_size: int = 6, 
        estilo_global: bool = False
    ):
        bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.WHITE) if estilo_global else "#1E1E1E"
        font_family = "monospace" if estilo_global else None
        
        super().__init__(
            col={"xs": col_size, "sm": 4},
            bgcolor=bgcolor,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.1, color_icono)),
            padding=20 if estilo_global else 15,
            border_radius=15,
            shadow=ft.BoxShadow(
                blur_radius=15 if estilo_global else 5, 
                color=ft.Colors.with_opacity(0.1, color_icono if estilo_global else "black")
            ),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Icon(icono, color=color_icono, size=32 if estilo_global else 28),
                    ft.Text(
                        valor, 
                        size=24 if estilo_global else 20, 
                        weight="w900" if estilo_global else "bold", 
                        color=ft.Colors.WHITE, 
                        font_family=font_family
                    ),
                    ft.Text(
                        titulo, 
                        size=11 if estilo_global else 10, 
                        color=ft.Colors.with_opacity(0.7, color_icono) if estilo_global else ft.Colors.GREY_500, 
                        weight="bold", 
                        font_family=font_family
                    ),
                ], 
                spacing=8 if estilo_global else 5
            )
        )