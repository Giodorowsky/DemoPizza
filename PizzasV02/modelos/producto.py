# modelos/producto.py
from dataclasses import dataclass, field, asdict
from typing import List, Dict

# Catálogo centralizado
CATALOGO_PRECIOS = {
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

@dataclass
class Producto:
    nombre: str
    precio: float
    limite_sabores: int
    incluye_refresco: bool
    sabores_elegidos: List[str] = field(default_factory=list)
    refresco_elegido: str = None

    def to_dict(self):
        """Convierte la instancia del producto a un diccionario serializable."""
        return asdict(self)

    @classmethod
    def crear_desde_catalogo(cls, nombre: str):
        info = CATALOGO_PRECIOS.get(nombre)
        if not info: raise ValueError("Producto no encontrado")
        return cls(nombre=nombre, precio=info[0], limite_sabores=info[1], incluye_refresco=info[2])

    @staticmethod
    def obtener_sabores():
        return SABORES_CATALOGO

    def agregar_sabor(self, sabor: str):
        if len(self.sabores_elegidos) < self.limite_sabores:
            self.sabores_elegidos.append(sabor)
            return True
        return False
    
    def puede_agregar_sabor(self) -> bool:
        """Verifica si el producto permite añadir más sabores."""
        return len(self.sabores_elegidos) < self.limite_sabores
    
    def obtener_siguiente_paso(self) -> str:
        """
        Retorna la acción que debe realizar la vista.
        Posibles valores: 'SELECCIONAR_SABORES', 'SELECCIONAR_REFRESCO', 'FINALIZAR'
        """
        if self.puede_agregar_sabor():
            return "SELECCIONAR_SABORES"
        if self.incluye_refresco and self.refresco_elegido is None:
            return "SELECCIONAR_REFRESCO"
        return "FINALIZAR"