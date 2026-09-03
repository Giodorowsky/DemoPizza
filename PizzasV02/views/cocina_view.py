import asyncio
import flet as ft
import flet_audio as fta

from datos_negocio import (
    COLOR_CONTRASTE,
    COLOR_ERROR,
    COLOR_EXITO,
    COLOR_FONDO,
    COLOR_NUEVO,
    COLOR_PRIMARIO,
    COLOR_TEXTO,
    ESTADO_LISTO,
)
from views.componentes.botones import BotonAnimado


class CocinaView(ft.Container):

    def __init__(self, db, sucursal="MATRIZ"):
        super().__init__()
        self.db = db
        self.sucursal = sucursal
        self.expand = True
        self.bgcolor = COLOR_FONDO
        self.padding = 20

        self.ultimo_id_visto = 0
        self.vista_activa = True

        # 1. Configuración idéntica a la referencia oficial
        # NOTA: Cambiamos "assets/campana.mp3" por "campana.mp3"
        self.audio_notificacion = fta.Audio(
            src="campana.mp3",
            autoplay=False,
            volume=1,
            balance=0,
            release_mode=fta.ReleaseMode.STOP,
            on_loaded=lambda _: print("Audio cargado correctamente"),
            on_state_change=lambda e: print("Estado de audio:", e.state),
        )

        self.lista_tickets = ft.Column(
            spacing=15, scroll=ft.ScrollMode.AUTO, expand=True
        )
        self.titulo_texto = ft.Text(
            f"MONITOR DE COCINA - {self.sucursal}",
            size=28,
            weight="bold",
            color=COLOR_PRIMARIO,
        )

        self.content = ft.Column(
            expand=True,
            controls=[
                self.titulo_texto,
                ft.Divider(height=10, color=ft.Colors.GREY_800),
                self.lista_tickets,
            ],
        )

    def actualizar_sucursal(self, nueva_sucursal):
        self.sucursal = nueva_sucursal
        self.ultimo_id_visto = 0
        self.titulo_texto.value = f"MONITOR DE COCINA - {self.sucursal}"
        try:
            self.update()
        except Exception:
            pass
        asyncio.create_task(self.forzar_recarga_inmediata())

    async def forzar_recarga_inmediata(self):
        try:
            pedidos = await self.db.obtener_pedidos_cocina(self.sucursal)
            # BLINDAJE: Aseguramos que 'pedidos' sea una lista antes de procesarla.
            # Si la DB falla, puede devolver None.
            if pedidos and isinstance(pedidos, list):
                self.ultimo_id_visto = max([p.get("id", 0) for p in pedidos])
            await self.dibujar_tickets(pedidos)
        except Exception as e:
            print(f"🔥 Error al cambiar de sucursal en cocina: {e}")

    def _notificar(self, mensaje, color):
        from views.componentes.ayuditas import notificar_seguro

        if getattr(self, "page", None):
            notificar_seguro(self.page, mensaje, color)

    def will_unmount(self):
        self.vista_activa = False

    def did_mount(self):
        self.vista_activa = True

        # 2. Registrar en page.services exactamente como la referencia oficial
        if self.page and self.audio_notificacion not in self.page.services:
            self.page.services.append(self.audio_notificacion)
            self.page.update()

        asyncio.create_task(self.bucle_actualizacion())

    async def tocar_campana_local(self):
        try:
            # 3. Reproducción idéntica a la referencia: await audio.play()
            await self.audio_notificacion.play()
        except Exception as e:
            print(f"Error reproduciendo audio: {e}")

    async def bucle_actualizacion(self):
        while self.vista_activa:
            try:
                pedidos = await self.db.obtener_pedidos_cocina(self.sucursal)

                if pedidos is None:
                    pedidos = []

                if pedidos:
                    max_id_actual = max(
                        [
                            p.get("id", 0)
                            for p in pedidos
                            if isinstance(p, dict)
                        ]
                    )

                    # Simplificación: El rol de cocina es implícito al estar en esta vista.
                    # La lógica de navegación ya protege esta ruta.
                    
                    # Si es la primera carga (inicio del sistema), sincronizamos sin sonar
                    if self.ultimo_id_visto == 0:
                        self.ultimo_id_visto = max_id_actual
                    elif max_id_actual > self.ultimo_id_visto:
                        await self.tocar_campana_local()
                        self._notificar(
                            f"¡NUEVO PEDIDO ({self.sucursal})! Ticket #{max_id_actual}",
                            COLOR_PRIMARIO,
                        )

                        self.ultimo_id_visto = max_id_actual

                await self.dibujar_tickets(pedidos)
                await asyncio.sleep(5)

            except Exception as e:
                print(f"🔥 Error en el bucle de cocina: {e}")
                await asyncio.sleep(5)

    async def dibujar_tickets(self, pedidos):
        self.lista_tickets.controls.clear()

        if not pedidos or not isinstance(pedidos, list):
            try:
                self.update()
            except Exception:
                pass
            return

        for p in pedidos:
            if not isinstance(p, dict):
                continue

            servicio = p.get("servicio", "LOCAL")
            es_domicilio = servicio == "DOMICILIO"
            color_etiqueta = COLOR_ERROR if es_domicilio else COLOR_NUEVO

            lista_productos_visuales = []
            detalles = p.get("detalle") or []

            for prod in detalles:
                if not isinstance(prod, dict):
                    continue

                nombre_prod = (
                    prod.get("nombre") or prod.get("producto") or "Producto"
                )
                sabores_raw = (
                    prod.get("sabores_elegidos")
                    or prod.get("sabores")
                    or prod.get("ingredientes")
                    or prod.get("mitades")
                    or []
                )
                lista_sabores = []

                if isinstance(sabores_raw, list):
                    for sab in sabores_raw:
                        if isinstance(sab, dict):
                            lista_sabores.append(
                                sab.get("nombre")
                                or sab.get("sabor")
                                or str(sab)
                            )
                        elif isinstance(sab, str):
                            lista_sabores.append(sab)
                elif isinstance(sabores_raw, str):
                    lista_sabores.append(sabores_raw)

                texto_sabores = (
                    f" 👉 ({', '.join(lista_sabores)})" if lista_sabores else ""
                )

                nota = prod.get("nota") or prod.get("observaciones")
                texto_nota = f" 📝 [{nota}]" if nota else ""

                lista_productos_visuales.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    f"• {nombre_prod}",
                                    size=18,
                                    weight="bold",
                                    color=COLOR_TEXTO,
                                ),
                                (
                                    ft.Text(
                                        f"{texto_sabores}{texto_nota}",
                                        size=15,
                                        color=COLOR_PRIMARIO,
                                        weight="w500",
                                    )
                                    if (texto_sabores or texto_nota)
                                    else ft.Container()
                                ),
                            ],
                            spacing=2,
                        ),
                        padding=ft.Padding.only(right=15, bottom=5),
                    )
                )

            ticket = ft.Container(
                expand=True,
                bgcolor=COLOR_CONTRASTE,
                padding=15,
                border_radius=15,
                border=ft.Border.all(
                    1, ft.Colors.with_opacity(0.1, COLOR_TEXTO)
                ),
                content=ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    f"#{p.get('id', '?')}",
                                    size=24,
                                    weight="bold",
                                    color=COLOR_PRIMARIO,
                                ),
                                ft.Container(
                                    bgcolor=color_etiqueta,
                                    padding=ft.Padding.symmetric(
                                        horizontal=8, vertical=2
                                    ),
                                    border_radius=5,
                                    content=ft.Text(
                                        servicio,
                                        size=10,
                                        weight="bold",
                                        color=COLOR_TEXTO,
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            width=100,
                        ),
                        ft.VerticalDivider(width=1, color=ft.Colors.GREY_800),
                        ft.Row(
                            lista_productos_visuales,
                            spacing=15,
                            expand=True,
                            wrap=True,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.VerticalDivider(width=1, color=ft.Colors.GREY_800),
                        ft.Container(
                            width=140,
                            content=BotonAnimado(
                                "LISTO",
                                on_click=lambda _, id_p=p.get(
                                    "id"
                                ): asyncio.create_task(
                                    self.marcar_listo(id_p)
                                ),
                                bgcolor=COLOR_EXITO,
                                height=45,
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    spacing=15,
                ),
            )
            self.lista_tickets.controls.append(ticket)

        try:
            self.update()
        except Exception:
            pass

    async def marcar_listo(self, id_ticket):
        try:
            await self.db.actualizar_estatus_pedido(id_ticket, ESTADO_LISTO)
            self._notificar(
                f"Pedido #{id_ticket} marcado como listo", COLOR_EXITO
            )

            pedidos_actualizados = await self.db.obtener_pedidos_cocina(
                self.sucursal
            )
            await self.dibujar_tickets(pedidos_actualizados)
        except Exception as e:
            self._notificar(f"Error al procesar: {str(e)}", COLOR_ERROR)