# -*- coding: utf-8 -*-
# Módulo de Perfil del Usuario (Actualizar datos / Inactivar cuenta / Reactivar cuenta)

from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from tienda_virtual.models import db, Persona, Usuario

perfil_bp = Blueprint('perfil_bp', __name__)

# -------------------------------------------------------------------
# PERFIL: VER Y ACTUALIZAR DATOS
# -------------------------------------------------------------------
@perfil_bp.route('/perfil', methods=['GET', 'POST'])
def perfil():
    id_usuario = session.get('usuario_id')
    if not id_usuario:
        flash("Debes iniciar sesión para acceder a tu perfil.", "danger")
        return redirect(url_for('inicioSesion'))

    usuario = Usuario.query.get(id_usuario)
    persona = Persona.query.get(usuario.id_persona)

    if request.method == 'POST':
        # Capturar campos actualizados
        cc = request.form.get('cc', '').strip()
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        correo = request.form.get('correo', '').strip()
        telefono = request.form.get('telefono', '').strip()
        direccion = request.form.get('direccion', '').strip()

        # Validaciones de unicidad
        if cc and Persona.query.filter(Persona.cc == cc, Persona.id_persona != persona.id_persona).first():
            flash('La cédula ingresada ya está registrada para otro usuario.', 'warning')
        elif correo and Persona.query.filter(Persona.correo == correo, Persona.id_persona != persona.id_persona).first():
            flash('El correo electrónico ya está registrado para otro usuario.', 'warning')
        elif telefono and Persona.query.filter(Persona.telefono == telefono, Persona.id_persona != persona.id_persona).first():
            flash('El teléfono ya está registrado para otro usuario.', 'warning')
        else:
            # Solo actualizar si se digitó un valor nuevo
            if cc: persona.cc = cc
            if nombre: persona.nombre = nombre
            if apellido: persona.apellido = apellido
            if correo: persona.correo = correo
            if telefono: persona.telefono = telefono
            if direccion: persona.direccion = direccion

            try:
                db.session.commit()
                flash("✅ Datos actualizados correctamente.", "success")
            except Exception as e:
                db.session.rollback()
                print("❌ Error al actualizar perfil:", e)
                flash("Ocurrió un error al actualizar los datos.", "danger")

        return redirect(url_for('perfil_bp.perfil'))

    # Renderizar perfil con datos actuales
    return render_template('perfil.html', persona=persona, usuario=usuario)

# -------------------------------------------------------------------
# INACTIVAR CUENTA
# -------------------------------------------------------------------
@perfil_bp.route('/inactivar_cuenta', methods=['POST'])
def inactivar_cuenta():
    id_usuario = session.get('usuario_id')
    if not id_usuario:
        flash("Debes iniciar sesión primero.", "danger")
        return redirect(url_for('inicioSesion'))

    usuario = Usuario.query.get(id_usuario)
    if usuario:
        usuario.id_estado_usuario = 2  # 2 = inactivo
        try:
            db.session.commit()
            session.clear()  # Cierra la sesión automáticamente
            flash("⚠️ Tu cuenta ha sido inactivada. ¡Esperamos verte pronto!", "info")
        except Exception as e:
            db.session.rollback()
            print("❌ Error al inactivar cuenta:", e)
            flash("No se pudo inactivar la cuenta.", "danger")
    else:
        flash("Usuario no encontrado.", "danger")

    return redirect(url_for('inicioSesion'))

# -------------------------------------------------------------------
# REACTIVAR CUENTA
# -------------------------------------------------------------------
@perfil_bp.route('/reactivar_cuenta', methods=['GET', 'POST'])
def reactivar_cuenta():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        cc = request.form.get('cc', '').strip()
        correo = request.form.get('correo', '').strip()
        telefono = request.form.get('telefono', '').strip()

        usuario = None

        # Buscar por cualquiera de los datos
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
            if usuario.id_estado_usuario == 2:
                usuario.id_estado_usuario = 1
                db.session.commit()
                flash("✅ Cuenta reactivada con éxito. Ya puedes iniciar sesión.", "success")
                return redirect(url_for('inicioSesion'))
            else:
                flash("Tu cuenta ya está activa.", "info")
        else:
            flash("No se encontró ninguna cuenta con esos datos.", "danger")

    return render_template('reactivar_cuenta.html')
