from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from tienda_virtual.pedido_states import (PendienteState, ProcesadoState, EnviadoState, EntregadoState, CanceladoState )

db = SQLAlchemy()

class Cliente(db.Model): # modelos de la base de datos (replica de las tablas)
    __tablename__ = 'cliente'
    id_cliente = db.Column(db.Integer, primary_key=True)
    id_persona = db.Column(db.Integer)
    fecha_registro = db.Column(db.DateTime)
    id_usuario = db.Column(db.Integer)
    id_estado_cliente = db.Column(db.Integer)

class Estado_Cliente(db.Model):
    __tablename__ = 'estado_cliente'
    id_estado_cliente = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(8))

class Detalle_Pedido(db.Model):
    __tablename__ = 'detalle_pedido'
    id_pedido = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, primary_key=True)
    id_proveedor = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Integer)

class Detalles_Venta(db.Model):
    __tablename__ = 'detalles_venta'
    id_venta = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, primary_key=True)
    id_proveedor = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Integer)
    iva = db.Column(db.Numeric)
    subtotal = db.Column(db.Numeric)

class Direccion_Envio(db.Model):
    __tablename__ = 'direccion_envio'
    id_direccion = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer)
    direccion = db.Column(db.String(48))
    ciudad = db.Column(db.String(16))
    departamento = db.Column(db.String(16))
    codigo_postal = db.Column(db.String(8))
    barrio = db.Column(db.String(16))
    
class Metodo_Pago(db.Model):
    __tablename__ = 'metodo_pago'
    id_metodo = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(24))

class Pedido(db.Model):
    __tablename__ = 'pedido'   
    id_pedido = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer)
    id_direccion = db.Column(db.Integer)
    id_metodo = db.Column(db.Integer)
    fecha_pedido = db.Column(db.DateTime)
    id_estado_pedido = db.Column(db.Integer, db.ForeignKey('estado_pedido.id_estado_pedido'))
    estado_pedido = db.relationship("Estado_Pedido", backref="pedidos")  # conexión entre tablas de 1...*

    #VÍNCULO con el patrón State
    @property
    def estado(self):
        mapping = {
            'Pendiente': PendienteState(),
            'Procesado': ProcesadoState(),
            'Enviado': EnviadoState(),
            'Entregado': EntregadoState(),
            'Cancelado': CanceladoState(),
        }
        return mapping.get(self.estado_pedido.estado, PendienteState())


class Estado_Pedido(db.Model):
    __tablename__ = 'estado_pedido'
    id_estado_pedido = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(16))


class Persona(db.Model):
    __tablename__ = 'persona' 
    id_persona = db.Column(db.Integer, primary_key=True)
    cc = db.Column(db.String(24))
    nombre = db.Column(db.String(24))
    apellido = db.Column(db.String(24))
    correo = db.Column(db.String(40))
    telefono = db.Column(db.String(16))
    direccion = db.Column(db.String(48))


class Producto(db.Model):
    __tablename__ = 'producto'  
    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(56))
    codigo = db.Column(db.String(8))
    descripcion = db.Column(db.Text())
    id_estado_producto = db.Column(
        db.Integer, 
        db.ForeignKey('estado_producto.id_estado_producto')
    )  

    estado_producto = db.relationship('Estado_producto', backref='productos')  # Para acceder al estado como objeto

    proveedores = db.relationship(
        'Proveedor',
        secondary='producto_proveedor',
        back_populates='productos'
    ) #relacion entre dtos usando su tabla producto_proveedor

class Proveedor(db.Model):
    __tablename__ = 'proveedor'   
    id_proveedor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(32))
    direccion = db.Column(db.String(48))
    rut = db.Column(db.String(16))
    telefono = db.Column(db.String(16))
    correo = db.Column(db.String(100))
    id_estado_proveedor = db.Column(db.Integer)

    productos = db.relationship(
        'Producto',
        secondary='producto_proveedor',
        back_populates='proveedores'
    )

class Producto_Proveedor(db.Model):
    __tablename__ = 'producto_proveedor'
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), primary_key=True)
    id_proveedor = db.Column(db.Integer, db.ForeignKey('proveedor.id_proveedor'), primary_key=True)
    precio = db.Column(db.Numeric(10, 2))
    cantidad = db.Column(db.Integer)
    fecha_compra = db.Column(db.DateTime)

class Estado_producto(db.Model):
    __tablename__ = 'estado_producto'
    id_estado_producto = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(16))

class Estado_Proveedor(db.Model):
    __tablename__ = 'estado_proveedor'
    id_estado_proveedor = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(8))

class Resena(db.Model):
    __tablename__ = 'resena'   
    id_resena = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer)
    id_producto = db.Column(db.Integer)
    comentario = db.Column(db.Text())
    calificacion = db.Column(db.Integer)
    fecha = db.Column(db.DateTime)

class Tipo(db.Model):
    __tablename__ = 'tipo'   
    id_tipo = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))

class Usuario(db.Model):
    __tablename__ = 'usuario'   
    id_usuario = db.Column(db.Integer, primary_key=True)
    id_persona = db.Column(db.Integer)
    username = db.Column(db.String(24))
    password = db.Column(db.String(16))
    fecha_creacion = db.Column(db.DateTime)
    id_tipo = db.Column(db.Integer)
    id_estado_usuario = db.Column(db.Integer)

class Estado_Usuario(db.Model):
    __tablename__ = 'estado_usuario'
    id_estado_usuario = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(16))

class Venta(db.Model):
    __tablename__ = 'venta'  
    id_ventas = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer)
    id_usuario = db.Column(db.Integer)
    total = db.Column(db.Numeric(10, 2))
    fecha = db.Column(db.DateTime)
