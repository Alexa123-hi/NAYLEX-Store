from flask import Blueprint, render_template, session, redirect, url_for, flash, request, send_file, current_app
from tienda_virtual.models import db, Pedido, Detalle_Pedido, Direccion_Envio, Venta, Detalles_Venta, Producto_Proveedor, Estado_Pedido, Metodo_Pago, Producto, Proveedor
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
import time
import io
import os

compras_bp = Blueprint('compras_bp', __name__)

@compras_bp.route('/compra', methods=['GET'])
def compra():
    IVA_PORCENTAJE = 0.19
    carrito = session.get('carrito', {})
    productos = []
    total_sin_iva = 0
    total_iva = 0
    total = 0

    for key, cantidad in carrito.items():
        id_producto, id_proveedor = map(int, key.split('_'))
        producto = Producto.query.get(id_producto)
        producto_proveedor = Producto_Proveedor.query.filter_by(
            id_producto=id_producto,
            id_proveedor=id_proveedor
        ).first()
        if producto and producto_proveedor:
            precio = float(producto_proveedor.precio or 0)
            subtotal_sin_iva = precio * cantidad
            iva_producto = subtotal_sin_iva * IVA_PORCENTAJE
            subtotal_con_iva = subtotal_sin_iva + iva_producto
            productos.append({
                'producto': producto,
                'proveedor': producto_proveedor,
                'cantidad': cantidad,
                'precio': precio,
                'iva': int(IVA_PORCENTAJE * 100),
                'subtotal': subtotal_con_iva
            })
            total_sin_iva += subtotal_sin_iva
            total_iva += iva_producto
            total += subtotal_con_iva

    return render_template(
        'compras.html',
        productos=productos,
        total_sin_iva=total_sin_iva,
        total_iva=total_iva,
        total=total
    )

@compras_bp.route('/direccion_envio', methods=['GET', 'POST'])
def direccion_envio():
    error_msg = None
    direccion = ciudad = departamento = codigo_postal = barrio = ''
    if request.method == 'POST': #llenado de datos
        direccion = request.form.get('direccion', '').strip()
        ciudad = request.form.get('ciudad', '').strip()
        departamento = request.form.get('departamento', '').strip()
        codigo_postal = request.form.get('codigo_postal', '').strip()
        barrio = request.form.get('barrio', '').strip()
        
        if not all([direccion, ciudad, departamento, codigo_postal, barrio]):
            error_msg = "Todos los campos son obligatorios. Por favor, completa todos los datos."
            return render_template('direccion_envio.html',
                direccion=direccion, 
                ciudad=ciudad, 
                departamento=departamento,
                codigo_postal=codigo_postal, 
                barrio=barrio, 
                error_msg=error_msg)
        
        session['direccion_envio'] = direccion
        session['ciudad_envio'] = ciudad
        session['departamento_envio'] = departamento
        session['codigo_postal_envio'] = codigo_postal
        session['barrio_envio'] = barrio #los guarda en la sesion ahsta que se confirme el pago
        return redirect(url_for('compras_bp.pago'))
    
    return render_template('direccion_envio.html', 
        direccion=direccion, 
        ciudad=ciudad, 
        departamento=departamento,
        codigo_postal=codigo_postal, 
        barrio=barrio, 
        error_msg=error_msg)


