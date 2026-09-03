import flet as ft
from app_builder import AppBuilder

async def main(page: ft.Page):
   
    # 1. Muestra una vista de carga INMEDIATA. Esto es lo primero que ve el usuario.
    page.title = "Cargando..."
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(ft.ProgressRing(), ft.Text("Iniciando aplicación..."))
    page.update()

    # 2. Se crea una instancia del constructor y se le pasa la página.
    builder = AppBuilder(page)
    
    # 3. Se ejecuta la construcción. La función 'main' ahora ESPERA a que todo termine.
    #    Esto elimina la condición de carrera y asegura un arranque estable.
    await builder.construir_app()

if __name__ == "__main__":
    # Flet maneja la ejecución asíncrona nativamente al pasarle una función 'async def main'
    try:
        ft.run(main)
    except (KeyboardInterrupt, SystemExit):
        pass