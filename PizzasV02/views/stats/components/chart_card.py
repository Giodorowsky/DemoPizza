import flet as ft

def crear_tarjeta_grafica(titulo: str, subtitulo: str, icono: str, color_accent: str, grafica_widget: ft.Control, col_config: dict) -> ft.Container:
    """Genera un contenedor estilizado para envolver cualquier gráfica."""
    return ft.Container(
        col=col_config,
        bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.2, color_accent)),
        padding=25,
        border_radius=15,
        shadow=ft.BoxShadow(blur_radius=25, color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK), offset=ft.Offset(0, 0)),
        content=ft.Column([
            ft.Row([
                ft.Icon(icono, color=color_accent, size=24),
                ft.Text(titulo, size=18, weight="w900", color=ft.Colors.WHITE, font_family="monospace"),
            ]),
            ft.Text(subtitulo, size=11, color=color_accent, font_family="monospace", weight="bold"),
            ft.Container(
                content=grafica_widget, 
                margin=ft.Margin.only(top=20, bottom=5),
                alignment=ft.Alignment.CENTER
            ),
        ])
    )