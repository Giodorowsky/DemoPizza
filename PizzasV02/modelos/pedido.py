from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import json
from datos_negocio import ESTADO_RECIBIDO, ESTADO_LISTO, ESTADO_EN_CAMINO, ESTADO_ENTREGADO, ESTADO_LIQUIDADO, SERVICIO_DOMICILIO
from datos_negocio import DB_COLUMNS

@dataclass
class Pedido:
    # Datos de Identificación
    id: str = None
    fecha: datetime = field(default_factory=datetime.now)
    
    # Datos del Cliente 
    cliente_nombre: str = ""
    cliente_tel: str = ""
    cliente_dir: str = ""
    cliente_colonia: str = "" # NUEVO: Para la colonia
    cliente_ref: str = ""
    
    # Lógica de Venta
    tipo_servicio: str = "" # LOCAL o DOMICILIO
    productos: List = field(default_factory=list)
    total: float = 0.0
    metodo_pago: str = ""
    estatus: str = ESTADO_RECIBIDO
    repartidor: str = ""
    sucursal: str = "" # NUEVO: Para identificar la sucursal
    corte: int = 0

    @classmethod
    def desde_base_datos(cls, fila_db):
        """
        Crea una instancia de Pedido a partir de una fila de la BD de forma resiliente,
        evitando errores por discrepancias entre DB_COLUMNS y los nombres físicos de Supabase,
        y deserializando correctamente los productos y el tipo de servicio.
        """
        def obtener(*claves, por_defecto=""):
            for c in claves:
                if c and c in fila_db and fila_db[c] is not None:
                    return fila_db[c]
            return por_defecto

        # Deserializar productos desde el JSON de la base de datos de manera segura
        detalle_bruto = obtener(DB_COLUMNS.get("DETALLE"), "detalle", por_defecto="[]")
        productos_lista = []
        if isinstance(detalle_bruto, str):
            try:
                productos_lista = json.loads(detalle_bruto)
            except Exception:
                productos_lista = []
        elif isinstance(detalle_bruto, list):
            productos_lista = detalle_bruto

        return cls(
            id=obtener("id", "id_ticket", DB_COLUMNS.get("ID"), por_defecto="0"),
            # CORRECCIÓN: asyncpg devuelve objetos datetime, no es necesaria la conversión manual.
            # Si fuera una cadena, se usaría fromisoformat para mayor robustez.
            fecha=obtener("fecha_hora", "fecha", DB_COLUMNS.get("FECHA")) or datetime.now(),
            cliente_nombre=obtener(DB_COLUMNS.get("CLIENTE"), "cliente"),
            cliente_tel=obtener(DB_COLUMNS.get("TEL"), "tel"),
            cliente_dir=obtener(DB_COLUMNS.get("DIR"), "dir"),
            cliente_colonia=obtener("colonia", DB_COLUMNS.get("COLONIA")), # CORREGIDO
            cliente_ref=obtener("referencias", DB_COLUMNS.get("REF")), # CORREGIDO
            total=float(obtener("monto_total", "total", DB_COLUMNS.get("TOTAL"), por_defecto=0.0)),
            estatus=obtener(DB_COLUMNS.get("ESTATUS"), "estatus", por_defecto=ESTADO_RECIBIDO),
            metodo_pago=obtener(DB_COLUMNS.get("METODO"), "metodo"),
            tipo_servicio=obtener(DB_COLUMNS.get("SERVICIO"), "tipo_servicio", "tipo"),
            repartidor=obtener(DB_COLUMNS.get("REPARTIDOR"), "repartidor"),
            sucursal=obtener(DB_COLUMNS.get("SUCURSAL"), "sucursal"), # NUEVO
            corte=int(obtener("corte", por_defecto=0)),
            productos=productos_lista
        )

    # --- LÓGICA DE NEGOCIO ---
    def calcular_total(self):
        """Calcula el total sumando el precio de cada producto (soporta objetos y diccionarios)."""
        total_acumulado = 0.0
        for p in self.productos:
            if isinstance(p, dict):
                total_acumulado += float(p.get("precio", 0.0))
            elif hasattr(p, 'precio'):
                total_acumulado += float(p.precio)
        self.total = total_acumulado
        return self.total   
    
    def esta_pendiente_de_liquidacion(self) -> bool:
        """
        Retorna True si el pedido fue en efectivo y aún no ha sido marcado como liquidado.
        Esto aplica tanto para pedidos a domicilio entregados como para pedidos locales entregados.
        """
        es_efectivo = self.metodo_pago == "EFECTIVO"
        esta_entregado_no_liquidado = self.estatus == ESTADO_ENTREGADO
        return es_efectivo and esta_entregado_no_liquidado

    def esta_liquidado(self) -> bool:
        """
        Retorna True si el pedido tiene el estatus de LIQUIDADO.
        """
        return self.estatus == ESTADO_LIQUIDADO


    def es_valido_para_guardar(self) -> (bool):
        """
        Valida que el pedido tenga los datos mínimos para ser guardado.
        Retorna una tupla (es_valido, mensaje_de_error).
        """
        if not self.productos:
            return False, "El carrito está vacío. Agrega al menos un producto."
        if not self.cliente_nombre or not self.cliente_nombre.strip():
            return False, "El nombre del cliente es obligatorio."
        if not self.metodo_pago or not self.metodo_pago.strip():
            return False, "Selecciona un método de pago (Efectivo o Tarjeta)."
        
        return True, ""

    def obtener_lineas_detalle_producto(self) -> List[str]:
        """Genera una lista de strings formateados para mostrar en la UI."""
        lineas = []
        for prod in self.productos:
            if isinstance(prod, dict):
                nombre_prod = prod.get('nombre', prod.get('titulo', 'Producto'))
                sabores_lista = prod.get('sabores', prod.get('sabores_elegidos', []))
            else: # Si es un objeto
                nombre_prod = getattr(prod, 'nombre', getattr(prod, 'tipo', 'Producto'))
                sabores_lista = getattr(prod, 'sabores_elegidos', getattr(prod, 'sabores', []))

            sabores_str = ", ".join(map(str, sabores_lista)) if isinstance(sabores_lista, (list, tuple, set)) else str(sabores_lista)
            
            lineas.append(f"• {nombre_prod} ({sabores_str})" if sabores_str else f"• {nombre_prod}")
        return lineas

    def obtener_siguiente_estatus(self) -> str:
        """Determina cuál es el siguiente estatus lógico del pedido."""
        if self.estatus == ESTADO_RECIBIDO: 
            return ESTADO_LISTO
        # La transición a 'EN CAMINO' ahora es manejada exclusivamente por la asignación de repartidor.
        elif self.estatus == ESTADO_LISTO and self.tipo_servicio != SERVICIO_DOMICILIO:
            return ESTADO_ENTREGADO
        elif self.estatus == ESTADO_EN_CAMINO:
            return ESTADO_ENTREGADO
        elif self.estatus == ESTADO_ENTREGADO:
            if self.metodo_pago == "EFECTIVO":
                return ESTADO_LIQUIDADO
        return self.estatus

    def obtener_texto_boton_accion(self) -> str:
        """Retorna la etiqueta legible para el botón de acción según el estatus."""
        if self.estatus == ESTADO_RECIBIDO:
            return "MARCAR LISTO"
        elif self.estatus == ESTADO_LISTO:
            # El botón de acción principal ya no manejará la lógica de 'EN CAMINO'.
            # Esto fuerza al usuario a usar el menú 'ASIGNAR REPARTIDOR'.
            return "ENTREGAR PEDIDO" if self.tipo_servicio != SERVICIO_DOMICILIO else ""
        elif self.estatus == ESTADO_EN_CAMINO:
            return "MARCAR ENTREGADO"
        elif self.estatus == ESTADO_ENTREGADO and self.metodo_pago == "EFECTIVO":
            return "LIQUIDAR PAGO"
        return ""