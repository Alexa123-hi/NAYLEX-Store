from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db, Persona, Usuario


perfil_bp = Blueprint('perfil_bp', __name__)

@perfil_bp.route('/perfil', methods=['GET', 'POST'])
def perfil():
    id_usuario = session.get('usuario_id')
    if not id_usuario:
        flash("Debes iniciar sesión para acceder a tu perfil.", "danger")
        return redirect(url_for('inicioSesion'))

    usuario = Usuario.query.get(id_usuario)
    persona = Persona.query.get(usuario.id_persona)

    # Por defecto, toma los datos actuales de la base de datos
    datos = {
        'cc': persona.cc,
        'nombre': persona.nombre,
        'apellido': persona.apellido,
        'correo': persona.correo,
        'telefono': persona.telefono,
        'direccion': persona.direccion
    }

    if request.method == 'POST':
        # Toma los datos que el usuario intentó enviar para validarlos
        cc = request.form.get('cc', '').strip()
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        correo = request.form.get('correo', '').strip()
        telefono = request.form.get('telefono', '').strip()
        direccion = request.form.get('direccion', '').strip()
        datos = {
            'cc': cc,
            'nombre': nombre,
            'apellido': apellido,
            'correo': correo,
            'telefono': telefono,
            'direccion': direccion
        }

        existe_cc = Persona.query.filter(Persona.cc == cc, Persona.id_persona != persona.id_persona).first()
        existe_correo = Persona.query.filter(Persona.correo == correo, Persona.id_persona != persona.id_persona).first()
        existe_telefono = Persona.query.filter(Persona.telefono == telefono, Persona.id_persona != persona.id_persona).first()

        if existe_cc:
            flash('La cédula ingresada ya está registrada para otro usuario.', 'warning')
        elif existe_correo:
            flash('El correo electrónico ya está registrado para otro usuario.', 'warning')
        elif existe_telefono:
            flash('El teléfono ya está registrado para otro usuario.', 'warning')
        else:
            # Actualiza solo si pasa validación
            persona.cc = cc
            persona.nombre = nombre
            persona.apellido = apellido
            persona.correo = correo
            persona.telefono = telefono
            persona.direccion = direccion
            db.session.commit()
            flash("¡Datos actualizados con éxito!", "success")
            # Luego de actualizar, carga los datos guardados en la base de datos
            datos = {
                'cc': persona.cc,
                'nombre': persona.nombre,
                'apellido': persona.apellido,
                'correo': persona.correo,
                'telefono': persona.telefono,
                'direccion': persona.direccion
            }

    return render_template('perfil.html', persona=persona, usuario=usuario, datos=datos)

#---------------------------------------------------------------------------------------------------------
#------------------------------Dejar cuenta Inactiva-----------------------------------------------------------
@perfil_bp.route('/inactivar_cuenta', methods=['POST'])
def inactivar_cuenta():
    id_usuario = session.get('usuario_id')
    if not id_usuario:
        flash("Debes iniciar sesión.", "danger")
        return redirect(url_for('inicioSesion')) # validación de que haya iniciado sesión antes de entrar al perfil

    usuario = Usuario.query.get(id_usuario)
    if usuario:
        usuario.id_estado_usuario = 2  # 2 = inactivo
        db.session.commit()
        flash("Tu cuenta ha sido inactivada. ¡Esperamos verte pronto!", "info")
        return redirect(url_for('cerrar_Sesion'))
    else:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for('perfil_bp.perfil'))


#---------------------------------------------------------------------------------------------------------
#------------------------------Reactivar la cuenta-----------------------------------------------------------
@perfil_bp.route('/reactivar_cuenta', methods=['GET', 'POST'])
def reactivar_cuenta():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        cc = request.form.get('cc', '').strip()
        correo = request.form.get('correo', '').strip()
        telefono = request.form.get('telefono', '').strip()

        usuario = None

        # Búsqueda de los datos segun lo digitado 
        if username:
            usuario = Usuario.query.filter_by(username=username).first()
        elif cc:
            persona = Persona.query.filter_by(cc=cc).first()
            if persona:
                usuario = Usuario.query.filter_by(id_persona=persona.id_persona).first()
        elif telefono:
            persona = Persona.query.filter_by(telefono=telefono).first()
            if persona:
                usuario = Usuario.query.filter_by(id_persona=persona.id_persona).first()
        elif correo:
            persona = Persona.query.filter_by(correo=correo).first()
            if persona:
                usuario = Usuario.query.filter_by(id_persona=persona.id_persona).first()

        if usuario:
            if usuario.id_estado_usuario == 2:  # inactivo
                usuario.id_estado_usuario = 1   # Se activa la cuenta y se guarda el cambio en la base de datos
                db.session.commit()
                flash("¡Cuenta reactivada con éxito! Ya puedes iniciar sesión.", "success")
                return redirect(url_for('inicioSesion'))
            else:
                flash("Tu cuenta ya está activa.", "info")
        else:
            flash("No se encontró ninguna cuenta con esos datos.", "danger")
    return render_template('reactivar_cuenta.html')
