import flet as ft
import traceback
from datos_negocio import COLOR_ERROR, COLOR_TEXTO
from core.router import GestorNavegacion


class AppBuilder:
    """
    Clase dedicada a construir y configurar la aplicación Flet de forma secuencial y segura.
    Esto resuelve el problema de la condición de carrera al asegurar que la inicialización
    se complete ANTES de que la función 'main' termine.
    """
    def __init__(self, page: ft.Page):
        self.page = page
        self.db = None
        self.config = None

    def _mostrar_error_en_pantalla(self, error_msg, etapa, traza_completa):
        """Muestra un error fatal de arranque directamente en la pantalla del móvil."""
        self.page.clean()
        self.page.add(
            ft.ListView([
                ft.Text("Error de Arranque", color=COLOR_ERROR, size=24, weight="bold"),
                ft.Text(f"Etapa: {etapa}", color=COLOR_TEXTO, size=16),
                ft.Text(error_msg, color=ft.Colors.YELLOW, size=14, selectable=True),
                ft.Divider(),
                ft.Text("Rastro completo:", color=ft.Colors.GREY_500),
                ft.Text(traza_completa, color=ft.Colors.GREY_600, size=10, selectable=True),
            ], spacing=10)
        )
        self.page.update()

    async def _cargar_configuracion(self):
        """ETAPA 1: Cargar configuración."""
        from views.componentes.ayuditas import GestorConfiguracion
        print("-> Iniciando gestor de configuración...")
        self.config = GestorConfiguracion()
        await self.config.cargar_configuracion()
        # Guardar la instancia, no solo el dict, para mantener la API uniforme
        self.page.session.store.set("config", self.config)
        print("-> Configuración cargada y guardada en sesión (GestorConfiguracion).")

    async def _conectar_base_datos(self):
        from database.database_manager import DatabaseManager
        
        print("-> Inicializando DatabaseManager...")
        self.db = DatabaseManager(self.config)
        await self.db.inicializar_db()
        print("-> Pool de conexiones a la base de datos creado.")

    async def _iniciar_navegacion(self):
        """ETAPA 3: Arranque del Gestor de Navegación."""
        
        self.page.clean() # Limpia la vista de carga ahora que todo está listo
        self.page.title = self.config.obtener("nombre_negocio") or "MI NEGOCIO"
        self.page.padding = 0
        self.page.spacing = 0
        
        print("-> Arrancando gestor de navegación...")
        gestor = GestorNavegacion(self.page, self.db)
        await gestor.iniciar_app() # Esto renderizará la vista de login
        print("-> Aplicación iniciada y vista de login renderizada.")

    async def construir_app(self):
        """
        Ejecuta todas las etapas de inicialización en orden.
        Si alguna falla, muestra el error y detiene el proceso.
        """
        try:
            await self._cargar_configuracion()
            await self._conectar_base_datos()
            await self._iniciar_navegacion()
        except Exception as e:
            etapa = "Desconocida"
            if not self.config: etapa = "Carga de config.json"
            elif not self.db: etapa = "Conexión a Base de Datos"
            else: etapa = "Arranque del Gestor de Navegación"
            self._mostrar_error_en_pantalla(str(e), etapa, traceback.format_exc())