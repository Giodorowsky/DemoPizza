import json
import os
import asyncio
from pathlib import Path
import flet as ft


class GestorConfiguracion:
    """
    Clase centralizada para cargar y gestionar el archivo de configuración (config.json)[cite: 1].
    Es compatible tanto con el entorno de desarrollo local como con Android y producción[cite: 1].
    """
    def __init__(self):
        self.config_data = {}

    @classmethod
    def from_dict(cls, data):
        """Crea una instancia de GestorConfiguracion a partir de un diccionario."""
        inst = cls()
        inst.config_data = data or {}
        return inst

    async def cargar_configuracion(self):
        """
        Carga la configuración de forma asíncrona para no bloquear el hilo principal[cite: 1].
        """
        config_filename = "config.json"
        try:
            default_assets_dir = Path(__file__).parent.parent.parent / "assets"
            assets_dir = Path(os.environ.get("FLET_ASSETS_DIR", str(default_assets_dir))).resolve()
            config_path = assets_dir / config_filename

            if not config_path.exists():
                config_path = Path("assets") / config_filename

            loop = asyncio.get_running_loop()
            content = await loop.run_in_executor(None, config_path.read_text, "utf-8")
            self.config_data = json.loads(content)

            if "database_url" not in self.config_data:
                raise KeyError("La clave 'database_url' es obligatoria en config.json.")

            print(f"✅ Configuración cargada exitosamente desde: {config_path}")
            return True

        except FileNotFoundError:
            print(f"❌ ERROR CRÍTICO: No se pudo encontrar '{config_filename}' en la carpeta 'assets'.")
            raise
        except json.JSONDecodeError:
            print(f"❌ ERROR CRÍTICO: El archivo '{config_filename}' tiene un formato JSON inválido.")
            raise
        except KeyError as e:
            print(f"❌ ERROR CRÍTICO DE CONFIGURACIÓN: {e}")
            raise
        except Exception as e:
            print(f"❌ ERROR INESPERADO al cargar la configuración: {e}")
            raise

    def obtener(self, clave, default=None):
        """Obtiene un valor de la configuración."""
        return self.config_data.get(clave, default)


def notificar_seguro(page: ft.Page, mensaje: str, color: str):
    """Lanzador de notificaciones a prueba de fallos usando page.overlay."""
    if not page:
        return
        
    try:
        snack = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.Colors.WHITE, weight="bold"),
            bgcolor=color,
            duration=3000
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
    except Exception as e:
        print(f"Error al notificar: {e}")