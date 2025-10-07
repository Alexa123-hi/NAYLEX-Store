from flask import Blueprint, render_template, request, session
from models import db, Producto, Proveedor, Producto_Proveedor

productos_bp = Blueprint('productos_bp', __name__) #conexion con tienda.py

@productos_bp.route('/productos', methods=['GET'])
def productos():
    filtro = request.args.get('filtro', '').strip()
    consulta = Producto.query

    if filtro: #filtro de productos segun la busqueda 
        filtro_like = f"%{filtro.lower()}%"
        consulta = consulta.join(Producto.proveedores, isouter=True).filter(
            db.or_(
                db.func.lower(Producto.nombre).like(filtro_like),
                db.func.lower(Producto.codigo).like(filtro_like),
                db.func.lower(Producto.descripcion).like(filtro_like),
                db.func.lower(Proveedor.nombre).like(filtro_like)
            )
        ).distinct()

    productos = consulta.order_by(Producto.nombre.asc()).all() #ordena los productos segun el nombre (alfabeticamente)
    carrito = session.get('carrito', {})
    productos_vista = []
    commit_flag = False  # Controla si hace falta hacer commit (para guardar en la base de datos)

    for producto in productos:
        for proveedor in producto.proveedores:
            pp = Producto_Proveedor.query.filter_by(
                id_producto=producto.id_producto,
                id_proveedor=proveedor.id_proveedor
            ).first()
            if not pp:
                continue
            key = f"{producto.id_producto}_{proveedor.id_proveedor}"
            en_carrito = int(carrito.get(key, 0))
            stock_disponible = max((pp.cantidad or 0) - en_carrito, 0)

            # Si el estado es 3(descontinuado), visualiza ese estado 
            if producto.id_estado_producto == 3:
                estado_visual = producto.estado_producto.estado if producto.estado_producto else "No definido"
            # Si el stock es 0 y NO está descontinuado(3), cambia a 2 y muestra 'Agotado'
            elif stock_disponible == 0 and producto.id_estado_producto != 3:
                if producto.id_estado_producto != 2:  # Solo actualiza si no es 2
                    producto.id_estado_producto = 2
                    commit_flag = True
                estado_visual = "Agotado"
            # Si no, muestra el estado que tenga
            else:
                estado_visual = producto.estado_producto.estado if producto.estado_producto else "No definido"

            productos_vista.append({ #dalos que se mostraran en la plantilla (card)
                'producto': producto,
                'proveedor': proveedor,
                'precio': float(pp.precio or 0),
                'stock_disponible': stock_disponible,
                'en_carrito': en_carrito,
                'estado_visual': estado_visual
            })

    if commit_flag:
        db.session.commit()  # guarda los cambios en la base de datos 

    return render_template('productos.html', productos=productos_vista, filtro=filtro)
