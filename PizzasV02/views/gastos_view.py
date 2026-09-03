import flet as ft
from datos_negocio import COLOR_FONDO, COLOR_PRIMARIO, COLOR_TEXTO, COLOR_CONTRASTE, COLOR_EXITO, COLOR_ERROR
from views.componentes.botones import BotonAnimado
from views.componentes.ayuditas import notificar_seguro
from modelos.gasto import Gasto

class GastosView(ft.Container):
    def __init__(self, db, cajero_nombre):
        super().__init__()
        self.db = db
        self.cajero = cajero_nombre
        self.expand = True
        self.bgcolor = COLOR_FONDO
        self.padding = 30 # Márgenes amplios para evitar toques accidentales en móviles

        # Campos de entrada de texto optimizados
        self.input_desc = ft.TextField(
            label="Descripción del Gasto (Ej. Insumos)", 
            border_color=COLOR_PRIMARIO, 
            color=COLOR_TEXTO
        )
        self.input_monto = ft.TextField(
            label="Monto $", 
            keyboard_type=ft.KeyboardType.NUMBER, # Fuerza el teclado numérico en el celular
            prefix=ft.Text("$", color=COLOR_PRIMARIO), 
            border_color=COLOR_PRIMARIO, 
            color=COLOR_TEXTO
        )

        self.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=25,
            controls=[
                ft.Icon(ft.Icons.ATTACH_MONEY, size=80, color=COLOR_PRIMARIO),
                ft.Text("REGISTRO DE GASTOS", size=28, weight="bold", color=COLOR_PRIMARIO),
                ft.Text(f"Operador: {self.cajero}", color=ft.Colors.GREY_400),
                
                # Formulario
                self.input_desc,
                self.input_monto,
                ft.Container(height=10), # Separador visual
                
                # Botón de acción asíncrono
                BotonAnimado("GUARDAR GASTO", on_click=self.procesar_gasto, bgcolor=COLOR_EXITO, width=300)
            ]
        )

    async def procesar_gasto(self, e):
        """Valida, guarda en base de datos y lanza notificación segura."""
        # 1. Validación de campos obligatorios
        if not self.input_desc.value or not self.input_monto.value:
            self.input_desc.error_text = "Requerido"
            self.input_monto.error_text = "Requerido"
            self.update()
            return

        try:
            # Obtenemos la sucursal activa desde la sesión de la página
            sucursal_actual = "MATRIZ" # Valor por defecto seguro
            if self.page and self.page.session and self.page.session.store:
                sucursal_actual = self.page.session.store.get("sucursal_actual") or "MATRIZ"

            # 2. Creación del objeto Gasto y conversión de texto a número (float)
            nuevo_gasto = Gasto(
                descripcion=self.input_desc.value.upper(),
                monto=float(self.input_monto.value),
                cajero=self.cajero,
                sucursal=sucursal_actual # <-- Pasamos la sucursal correcta
            )
            
            # 3. Guardado en la base de datos
            await self.db.guardar_gasto(nuevo_gasto)

            # 4. Limpieza de interfaz ANTES de notificar
            self.input_desc.value = ""
            self.input_monto.value = ""
            self.input_desc.error_text = None
            self.input_monto.error_text = None
            self.update()

            # 5. Notificación Visual Segura
            if self.page:
                notificar_seguro(self.page, f"✅ GASTO REGISTRADO: ${nuevo_gasto.monto:.2f}", COLOR_EXITO)

        except ValueError:
            # Si el usuario intenta guardar letras en el campo de monto
            self.input_monto.error_text = "Ingrese un número válido"
            self.update()
        except Exception as ex:
            # Si hay un error con la base de datos
            print(f"Error al guardar gasto: {ex}")
            if self.page:
                notificar_seguro(self.page, f"ERROR AL GUARDAR: {str(ex)}", COLOR_ERROR)