import flet as ft
from datos_negocio import COLOR_PRIMARIO, COLOR_TEXTO, COLOR_EXITO, ESTADO_LIQUIDADO

class SelectorGrid(ft.Column):
    """Componente que muestra Imagenes, Nombres y Precios."""
    def __init__(self, titulo, opciones, al_seleccionar, columnas=2):
        super().__init__()
        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 20
        self.expand = True # Permite desplazamiento fluido
        
        self.controls.append(
            ft.Text(titulo.upper(), size=24, weight="bold", color=COLOR_PRIMARIO)
        )

        # ¡EL FIX MÁGICO DE ARQUITECTURA!
        # Si se pide 1 columna (LOCAL / DOMICILIO), usamos un contenedor nativo vertical.
        # Si se piden varias (SABORES), usamos la cuadrícula sin que max_extent interfiera.
        if columnas == 1:
            self.grid = ft.Column(
                spacing=25, 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            )
        else:
            self.grid = ft.GridView(
                runs_count=columnas,
                spacing=15,
                run_spacing=15,
                expand=True
            )

        for opt in opciones:
            nombre = opt[0]
            visual = opt[1]
            valor = opt[2]
            precio = opt[3] if len(opt) > 3 else None
            color_fondo = opt[4] if len(opt) > 4 else "#1E1E1E"

            # Detectamos si es imagen o un icono
            if isinstance(visual, str) and (visual.endswith(".png") or visual.endswith(".jpg")):
                elemento_visual = ft.Image(src=visual, width=100, height=100, fit="contain")
            else:
                elemento_visual = ft.Icon(visual, size=50, color=COLOR_TEXTO)

            btn = ft.Container(
                # Si es 1 columna, hacemos el botón grande y vistoso (300px)
                width=250 if columnas == 1 else 180, 
                height=250 if columnas == 1 else 180,
                content=ft.Column([
                    elemento_visual,
                    ft.Text(nombre, weight="bold", size=18, color=ft.Colors.WHITE),
                    # Solo pintamos el precio si realmente existe
                    ft.Text(f"${precio}", size=16, color=COLOR_EXITO, weight="w500", visible=bool(precio))
                ], alignment="center", horizontal_alignment="center", spacing=5),
                bgcolor=color_fondo,
                border_radius=25,
                padding=15,
                on_click=lambda _, v=valor: al_seleccionar(v),
                animate_scale=ft.Animation(200, "decelerate"),
            )
            self.grid.controls.append(btn)

        self.controls.append(self.grid)
#----------------------------------
class TarjetaPedidoHistorial(ft.Container):
    """Componente POO: Tarjeta oscura con botón de estatus dinámico."""
    def __init__(self, pedido, al_hacer_click, colores_config):
        super().__init__()
        self.pedido = pedido
        colores = colores_config if colores_config is not None else {}
        # FONDO SIEMPRE OSCURO: Usamos el color de contraste del JSON o un gris muy oscuro
        self.bgcolor = colores.get("color_contraste", "#1E1E1E")
        self.padding = 20
        self.border_radius = 15
        self.ink = True
        self.on_click = lambda e: al_hacer_click(self.pedido, e)
        self.content = self._crear_diseno()

    
    def _crear_diseno(self):
        estatus = self.pedido.estatus # Asumiendo que self.pedido siempre es un objeto Pedido con atributo 'estatus'
        
        # Definición de colores según el estatus
        color_tag = ft.Colors.GREY_800
        color_texto_tag = ft.Colors.WHITE

        if estatus == "EN COCINA":
            color_tag = ft.Colors.ORANGE_800
        elif estatus == "POR ENTREGAR":
            color_tag = ft.Colors.YELLOW_400
            color_texto_tag = ft.Colors.BLACK
        elif estatus == "EN CAMINO":
            color_tag = ft.Colors.BLUE_600
        elif estatus == "ENTREGADO":
            color_tag = ft.Colors.GREEN_700
        elif estatus == ESTADO_LIQUIDADO:
            color_tag = COLOR_EXITO
            color_texto_tag = ft.Colors.WHITE

        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column([
                    ft.Text(f"TICKET #{self.pedido.id}", weight="bold", size=20, color=ft.Colors.WHITE),
                    ft.Text(f"{self.pedido.tipo_servicio} • ${self.pedido.total:.2f}", color=ft.Colors.GREY_400, size=14),
                ], spacing=3),
                
                # Botón de estatus con estilo de "Píldora"
                ft.Container(
                    bgcolor=color_tag,
                    padding=ft.Padding.symmetric(horizontal=15, vertical=5),
                    border_radius=20, # Bordes más redondeados para "darle vida"
                    content=ft.Text(
                        estatus.upper(), 
                        size=11, 
                        weight="bold", 
                        color=color_texto_tag,
                    
                    ),
                    shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.3, "black"))
                )
            ]
        )
