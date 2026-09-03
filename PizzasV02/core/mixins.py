
class VistaSeguraMixin:
    def did_mount(self):
        self.vista_activa = True

    def will_unmount(self):
        self.vista_activa = False

    def update_seguro(self):
        # Valida que el componente siga existiendo en la pantalla antes de actualizar
        if getattr(self, "page", None) and getattr(self, "vista_activa", False):
            self.update()