@compras_bp.route('/pago', methods=['GET', 'POST'])
def pago():
    mensaje_exito = None
    metodos_pago = Metodo_Pago.query.all()
    if request.method == 'POST':
        id_cliente = session.get('id_cliente')
        id_usuario = session.get('usuario_id')
        metodo_pago = request.form.get('metodo')
        carrito = session.get('carrito', {})
        direccion = {
            "direccion": session.get('direccion_envio'),
            "ciudad": session.get('ciudad_envio'),
            "departamento": session.get('departamento_envio'),
            "codigo_postal": session.get('codigo_postal_envio'),
            "barrio": session.get('barrio_envio')
        }

        # Realiza la valión y si algo esta mal lo devuelve a la dirección de envío
        if not (id_cliente and id_usuario and metodo_pago and carrito and
                direccion["direccion"] and direccion["ciudad"] and direccion["departamento"] and
                direccion["codigo_postal"] and direccion["barrio"]):
            flash("Faltan datos para procesar el pedido.", "danger")
            return redirect(url_for('compras_bp.direccion_envio'))

        try:
            #Guarda la dirección de envío
            direccion_envio = Direccion_Envio(
                id_cliente=id_cliente,
                direccion=direccion["direccion"],
                ciudad=direccion["ciudad"],
                departamento=direccion["departamento"],
                codigo_postal=direccion["codigo_postal"],
                barrio=direccion["barrio"]
            )
            db.session.add(direccion_envio)
            db.session.commit()

            #Guarda el pedido
            pedido = Pedido(
                id_cliente=id_cliente,
                id_direccion=direccion_envio.id_direccion,
                id_metodo=metodo_pago,
                fecha_pedido=datetime.now(),
                id_estado_pedido=1
            )
            db.session.add(pedido)
            db.session.flush()

            #Guarda la venta
            venta = Venta(
                id_cliente=id_cliente,
                id_usuario=id_usuario,
                total=0,
                fecha=datetime.now()
            )
            db.session.add(venta)
            db.session.flush()

            IVA_PORCENTAJE = 0.19
            total_venta = 0

            #Detalles
            for key, cantidad in carrito.items():
                id_producto, id_proveedor = map(int, key.split('_'))
                pp = Producto_Proveedor.query.filter_by(
                    id_producto=id_producto, id_proveedor=id_proveedor
                ).first()
                if not pp:
                    continue
                precio = float(pp.precio or 0)
                subtotal_sin_iva = precio * cantidad
                iva_valor = subtotal_sin_iva * 0.19
                subtotal_con_iva = subtotal_sin_iva + iva_valor

                # Actualiza el stock (cantidad de productos)
                if pp.cantidad is not None:
                    if pp.cantidad < cantidad:
                        flash(f"Stock insuficiente para el producto {id_producto} del proveedor {id_proveedor}.", "danger")
                        return redirect(url_for('compras_bp.compra'))
                    pp.cantidad -= cantidad
                    if pp.cantidad < 0:
                        pp.cantidad = 0

                with db.session.no_autoflush:
                    # Detalle del Pedido
                    detalle_pedido = Detalle_Pedido.query.filter_by(
                        id_pedido=pedido.id_pedido,
                        id_producto=id_producto,
                        id_proveedor=id_proveedor
                    ).first()
                    if detalle_pedido:
                        detalle_pedido.cantidad += cantidad
                    else:
                        detalle_pedido = Detalle_Pedido(
                            id_pedido=pedido.id_pedido,
                            id_producto=id_producto,
                            id_proveedor=id_proveedor,
                            cantidad=cantidad
                        )
                        db.session.add(detalle_pedido)

                    # Detalle de la Venta
                    detalle_venta = Detalles_Venta.query.filter_by(
                        id_venta=venta.id_ventas,
                        id_producto=id_producto,
                        id_proveedor=id_proveedor
                    ).first()
                    if detalle_venta:
                        detalle_venta.cantidad += cantidad
                        detalle_venta.iva += iva_valor
                        detalle_venta.subtotal += subtotal_con_iva
                    else:
                        detalle_venta = Detalles_Venta(
                            id_venta=venta.id_ventas,
                            id_producto=id_producto,
                            id_proveedor=id_proveedor,
                            cantidad=cantidad,
                            iva=iva_valor,
                            subtotal=subtotal_con_iva
                        )
                        db.session.add(detalle_venta)
                total_venta += subtotal_con_iva

            # Actualiza el total de la venta 
            venta.total = total_venta
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print(f"Error registrando la compra: {e}", "danger")
            flash("Error registrando la compra.", "danger")
            return redirect(url_for('compras_bp.direccion_envio'))

        # Limpia la sesión del carrito y dirección
        session.pop('carrito', None)
        session.pop('direccion_envio', None)
        session.pop('ciudad_envio', None)
        session.pop('departamento_envio', None)
        session.pop('codigo_postal_envio', None)
        session.pop('barrio_envio', None)

        # Lo envia a la confirmación del pago
        return redirect(url_for('compras_bp.confirmar_pago', id_pedido=pedido.id_pedido))

    return render_template('metodo_pago.html', metodos_pago=metodos_pago)

