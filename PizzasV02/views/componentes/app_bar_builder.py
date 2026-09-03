import flet as ft
from datos_negocio import COLOR_TEXTO, COLOR_PRIMARIO, SUCURSALES_CATALOGO
from views.componentes.botones import BarraNavegacion

def crear_app_bar_personalizada(page: ft.Page, session_mgr, titulo_principal: str, on_cambiar_sucursal) -> BarraNavegacion:
    usuario = session_mgr.usuario_actual or {}
    nombre_usuario = usuario.get("nombre", "Usuario")
    es_dueno = usuario.get("rol") == "DUEÑO"
    sucursal_actual = session_mgr.sucursal_actual

    titulo_appbar = ft.Text(f"{titulo_principal} | 👤 {nombre_usuario}", color=COLOR_TEXTO, size=14)

    if es_dueno:
        menu_items = [
            ft.PopupMenuItem(
                content=ft.Text(suc),
                on_click=lambda e, s=suc: page.run_task(on_cambiar_sucursal, s)
            ) for suc in SUCURSALES_CATALOGO
        ]
        control_sucursal = ft.PopupMenuButton(
            content=ft.Row([
                ft.Text("•", color=COLOR_TEXTO, size=14),
                ft.Text(f"📍 {sucursal_actual}", color=COLOR_PRIMARIO, size=14, weight="bold"),
                ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=COLOR_PRIMARIO)
            ]),
            items=menu_items
        )
        titulo_completo = ft.Row([titulo_appbar, control_sucursal], spacing=10)
    else:
        titulo_completo = ft.Row([titulo_appbar, ft.Text(f"• 📍 {sucursal_actual}", color=COLOR_TEXTO, size=14)], spacing=10)

    return BarraNavegacion(titulo_completo, page)