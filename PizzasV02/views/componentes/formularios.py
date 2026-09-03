import flet as ft
# 1. Importamos las constantes correctamente
from datos_negocio import COLOR_PRIMARIO, COLOR_EXITO, COLOR_CONTRASTE
# 2. Importamos los nuevos módulos separados
from modelos.gasto import Gasto
from views.componentes.botones import BotonAnimado
from views.componentes.ayuditas import notificar_seguro

class FormularioEntrega(ft.Column):
    """Componente POO blindado contra el error __getattr__."""
    def __init__(self, es_domicilio, al_finalizar, colonias=None): # ✅ 1. Agregamos colonias aquí
        super().__init__(spacing=15, horizontal_alignment="center")
        
        self.controls.append(ft.Text("DATOS DEL CLIENTE", size=24, weight="bold", color=COLOR_PRIMARIO))
        
        self.nombre = ft.TextField(label="Nombre del Cliente", border_color=COLOR_PRIMARIO, width=350)
        self.tel = ft.TextField(label="Teléfono", keyboard_type="phone", width=350)
        self.controls.extend([self.nombre, self.tel])

        # BLINDAJE: Definimos variables al inicio
        self.dir = None
        self.ref = None
        self.colonia = None # ✅ 2. Inicializamos la variable para la colonia

        if es_domicilio:
            # ✅ 3. Creamos un Dropdown si hay colonias, o un TextField normal si no las hay
            if colonias:
                self.colonia = ft.Dropdown(
                    label="Colonia",
                    options=[ft.dropdown.Option(c) for c in colonias],
                    width=350
                )
            else:
                self.colonia = ft.TextField(label="Colonia", width=350)

            self.dir = ft.TextField(label="Dirección de Entrega", multiline=True, width=350)
            self.ref = ft.TextField(label="Referencias (Casa, color, etc.)", multiline=True, width=350)
            self.controls.extend([self.colonia, self.dir, self.ref])

        self.controls.append(
            BotonAnimado("IR AL PAGO", on_click=lambda _: al_finalizar(self), bgcolor=COLOR_EXITO, width=350)
        )

    def obtener_datos(self):
        nombre_cliente = self.nombre.value or ""
        telefono_cliente = self.tel.value or ""
        
        direccion_cliente = "LOCAL"
        referencia_cliente = ""
        colonia_cliente = "" # ✅ 4. Variable temporal para la colonia

        if self.dir is not None:
            direccion_cliente = self.dir.value or ""
            
        if self.ref is not None:
            referencia_cliente = self.ref.value or ""
            
        if self.colonia is not None:
            colonia_cliente = self.colonia.value or ""

        return {
            "nombre": nombre_cliente,
            "tel": telefono_cliente,
            "dir": direccion_cliente,
            "ref": referencia_cliente,
            "colonia": colonia_cliente 
        }

class ModalGasto(ft.AlertDialog):
    """Componente POO auto-gestionado y blindado."""
    def __init__(self, page, db, cajero_nombre):
        super().__init__()
        self.page = page
        self.db = db
        self.cajero = cajero_nombre
        
        self.bgcolor = COLOR_CONTRASTE
        self.title = ft.Text("REGISTRAR GASTO", color=COLOR_PRIMARIO, weight="bold")
        
        self.input_desc = ft.TextField(label="Descripción (Ej. Compra de gas)", border_color=COLOR_PRIMARIO)
        self.input_monto = ft.TextField(label="Monto $", keyboard_type=ft.KeyboardType.NUMBER, prefix_text="$")
        
        self.content = ft.Column(
            [self.input_desc, self.input_monto],
            tight=True,
            spacing=20
        )
        
        self.actions = [
            # 3. Usamos cierre seguro
            ft.TextButton("CANCELAR", on_click=lambda _: self._cerrar_modal()),
            BotonAnimado("GUARDAR GASTO", on_click=self.procesar_gasto, bgcolor=COLOR_EXITO, width=200)
        ]

    def _cerrar_modal(self):
        self.open = False
        self.page.update()

    async def procesar_gasto(self, e):
        if not self.input_desc.value or not self.input_monto.value:
            self.input_desc.error_text = "Campo requerido"
            self.update()
            return
            
        try:
            # Obtenemos la sucursal activa desde la sesión de la página
            sucursal_actual = "MATRIZ" # Valor por defecto seguro
            if self.page and self.page.session and self.page.session.store:
                sucursal_actual = self.page.session.store.get("sucursal_actual") or "MATRIZ"

            nuevo_gasto = Gasto(
                descripcion=self.input_desc.value.upper(),
                monto=float(self.input_monto.value),
                cajero=self.cajero,
                sucursal=sucursal_actual # <-- Pasamos la sucursal correcta
            )
            
            await self.db.guardar_gasto(nuevo_gasto)
            
            # 4. Eliminamos el '.store' y llamamos al notificador global
            self._cerrar_modal()
            notificar_seguro(self.page, f"✅ Gasto registrado: ${nuevo_gasto.monto:.2f}", COLOR_EXITO)
            
        except ValueError:
            self.input_monto.error_text = "Monto inválido"
            self.update()