#--------------------------------Confirmación del pago---------------------------------------
@compras_bp.route('/confirmar_pago/<int:id_pedido>')
def confirmar_pago(id_pedido):
    pedido = Pedido.query.get(id_pedido)
    if not pedido:
        flash("Pedido no encontrado", "danger")
        return redirect(url_for('compras_bp.compra'))

    metodo = Metodo_Pago.query.get(pedido.id_metodo)
    detalles = Detalle_Pedido.query.filter_by(id_pedido=id_pedido).all()
    subtotal_general = 0
    iva_total = 0
    iva_porcentaje = 19

    for detalle in detalles:
        prod_prov = Producto_Proveedor.query.filter_by(
            id_producto=detalle.id_producto,
            id_proveedor=detalle.id_proveedor
        ).first()
        precio_unitario = float(prod_prov.precio) if prod_prov else 0
        cantidad = detalle.cantidad
        subtotal = precio_unitario * cantidad
        iva_valor = subtotal * iva_porcentaje / 100
        subtotal_general += subtotal
        iva_total += iva_valor

    total_pagar = subtotal_general + iva_total

    #segun seleccción del metodo
    if metodo and metodo.nombre.lower() in ['contraentrega', 'contra entrega', 'contra-entrega']:
        mensaje = (
            f"Tu pedido fue registrado exitosamente.<br>"
            f"El valor total a pagar es: <b>${total_pagar:,.0f}</b> al momento de la entrega."
        )
    else:
        mensaje = (
            f"¡Pago realizado con éxito! Tu pedido está <b>{pedido.estado_pedido.estado}</b>."
        )

    return render_template('confirmacion.html', mensaje=mensaje, id_pedido=pedido.id_pedido)



@compras_bp.route('/estado_pedido/<int:id_pedido>/<estado>') #cambio del estado del pedido
def estado_pedido(id_pedido, estado):
    pedido = Pedido.query.get(id_pedido)
    if not pedido:
        return "Pedido no encontrado", 404

    estado_map = {
        'pendiente': 1,
        'procesado': 2,
        'enviado': 3,
        'entregado': 4,
        'cancelado': 5
    }
    id_estado = estado_map.get(estado)
    if not id_estado:
        mensaje = "Estado desconocido."
        return render_template('confirmacion.html', mensaje=mensaje, id_pedido=id_pedido)

    estado_obj = Estado_Pedido.query.get(id_estado)
    estado_nombre = estado_obj.estado if estado_obj else estado.capitalize()
    mensaje = ""
    siguiente_estado = None

    if estado == 'pendiente':
        mensaje = f"Pago realizado con éxito. Tu pedido está <b>{estado_nombre}</b>."
        time.sleep(5)
        pedido.id_estado_pedido = estado_map['procesado']
        pedido.estado = Estado_Pedido.query.get(estado_map['procesado']).estado
        db.session.commit()
        siguiente_estado = 'procesado'

    elif estado == 'procesado':
        mensaje = f"¡Tu pedido ya fue <b>{estado_nombre}</b>! En breve será enviado."
        time.sleep(5)
        pedido.id_estado_pedido = estado_map['enviado']
        pedido.estado = Estado_Pedido.query.get(estado_map['enviado']).estado
        db.session.commit()
        siguiente_estado = 'enviado'

    elif estado == 'enviado':
        mensaje = f"¡Tu pedido ha sido <b>{estado_nombre}</b>! Pronto llegará a tu dirección."
    else:
        mensaje = "Estado desconocido."

    if siguiente_estado:
        return redirect(url_for('compras_bp.estado_pedido', id_pedido=id_pedido, estado=siguiente_estado))
    else:
        return render_template('confirmacion.html', mensaje=mensaje, id_pedido=id_pedido)

