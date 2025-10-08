from flask import Blueprint, session, redirect, url_for, request, flash, render_template
from tienda_virtual.models import db, Producto, Producto_Proveedor

carrito_compras_bp = Blueprint('carrito_compras_bp', __name__) #conexion con el archivo principal

def obtener_stock_disponible(id_producto, id_proveedor): #saca el stock del producto(pueden estar repetidos) segun su proveedor
    stock = db.session.query(Producto_Proveedor.cantidad)\
        .filter_by(id_producto=id_producto, id_proveedor=id_proveedor).scalar()
    return int(stock) if stock is not None else 0

@carrito_compras_bp.route('/agregar_al_carrito/<int:id_producto>/<int:id_proveedor>', methods=['POST'])
def agregar_al_carrito(id_producto, id_proveedor):
    key = f"{id_producto}_{id_proveedor}"
    carrito = session.get('carrito', {})
    en_carrito = carrito.get(key, 0)
    stock_disponible = obtener_stock_disponible(id_producto, id_proveedor)

    if en_carrito < stock_disponible:
        carrito[key] = en_carrito + 1
        session['carrito'] = carrito
        flash('Producto agregado al carrito.')
    else:
        flash('No puedes agregar más unidades de este producto (stock insuficiente).', 'warning')
    return redirect(url_for('productos_bp.productos'))

@carrito_compras_bp.route('/restar_unidad_carrito/<key>', methods=['POST']) #para la funcion de - en el carrito
def restar_unidad_carrito(key):
    carrito = session.get('carrito', {})
    if key in carrito:
        if carrito[key] > 1:
            carrito[key] -= 1
        else:
            del carrito[key]
    session['carrito'] = carrito
    flash('Se eliminó una unidad del producto.')
    return redirect(url_for('carrito_compras_bp.carrito'))


@carrito_compras_bp.route('/eliminar_del_carrito/<key>') #elimina todas las unidades de un mismo producto
def eliminar_del_carrito(key):
    carrito = session.get('carrito', {})
    if key in carrito:
        del carrito[key]
    session['carrito'] = carrito
    flash('Producto eliminado del carrito.')
    return redirect(url_for('carrito_compras_bp.carrito'))

@carrito_compras_bp.route('/vaciar_carrito') #elimina todos los productos del carrito 
def vaciar_carrito():
    session.pop('carrito', None)
    flash('Carrito vaciado.')
    return redirect(url_for('carrito_compras_bp.carrito'))

@carrito_compras_bp.route('/carrito')#datos del carrito de compras
def carrito():
    carrito = session.get('carrito', {})
    productos = []
    total = 0
    total_iva = 0
    total_sin_iva = 0
    IVA_PORCENTAJE = 19  #iva definido

    for key, cantidad in carrito.items():
        partes = key.split('_')
        if len(partes) != 2:
            continue
        id_producto, id_proveedor = map(int, partes)
        producto = Producto.query.get(id_producto)
        producto_proveedor = Producto_Proveedor.query.filter_by(
            id_producto=id_producto,
            id_proveedor=id_proveedor
        ).first()
        if producto and producto_proveedor:
            precio = float(producto_proveedor.precio or 0)
            subtotal = precio * cantidad
            iva_valor = subtotal * IVA_PORCENTAJE / 100
            productos.append({
                'producto': producto,
                'proveedor': producto_proveedor,
                'cantidad': cantidad,
                'precio': precio,
                'iva': IVA_PORCENTAJE,      # Porcentaje fijo
                'iva_valor': iva_valor,     # Valor calculado
                'subtotal': subtotal,
                'key': key
            })
            total_sin_iva += subtotal
            total_iva += iva_valor
            total += subtotal + iva_valor
    return render_template('carrito.html', productos=productos, total=total, total_iva=total_iva, total_sin_iva=total_sin_iva)
#datos mostrados en el template