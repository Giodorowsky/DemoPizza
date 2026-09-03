# Este archivo encapsula la navegación compleja
class GestorFlujoPizza:
    @staticmethod
    def obtener_siguiente_paso(producto):
        if producto.puede_agregar_sabor():
            return "SABORES"
        if producto.incluye_refresco and not producto.refresco_elegido:
            return "REFRESCO"
        return "FINALIZAR_PIZZA"