#--------------------------------Visualización de pedidos realizados---------------------------------------
@compras_bp.route('/mis_pedidos')
def mis_pedidos():
    id_cliente = session.get('id_cliente')
    if not id_cliente:
        flash("Debes iniciar sesión para ver tus pedidos.", "danger")
        return redirect(url_for('inicioSesion'))
    pedidos = Pedido.query.filter_by(id_cliente=id_cliente).order_by(Pedido.fecha_pedido.desc()).all()
    return render_template('pedidos.html', pedidos=pedidos)

#los detalles de cada pedido
@compras_bp.route('/detalle_pedido/<int:id_pedido>')
def detalle_pedido(id_pedido):
    pedido = Pedido.query.get(id_pedido)
    if not pedido:
        flash("Pedido no encontrado", "danger")
        return redirect(url_for('compras_bp.mis_pedidos'))

    detalles = Detalle_Pedido.query.filter_by(id_pedido=id_pedido).all()
    productos = []
    subtotal_general = 0
    iva_total = 0

    for detalle in detalles:
        producto = Producto.query.get(detalle.id_producto)
        proveedor = Proveedor.query.get(detalle.id_proveedor)
        prod_prov = Producto_Proveedor.query.filter_by(
            id_producto=producto.id_producto,
            id_proveedor=proveedor.id_proveedor
        ).first()

        if not prod_prov:
            precio_unitario = 0
        else:
            precio_unitario = float(prod_prov.precio)

        cantidad = detalle.cantidad
        iva_porcentaje = 19  # Modifica aquí si tienes IVA variable
        subtotal = precio_unitario * cantidad
        iva_valor = subtotal * iva_porcentaje / 100

        productos.append({
            'producto': producto,
            'proveedor': (proveedor.nombre if proveedor else '-'),
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'iva_porcentaje': iva_porcentaje,
            'iva_valor': iva_valor,
            'subtotal': subtotal
        })

        subtotal_general += subtotal
        iva_total += iva_valor

    return render_template(
        'detalle_pedido.html',
        pedido=pedido,
        productos=productos,
        subtotal_general=subtotal_general,
        iva_total=iva_total,
        total_general=subtotal_general + iva_total
    ) #datos que se mostraran en el template


#------------------------------CAMBIO DE ESTADO DEL PEDIDO CON LOS BOTONES----------------------------------
@compras_bp.route('/pedido_recibido/<int:id_pedido>', methods=['POST'])
def pedido_recibido(id_pedido):
    pedido = Pedido.query.get(id_pedido)
    if not pedido:
        flash("Pedido no encontrado.", "danger")
        return redirect(url_for('compras_bp.mis_pedidos'))
    if pedido.id_estado_pedido == 4:
        flash("El pedido ya está entregado.", "info")
    else:
        pedido.id_estado_pedido = 4  # 4 = entregado
        db.session.commit()
        flash("¡Pedido marcado como recibido!", "success")
    return redirect(url_for('compras_bp.detalle_pedido', id_pedido=id_pedido))


@compras_bp.route('/pedido_cancelar/<int:id_pedido>', methods=['POST'])
def pedido_cancelar(id_pedido):
    pedido = Pedido.query.get(id_pedido)
    if not pedido:
        flash("Pedido no encontrado.", "danger")
        return redirect(url_for('compras_bp.mis_pedidos'))

    if pedido.id_estado_pedido in [2, 3, 4]:
        flash("No se puede cancelar un pedido que ya está procesado, enviado o entregado.", "warning")
        return redirect(url_for('compras_bp.detalle_pedido', id_pedido=id_pedido))

    pedido.id_estado_pedido = 5  # 5 = Cancelado
    db.session.commit()
    flash("Pedido cancelado con éxito, se ha devuelto el dinero.", "success")
    return redirect(url_for('compras_bp.detalle_pedido', id_pedido=id_pedido))


