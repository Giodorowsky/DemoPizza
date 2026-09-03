NOMBRE_NEGOCIO = "PIZZA EXPRESS"

VERSION_APP = "3.0.0"

# --- SUCURSALES DISPONIBLES ---
SUCURSALES_CATALOGO = [
    "MATRIZ",
    "SUCURSAL2"
]


# --- COLORES DE IDENTIDAD ---
COLOR_PRIMARIO = "#FF9900"    # Naranja/Rojo Pizza
COLOR_SECUNDARIO = "#121212" 
COLOR_TRES = "#B90E0EFF" 
COLOR_FONDO = "#060606"      # Negro mate
COLOR_CONTRASTE = "#1E1E1E"   # Gris tarjetas
COLOR_TEXTO = "#FFFFFF"
COLOR_EXITO = "#1AC720"
COLOR_ERROR = "#FF1100"
COLOR_NUEVO = "#0058E6"
COLOR_GRAFICA_SECUNDARIO = "#E91E63" # Rosa/Magenta para contraste en gráficas
# --- CONSTANTES DE ESTADO ---
SERVICIO_LOCAL = "LOCAL"
SERVICIO_DOMICILIO = "DOMICILIO"

ESTADO_RECIBIDO = "RECIBIDO"
ESTADO_PREPARANDO = "EN COCINA"
ESTADO_LISTO = "POR ENTREGAR"
ESTADO_EN_CAMINO ="EN CAMINO"
ESTADO_ENTREGADO = "ENTREGADO"
ESTADO_LIQUIDADO = "LIQUIDADO"

# --- MAPEO DE BASE DE DATOS (El corazón de la sincronización) ---
# Si decides cambiar el nombre de una columna en la DB, solo lo haces aquí.
DB_COLUMNS = {
    "ID": "id_ticket",
    "FECHA": "fecha_hora",
    "CLIENTE": "nombre_cliente",
    "TEL": "telefono",
    "DIR": "direccion",
    "COLONIA": "colonia",
    "DETALLE": "pedido_detalle",
    "TOTAL": "monto_total",
    "METODO": "metodo_pago",
    "SERVICIO": "tipo_servicio",
    "ESTATUS": "estado_pedido",
    "REPARTIDOR": "repartidor_asignado",
    "SUCURSAL": "sucursal",
    "CAJERO": "cajero",
    "REF": "referencias",
    "CORTE": "corte",
}

# --- COLONIAS PARA SERVICIO A DOMICILIO ---
COLONIAS_CATALOGO = [
    "CENTRO",
    "REFORMA",
    "DEL VALLE",
    "POLANCO",
    "CONDESA",
    "ROMA NORTE",
    "SANTA FE"
]
# --- PRECIOS Y LÓGICA ---
# "TAMAÑO": (PRECIO, MÁX_SABORES, INCLUYE_REFRESCO)
PRECIOS_PIZZAS = {
    "CHICA": (160, 2, False),
    "MEDIANA": (235, 2, False),
    "GRANDE": (275, 2, False),
    "FAMILIAR": (320, 2, False),
    "BARRA": (415, 2, True),
    "MEGA": (415, 4, True),
}

SABORES_CATALOGO = [
    "Hawaiana", "Peperoni", "Mexicana", "Champiñones", 
    "Carnes Frías", "Especial", "Pollo BBQ", "Quesos"
]

REFRESCO_PRECIOS = {"COCA COLA":(50),"MANZANITA":(45),"MIRINDA":(45),"JARRITO":(30)}