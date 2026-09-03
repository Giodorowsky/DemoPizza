from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Gasto:
    descripcion: str
    monto: float
    sucursal: str
    cajero: str = "Desconocido" # Reordenado para que los campos sin valor por defecto vayan primero
    fecha: datetime = field(default_factory=datetime.now)
    corte: int = 0