import flet as ft
import hashlib
try:
    import bcrypt
except Exception:
    bcrypt = None
from modelos.usuario import Usuario 
from datos_negocio import COLOR_PRIMARIO, COLOR_FONDO, COLOR_TEXTO, COLOR_ERROR

class LoginView(ft.Container):
    def __init__(self, al_ingresar, config):
        super().__init__()
        self.al_ingresar = al_ingresar
        self.expand = True
        self.alignment = ft.Alignment.CENTER
        self.config = config
        self.bgcolor = COLOR_FONDO 

        self.campo_nip = ft.TextField(
            label="PIN DE ACCESO", 
            password=True,
            can_reveal_password=True,
            max_length=4,
            width=280,
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=COLOR_PRIMARIO,
            focused_border_color=COLOR_PRIMARIO,
            color=COLOR_TEXTO,
            on_submit=self.validar_acceso
        )

        nombre_negocio = self.config.obtener("nombre_negocio") if self.config else "MI NEGOCIO"
        
        self.content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Image(src="mi_logitos.png", width=300, height=300, fit="contain"),
                ft.Container(height=10),
                ft.Text(value=nombre_negocio.upper(), size=32, weight="bold", color=ft.Colors.WHITE),
                ft.Text(value="Ingrese su PIN para continuar", color=ft.Colors.GREEN_700),
                ft.Container(height=30),
                self.campo_nip,
                ft.Container(height=20),
                ft.Button(
                    "ENTRAR",
                    icon=ft.Icons.LOGIN_ROUNDED,
                    style=ft.ButtonStyle(
                        color=COLOR_TEXTO,
                        bgcolor=COLOR_PRIMARIO,
                        padding=20
                    ),
                    on_click=self.validar_acceso,
                    width=280
                )
            ]
        )

    async def validar_acceso(self, e):
        nip = self.campo_nip.value
        config = self.config
        if not config:
            self.campo_nip.error_text = "ERROR DE CONFIGURACIÓN"
            self.campo_nip.error_style = ft.TextStyle(color=COLOR_ERROR)
            self.update()
            return

        seguridad = config.obtener("seguridad")
        hash_nip_ingresado = hashlib.sha256(nip.encode('utf-8')).hexdigest()
        pines_por_sucursal_config = seguridad.get("pines_por_sucursal", {})

        for sucursal_nombre, pines_config in pines_por_sucursal_config.items():
            sucursal_dispositivo = sucursal_nombre.strip().upper().replace(" ", "")
            pines_sucursal = pines_config or {}

            # Validar Cocina
            hash_cocina_guardado = pines_sucursal.get("pin_cocina", "")
            if hash_cocina_guardado and hash_nip_ingresado == hash_cocina_guardado.strip():
                sesion = Usuario(nombre=f"Cocina {sucursal_dispositivo}", rol="COCINA", esta_activo=True)
                self.campo_nip.value = ""
                await self.al_ingresar(sesion, sucursal=sucursal_dispositivo)
                return

            # Validar Empleados
            hashes_empleados_guardados = pines_sucursal.get("pines_empleados", [])
            for idx, hash_empleado_guardado in enumerate(hashes_empleados_guardados, start=1):
                if hash_empleado_guardado and hash_nip_ingresado == hash_empleado_guardado.strip():
                    sesion = Usuario(nombre=f"Empleado {idx}", rol="CAJERA", esta_activo=True)
                    self.campo_nip.value = ""
                    await self.al_ingresar(sesion, sucursal=sucursal_dispositivo)
                    return
            
            # Validar Repartidores
            hashes_repartidores_guardados = pines_sucursal.get("pines_repartidores", [])
            for idx, hash_repartidor_guardado in enumerate(hashes_repartidores_guardados, start=1):
                if hash_repartidor_guardado and hash_nip_ingresado == hash_repartidor_guardado.strip():
                    sesion = Usuario(nombre=f"Repartidor {idx}", rol="REPARTIDOR", esta_activo=True)
                    self.campo_nip.value = ""
                    await self.al_ingresar(sesion, sucursal=sucursal_dispositivo)
                    return

        # Validar Dueño
        hash_dueno_guardado = seguridad.get("pin_dueno", "")
        if hash_dueno_guardado and hash_nip_ingresado == hash_dueno_guardado.strip():
            sesion = Usuario(nombre="Administrador", rol="DUEÑO", esta_activo=True)
            self.campo_nip.value = ""
            await self.al_ingresar(sesion)
            return

        self.campo_nip.error_text = "PIN INCORRECTO O NO RECONOCIDO"
        self.campo_nip.error_style = ft.TextStyle(color=COLOR_ERROR)
        self.campo_nip.value = ""
        self.update()