#-------------------------------------------------Factura De Pago----------------------------------------------
@compras_bp.route('/factura/<int:id_pedido>')
def factura(id_pedido):
    from tienda_virtual.models import Pedido, Detalle_Pedido, Cliente, Persona, Proveedor, Producto, Producto_Proveedor, Metodo_Pago
    import io, os
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from flask import current_app, send_file, flash, redirect, url_for

    # ==========================================================
    # 🧠 SINGLETON: Configuración global del PDF
    # ==========================================================
    class ConfiguracionFactura:
        _instancia = None

        def __new__(cls):
            if cls._instancia is None:
                cls._instancia = super().__new__(cls)
                cls._instancia.logo_path = os.path.join(current_app.root_path, 'static', 'imagenes', 'ICONO.png')
                cls._instancia.font_titulo = "Times-Bold"
                cls._instancia.font_texto = "Times-Roman"
                cls._instancia.iva_porcentaje = 19
                cls._instancia.contacto = "naylexstore@gmail.com"
            return cls._instancia

    # ==========================================================
    # 💡 STRATEGY: Cálculo de IVA (permite cambiar fácilmente)
    # ==========================================================
    class IVAStrategy:
        def calcular(self, subtotal: float) -> float:
            raise NotImplementedError

    class IVA19(IVAStrategy):
        def calcular(self, subtotal: float) -> float:
            return subtotal * 0.19

    class IVA0(IVAStrategy):
        def calcular(self, subtotal: float) -> float:
            return 0.0

    # ==========================================================
    # 🧱 BUILDER: Construcción paso a paso de la factura PDF
    # ==========================================================
    class FacturaBuilder:
        def __init__(self, pedido, detalles):
            self.pedido = pedido
            self.detalles = detalles
            self.config = ConfiguracionFactura()
            self.buffer = io.BytesIO()
            self.canvas = canvas.Canvas(self.buffer, pagesize=letter)
            self.width, self.height = letter
            self.y = self.height - 170
            self.subtotal_general = 0
            self.iva_total = 0
            self.iva_strategy = IVA19()  # estrategia por defecto

        def agregar_encabezado(self):
            try:
                self.canvas.drawImage(self.config.logo_path, 40, self.height - 140, width=110, height=110, mask='auto')
            except Exception as e:
                print(f"⚠️ No se pudo cargar el logo: {e}")

            self.canvas.setFont(self.config.font_titulo, 24)
            self.canvas.drawString(170, self.height - 80, "Factura de compra - Naylex Store")
            self.canvas.setFont(self.config.font_texto, 13)

            # Información del cliente
            cliente = Cliente.query.filter_by(id_cliente=self.pedido.id_cliente).first()
            nombre_cliente, cedula_cliente = "-", "-"
            if cliente:
                persona = Persona.query.filter_by(id_persona=cliente.id_persona).first()
                if persona:
                    nombre_cliente = f"{persona.nombre} {persona.apellido}"
                    cedula_cliente = persona.cc

            inicio = 40
            self.canvas.drawString(inicio, self.y, f"Pedido N°: {self.pedido.id_pedido}")
            self.y -= 18
            self.canvas.drawString(inicio, self.y, f"Fecha: {self.pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M') if self.pedido.fecha_pedido else '-'}")
            self.y -= 18
            self.canvas.drawString(inicio, self.y, f"Cliente: {nombre_cliente}")
            self.y -= 18
            self.canvas.drawString(inicio, self.y, f"Cédula: {cedula_cliente}")
            self.y -= 28
            return self

        def agregar_tabla_productos(self):
            fin_linea = 585
            self.canvas.setFont("Times-Bold", 12)
            encabezado = ["Producto", "Proveedor", "Cant.", "P. Unit", "IVA (%)", "IVA Valor", "Subtotal"]
            x_list = [40, 150, 230, 305, 385, 455, 535]
            for i, titulo in enumerate(encabezado):
                self.canvas.drawString(x_list[i], self.y, titulo)
            self.canvas.line(38, self.y - 2, fin_linea, self.y - 2)

            self.canvas.setFont("Times-Roman", 12)
            self.y -= 18

            for detalle in self.detalles:
                producto = Producto.query.get(detalle.id_producto)
                proveedor = Proveedor.query.get(detalle.id_proveedor)
                prod_nombre = (producto.nombre[:16] + '...') if producto and len(producto.nombre) > 16 else (producto.nombre if producto else "-")
                prov_nombre = (proveedor.nombre[:15] + '...') if proveedor and len(proveedor.nombre) > 15 else (proveedor.nombre if proveedor else "-")

                cantidad = detalle.cantidad
                prod_prov = Producto_Proveedor.query.filter_by(id_producto=producto.id_producto, id_proveedor=detalle.id_proveedor).first()
                precio_unit = float(prod_prov.precio) if prod_prov else 0
                subtotal = precio_unit * cantidad

                iva_valor = self.iva_strategy.calcular(subtotal)

                fila = [
                    prod_nombre,
                    prov_nombre,
                    str(cantidad),
                    "${:,.0f}".format(precio_unit),
                    f"{self.config.iva_porcentaje}%",
                    "${:,.0f}".format(iva_valor),
                    "${:,.0f}".format(subtotal),
                ]

                for i, dato in enumerate(fila):
                    self.canvas.drawString(x_list[i], self.y, dato)
                self.y -= 18

                self.subtotal_general += subtotal
                self.iva_total += iva_valor

                if self.y < 90:
                    self.canvas.showPage()
                    self.canvas.setFont("Times-Roman", 12)
                    self.y = self.height - 60

            self.canvas.line(38, self.y + 10, fin_linea, self.y + 10)
            return self

        def agregar_totales(self):
            self.canvas.setFont("Times-Bold", 12)
            inicio_titulo, inicio_totales = 520, 525
            self.y -= 10
            self.canvas.drawRightString(inicio_titulo, self.y, "Subtotal:")
            self.canvas.drawString(inicio_totales, self.y, "${:,.0f}".format(self.subtotal_general))
            self.y -= 18
            self.canvas.drawRightString(inicio_titulo, self.y, "IVA Total:")
            self.canvas.drawString(inicio_totales, self.y, "${:,.0f}".format(self.iva_total))
            self.y -= 18

            metodo = Metodo_Pago.query.get(self.pedido.id_metodo)
            es_contraentrega = metodo and metodo.nombre.lower() in ['contraentrega', 'contra entrega', 'contra-entrega']

            total_label = "TOTAL A PAGAR:" if es_contraentrega else "TOTAL:"
            self.canvas.drawRightString(inicio_titulo, self.y, total_label)
            self.canvas.setFont("Times-Bold", 14)
            self.canvas.drawString(inicio_totales, self.y, "${:,.0f}".format(self.subtotal_general + self.iva_total))
            return self

        def agregar_pie_pagina(self):
            self.canvas.setFont("Times-Roman", 10)
            self.canvas.setFillColor(colors.darkblue)
            self.canvas.drawString(40, 35, f"Contacto Naylex Store: {self.config.contacto}")
            self.canvas.setFillColor(colors.black)
            return self

        def construir(self):
            self.canvas.showPage()
            self.canvas.save()
            self.buffer.seek(0)
            return self.buffer

    # ==========================================================
    # 🧩 CONTROLADOR PRINCIPAL (usa el Builder)
    # ==========================================================
    pedido = Pedido.query.get(id_pedido)
    if not pedido or not (1 <= pedido.id_estado_pedido <= 4):
        flash("Factura no disponible para este pedido.", "warning")
        return redirect(url_for('compras_bp.pedidos'))

    detalles = Detalle_Pedido.query.filter_by(id_pedido=id_pedido).all()

    builder = FacturaBuilder(pedido, detalles)
    pdf_buffer = (
        builder
        .agregar_encabezado()
        .agregar_tabla_productos()
        .agregar_totales()
        .agregar_pie_pagina()
        .construir()
    )

    return send_file(pdf_buffer, as_attachment=True,
                     download_name=f"Factura_Pedido_{pedido.id_pedido}.pdf",
                     mimetype='application/pdf')
