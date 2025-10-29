from flask import flash
from tienda_virtual import db  # Importa db desde models.py


class EstadoBase:
    """Estado genérico (base)."""
    def marcar_recibido(self, pedido):
        flash("Operación no permitida en este estado.", "warning")

    def cancelar(self, pedido):
        flash("Operación no permitida en este estado.", "warning")


class PendienteState(EstadoBase):
    def marcar_recibido(self, pedido):
        pedido.id_estado_pedido = 4  # Entregado
        db.session.commit()
        flash("Pedido marcado como recibido (desde Pendiente).", "success")

    def cancelar(self, pedido):
        pedido.id_estado_pedido = 5  # Cancelado
        db.session.commit()
        flash("Pedido cancelado correctamente.", "info")


class ProcesadoState(EstadoBase):
    def marcar_recibido(self, pedido):
        pedido.id_estado_pedido = 4
        db.session.commit()
        flash("Pedido entregado correctamente (desde Procesado).", "success")

    def cancelar(self, pedido):
        pedido.id_estado_pedido = 5
        db.session.commit()
        flash("Pedido cancelado mientras estaba procesado.", "info")


class EnviadoState(EstadoBase):
    def marcar_recibido(self, pedido):
        pedido.id_estado_pedido = 4
        db.session.commit()
        flash("Pedido recibido exitosamente.", "success")

    def cancelar(self, pedido):
        flash("No se puede cancelar un pedido que ya fue enviado.", "danger")


class EntregadoState(EstadoBase):
    def marcar_recibido(self, pedido):
        flash("El pedido ya está entregado.", "info")

    def cancelar(self, pedido):
        flash("No se puede cancelar un pedido entregado.", "danger")


class CanceladoState(EstadoBase):
    def marcar_recibido(self, pedido):
        flash("No se puede marcar como recibido un pedido cancelado.", "warning")

    def cancelar(self, pedido):
        flash("El pedido ya está cancelado.", "info")
