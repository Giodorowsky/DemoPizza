"""
Módulo de Gestión de Sesiones (SessionManager)
Maneja el almacenamiento y recuperación de datos de la sesión del usuario
a través del almacenamiento de sesión de Flet (page.session.store).
"""

from dataclasses import is_dataclass, asdict
import flet as ft


class SessionManager:
    """Administra el estado de la sesión activa del usuario y sucursal."""

    def __init__(self, page: ft.Page):
        self.page = page

    @property
    def usuario_actual(self) -> dict | None:
        """Obtiene el diccionario del usuario almacenado en la sesión activa."""
        return self.page.session.store.get("usuario_actual")

    @property
    def sucursal_actual(self) -> str | None:
        """Obtiene la sucursal activa en la sesión."""
        return self.page.session.store.get("sucursal_actual")

    def iniciar_sesion(self, sesion, sucursal: str = None) -> None:
        """
        Guarda los datos del usuario autenticado en la sesión.
        Soporta objetos Dataclass, clases convencionales o diccionarios.
        """
        if is_dataclass(sesion):
            usuario_dict = asdict(sesion)
        elif hasattr(sesion, "__dict__"):
            usuario_dict = vars(sesion)
        elif isinstance(sesion, dict):
            usuario_dict = sesion.copy()
        else:
            # Fallback manual en caso de ser un objeto simple o tuple
            usuario_dict = {
                "id": getattr(sesion, "id", None),
                "nombre": getattr(sesion, "nombre", ""),
                "rol": getattr(sesion, "rol", ""),
                "esta_activo": getattr(sesion, "esta_activo", True),
            }

        self.page.session.store.set("usuario_actual", usuario_dict)

        if sucursal is not None:
            self.establecer_sucursal(sucursal)

    def establecer_sucursal(self, sucursal: str) -> None:
        """Establece o actualiza la sucursal seleccionada en el estado global."""
        self.page.session.store.set("sucursal_actual", str(sucursal))

    def cerrar_sesion(self) -> None:
        """Limpia completamente el almacenamiento de sesión activa."""
        self.page.session.store.clear()