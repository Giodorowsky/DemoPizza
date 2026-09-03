from dataclasses import dataclass

@dataclass
class Usuario:
    nombre: str
    rol: str
    esta_activo: bool
    id: int = None  # El campo con valor por defecto va al final