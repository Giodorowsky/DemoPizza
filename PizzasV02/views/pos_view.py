import flet as ft
from datos_negocio import (
    COLOR_FONDO, COLOR_ERROR, COLOR_EXITO, COLOR_SECUNDARIO, COLONIAS_CATALOGO,
    COLOR_PRIMARIO, COLOR_CONTRASTE, COLOR_TEXTO, COLOR_NUEVO, 
    ESTADO_PREPARANDO, SERVICIO_LOCAL, SERVICIO_DOMICILIO
)
from modelos.producto import Producto
from modelos.pedido import Pedido
from views.componentes.tarjetas import SelectorGrid
from views.componentes.botones import BotonAnimado
from views.vistas_factory import VistasFactory
from views.componentes.formularios import FormularioEntrega

# 🧹 IMPORTACIONES LIMPIAS: Eliminamos las vistas gráficas de la cabecera y 
# desacoplamos totalmente los precios del negocio utilizando el modelo Producto.

class PosView(ft.Container):
    def __init__(self, gestor_nav, db):
        super().__init__(expand=True, bgcolor=COLOR_FONDO) # OOP: Inicialización directa en el super
        self.db = db
        # Guardamos la referencia al gestor para acceder a la sesión centralizada
        self.gestor_nav = gestor_nav
        self.pedido_actual = Pedido()
        self.pizza_en_preparacion = None

        self.vistas_flujo = ft.Container(expand=True, padding=20, alignment=ft.Alignment.CENTER)
        self.content = self.vistas_flujo
        
        self.preparar_interfaz_inicial()

    def _mostrar_notificacion(self, mensaje, color):
        """Único canal de comunicación para alertas. Lazy Load de 'ayuditas'."""
        if self.gestor_nav:
            self.gestor_nav._notificar(mensaje, color)
    def preparar_interfaz_inicial(self):
        """Paso 1: Selección de Servicio."""
        opciones = [
            ["LOCAL", ft.Icons.RESTAURANT, SERVICIO_LOCAL, None, COLOR_NUEVO],
            ["DOMICILIO", ft.Icons.DELIVERY_DINING, SERVICIO_DOMICILIO, None, ft.Colors.RED_600]
        ]
        
        self.vistas_flujo.content = SelectorGrid(
            titulo="TIPO DE SERVICIO",
            opciones=opciones,
            al_seleccionar=self.registrar_servicio,
            columnas=1  
        )
        try: self.update()
        except: pass

    def registrar_servicio(self, valor):
        self.pedido_actual.tipo_servicio = valor
        self.mostrar_seleccion_tamano()

    def mostrar_seleccion_tamano(self):
        """Paso 2: Selección de Tamaños consumiendo el catálogo del modelo."""
        opciones = [
            ["CHICA", "chica.png", "CHICA"],
            ["MEDIANA", "mediana.png", "MEDIANA"], # Asumiendo que estos son nombres de productos en el catálogo
            ["GRANDE", "grande.png", "GRANDE"],    # y no solo etiquetas.
            ["FAMILIAR", "familiar.png", "FAMILIAR"] # Si son solo etiquetas, el modelo Producto debe manejarlas.
        ]
        
        self.vistas_flujo.content = VistasFactory.crear_vista_tamano(
            opciones=opciones,
            al_seleccionar=self.iniciar_preparacion_pizza_por_nombre,
            al_cancelar=lambda _: self.preparar_interfaz_inicial(),
            al_clic_especial=lambda _: self.mostrar_menu_promos() # <--- Activación del 5to botón rectangular
        )
        self.update()

    def mostrar_menu_promos(self):
        """Paso 2B: Selección de Promociones Especiales usando la fábrica."""
        opciones = [
            [nombre, ft.Icons.LOCAL_OFFER, nombre] 
            for nombre in ["BARRA", "MEGA"]
        ]        
        
        # Ahora usamos la vista estandarizada definida en VistasFactory
        self.vistas_flujo.content = VistasFactory.crear_vista_promociones(
            opciones=opciones,
            al_seleccionar=self.iniciar_preparacion_pizza_por_nombre,
            al_volver=lambda _: self.mostrar_seleccion_tamano()
        )
        self.update()

    def iniciar_preparacion_pizza_por_nombre(self, nombre):
        """Instancia el producto usando el método de fábrica del modelo."""
        try:
            self.pizza_en_preparacion = Producto.crear_desde_catalogo(nombre)
            self.mostrar_seleccion_sabores()
        except ValueError as e:
            self._mostrar_notificacion(str(e), COLOR_ERROR)

    def mostrar_seleccion_sabores(self):
        """Paso 3: Selección de Sabores con diseño de 2 columnas y scroll para Android."""
        titulo = f"SABORES ({len(self.pizza_en_preparacion.sabores_elegidos)}/{self.pizza_en_preparacion.limite_sabores})"
        
        # Obtenemos los sabores directamente desde la fuente de verdad (Producto)
        lista_sabores = Producto.obtener_sabores()
        opciones_sabores = [[sabor, "sabor.png", sabor] for sabor in lista_sabores]
        
        self.vistas_flujo.content = ft.Column(
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.ADAPTIVE, # Crucial para que los botones grandes no se corten
            controls=[
                SelectorGrid(
                    titulo=titulo, 
                    opciones=opciones_sabores, 
                    al_seleccionar=self.agregar_sabor, 
                    columnas=2
                ),
                ft.Container(height=20),
                BotonAnimado(
                    "CANCELAR PIZZA", 
                    on_click=lambda _: self.mostrar_seleccion_tamano(), 
                    bgcolor=COLOR_ERROR,
                    width=300
                )
            ]
        )
        self.update()
        
    def agregar_sabor(self, sabor):
        if self.pizza_en_preparacion.agregar_sabor(sabor):
            # Consultamos al modelo cuál debe ser el siguiente paso en el flujo
            siguiente = self.pizza_en_preparacion.obtener_siguiente_paso()
            
            if siguiente == "SELECCIONAR_SABORES":
                self.mostrar_seleccion_sabores()
            elif siguiente == "SELECCIONAR_REFRESCO":
                self.mostrar_seleccion_refresco()
            else:
                self.finalizar_pizza_individual()
        else:
            self._mostrar_notificacion("Ya alcanzó el límite de sabores para esta pizza", COLOR_ERROR)

    def mostrar_seleccion_refresco(self):
        """Paso 4: Selección de Refresco."""
        refrescos = ["COCA COLA", "SPRITE", "SIDRAL", "MANZANITA"]
        opciones_refrescos = [[r, ft.Icons.LOCAL_DRINK, r] for r in refrescos]
        self.vistas_flujo.content = SelectorGrid("REFRESCO GRATIS", opciones_refrescos, self.set_refresco, 2)
        self.update()

    def set_refresco(self, sabor_ref):
        self.pizza_en_preparacion.refresco_elegido = sabor_ref
        self.finalizar_pizza_individual()

    def finalizar_pizza_individual(self):
        """Paso 5: Resumen y opciones de continuación."""
        self.pedido_actual.productos.append(self.pizza_en_preparacion)
        self.pedido_actual.calcular_total()
        
        self.vistas_flujo.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20,
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=COLOR_EXITO, size=80),
                ft.Text("¡AGREGADO!", size=28, weight="bold"),
                ft.Text(f"Total Carrito: ${self.pedido_actual.total}", size=22, color=COLOR_TEXTO),
                ft.Container(height=10),
                BotonAnimado("AGREGAR OTRA PIZZA", on_click=lambda _: self.mostrar_seleccion_tamano(), bgcolor=COLOR_CONTRASTE, width=300),
                BotonAnimado("FINALIZAR Y PAGAR", on_click=lambda _: self.mostrar_formulario_cliente(), bgcolor=COLOR_PRIMARIO, width=300)
            ]
        )
        self.update()

    def mostrar_formulario_cliente(self):
        """Paso 6: Formulario de envío."""
        self.vistas_flujo.content = FormularioEntrega(
            es_domicilio=(self.pedido_actual.tipo_servicio == SERVICIO_DOMICILIO),
            al_finalizar=self.validar_y_pagar,
            colonias=COLONIAS_CATALOGO
        )
        self.update()

    def validar_y_pagar(self, formulario):
        datos = formulario.obtener_datos()
        if not datos["nombre"]:
            self._mostrar_notificacion("El nombre del cliente es obligatorio", COLOR_ERROR)
            return
            
        self.pedido_actual.cliente_nombre = datos["nombre"]
        self.pedido_actual.cliente_tel = datos["tel"]
        self.pedido_actual.cliente_colonia = datos["colonia"]
        self.pedido_actual.cliente_dir = datos["dir"]
        self.pedido_actual.cliente_ref = datos["ref"]
        self.mostrar_pantalla_pago()

    def mostrar_pantalla_pago(self):
        """Paso 7: Pantalla de Pago y Guardado final."""
        self.vistas_flujo.content = VistasFactory.crear_vista_pago(
            total=self.pedido_actual.total,
            al_seleccionar_efectivo=lambda e: self.seleccionar_metodo_pago("EFECTIVO"),
            al_seleccionar_tarjeta=lambda e: self.seleccionar_metodo_pago("TARJETA"),
            al_guardar=self.finalizar_venta_total,
            al_corregir=lambda e: self.mostrar_formulario_cliente(),
            metodo_actual=self.pedido_actual.metodo_pago
        )
        self.update()
        
    def seleccionar_metodo_pago(self, metodo):
        self.pedido_actual.metodo_pago = metodo
        self._mostrar_notificacion(f"Método: {metodo}", COLOR_NUEVO)
        self.mostrar_pantalla_pago() # Forzamos la actualización para que el estado se refleje internamente

    async def finalizar_venta_total(self, e):
        """Cierre de ticket, validando y registrando la venta."""
        # 1. Validación centralizada en el modelo
        es_valido, mensaje_error = self.pedido_actual.es_valido_para_guardar()
        if not es_valido:
            self._mostrar_notificacion(f"❌ {mensaje_error}", COLOR_ERROR)
            return
        
        # 2. Intentar guardado en la base de datos
        try:
            # Asignamos el estado inicial válido para la máquina de estados
            self.pedido_actual.estatus = ESTADO_PREPARANDO
            
            # Obtener sucursal (Manejo seguro de atributos)
            sucursal = "MATRIZ"
            if hasattr(self, 'page') and self.page and hasattr(self.page, 'session'):
                sucursal = self.page.session.store.get("sucursal_actual") or "MATRIZ"
            self.pedido_actual.sucursal = sucursal

            # Obtener usuario responsable
            nombre_usuario = "Desconocido"
            if self.gestor_nav and self.gestor_nav.usuario_actual:
                nombre_usuario = self.gestor_nav.usuario_actual.get("nombre", "Desconocido")

            # Guardar pedido en base de datos
            guardado_online = await self.db.guardar_pedido(self.pedido_actual, usuario_nombre=nombre_usuario)
            
            # Reiniciar pedido e interfaz
            self.pedido_actual = Pedido() 
            self.preparar_interfaz_inicial()

            if guardado_online:
                self._mostrar_notificacion("✅ ¡VENTA REGISTRADA CORRECTAMENTE!", COLOR_EXITO)
            else:
                self._mostrar_notificacion("SIN CONEXIÓN. Pedido guardado localmente.", COLOR_NUEVO)
            
        except Exception as ex:
            print(f"Error detallado al guardar venta: {ex}")
            self._mostrar_notificacion(f"❌ ERROR AL GUARDAR: {str(ex)}", COLOR_ERROR)