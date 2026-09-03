import os
import json
import uuid
import logging
from datetime import datetime
from modelos.pedido import Pedido

logger = logging.getLogger(__name__)

OFFLINE_DIR = "offline_pedidos"

class OfflineManager:
    """
    Gestiona el almacenamiento de pedidos en archivos locales cuando no hay conexión a la base de datos.
    """
    def __init__(self):
        if not os.path.exists(OFFLINE_DIR):
            try:
                os.makedirs(OFFLINE_DIR)
                logger.info("Directorio para pedidos offline creado.")
            except OSError as e:
                logger.exception(f"Error al crear el directorio offline: {e}")

    def _pedido_to_dict(self, pedido, usuario_nombre):
      """Convierte un objeto Pedido a un diccionario serializable, incluyendo el usuario."""
      productos_serializables = [
          p.to_dict() if hasattr(p, "to_dict") else p for p in pedido.productos
      ]

      # Manejo seguro de fecha: si ya es string la dejamos igual, si es datetime usamos isoformat()
      if hasattr(pedido.fecha, "isoformat"):
        fecha_str = pedido.fecha.isoformat()
      else:
        fecha_str = str(pedido.fecha)

      pedido_dict = {
          "id": pedido.id,
          "fecha": fecha_str,
          "cliente_nombre": pedido.cliente_nombre,
          "cliente_tel": pedido.cliente_tel,
          "cliente_dir": pedido.cliente_dir,
          "cliente_colonia": pedido.cliente_colonia,
          "cliente_ref": pedido.cliente_ref,
          "tipo_servicio": pedido.tipo_servicio,
          "productos": productos_serializables,
          "total": pedido.total,
          "metodo_pago": pedido.metodo_pago,
          "estatus": pedido.estatus,
          "repartidor": pedido.repartidor,
          "sucursal": pedido.sucursal,
          "corte": pedido.corte,
          "usuario_responsable": usuario_nombre,
      }
      return pedido_dict

    def guardar_pedido_offline(self, pedido, usuario_nombre):
        """Guarda un pedido en un archivo JSON local con un ID único.

        Si el pedido no tiene id asignado, se crea un id provisional con prefijo OFF- para
        facilitar rastreo y evitar colisiones. Se añade el campo id_provisional al JSON.
        """
        provisional_id = None
        if not getattr(pedido, 'id', None):
            provisional_id = f"OFF-{uuid.uuid4()}"
            try:
                pedido.id = provisional_id
            except Exception:
                # No crítico si no puede asignarse al objeto
                pass

        filename = os.path.join(OFFLINE_DIR, f"pedido_{uuid.uuid4()}.json")
        data_to_save = self._pedido_to_dict(pedido, usuario_nombre)

        if provisional_id:
            data_to_save["id_provisional"] = provisional_id
            data_to_save["id"] = provisional_id

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            logger.info(f"Pedido guardado offline en: {filename} (id: {data_to_save.get('id')})")
        except Exception as e:
            logger.exception(f"Error al guardar pedido offline en {filename}: {e}")

    def obtener_pedidos_offline(self):
        """Carga todos los pedidos desde los archivos JSON en el directorio offline."""
        pedidos_pendientes = []
        if not os.path.exists(OFFLINE_DIR): return []
        for filename in os.listdir(OFFLINE_DIR):
            if filename.endswith(".json"):
                pedidos_pendientes.append(os.path.join(OFFLINE_DIR, filename))
        return pedidos_pendientes