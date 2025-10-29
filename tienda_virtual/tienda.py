#C ORRER CODIGO flask --app tienda.py --debug run y Ctrol shif p para el auto save
#request =información que viene del cliente

from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
from datetime import datetime
from tienda_virtual import db
from tienda_virtual.Carrito_compras import carrito_compras_bp
from tienda_virtual.productos import productos_bp
from tienda_virtual.Compras import compras_bp
from tienda_virtual.perfil import perfil_bp
import re
import os


app = Flask(__name__)
app.secret_key = 'clave_proyecto' 


#Conexión base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# # Conexión a la base de datos (Render o local)
# if 'DATABASE_URL' in os.environ:
#     app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
# else:
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Alexa_0511@localhost:5432/Aplicacion_Escritorio'

# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# #Conexion a la base de datos
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Alexa_0511@localhost:5432/Aplicacion_Escritorio'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialización 
db.init_app(app) 
# Importar modelos (después de db.init_app)
from tienda_virtual.models import Persona, Usuario, Cliente, Producto

#conexión con los otros archivos.py
app.register_blueprint(productos_bp)
app.register_blueprint(carrito_compras_bp)
app.register_blueprint(compras_bp)
app.register_blueprint(perfil_bp)


@app.route('/', methods=['GET', 'POST'])
def inicioSesion():
    if request.method == 'POST':
        username = request.form['nombreUsuario']
        password = request.form['contrasena']

        usuario = Usuario.query.filter_by(username=username, password=password).first()

        if usuario:
            # Validar estado del usuario
            if usuario.id_estado_usuario != 1:  # 1 = Activo 
                flash("Su cuenta está inactiva. Debe activar nuevamente la cuenta para ingresar.")
                return redirect(url_for('inicioSesion'))

            if usuario.id_tipo == 2:  # 2=cliente
                session['usuario_id'] = usuario.id_usuario
                session['usuario_nombre'] = usuario.username
                # Buscar el cliente relacionado y guardar su id en sesión para usarlo en el registro de compras
                cliente = Cliente.query.filter_by(id_usuario=usuario.id_usuario).first()
                if cliente:
                    session['id_cliente'] = cliente.id_cliente
                flash(f'¡Bienvenido {usuario.username}!')
                print("ID USUARIO: ", session.get('usuario_id'))
                print("ID CLIENTE: ", session.get('id_cliente'))   #Para corroborar que se guarden los datos
                return redirect(url_for('inicio'))
            else:
                tipo = {1: "Administrador", 3: "Vendedor"}.get(usuario.id_tipo, "Usuario") #Para que no acepte encargados de la tienda fisica ya que genera problemas con la aplicación de escritorio
                flash(f"El usuario '{usuario.username}' está registrado como {tipo}.")
                flash("Por favor, registrese como cliente para usar la tienda virtual.")
                return redirect(url_for('inicioSesion'))
        else:
            flash('Usuario o contraseña incorrectos.')
            flash('Intentelo Nuevamente.')
            return redirect(url_for('inicioSesion'))
        
    return render_template('inicioSesion.html')



@app.route('/inicio') #primer template al ingresar
def inicio():
    if 'usuario_id' in session:
        response = make_response(render_template('inicio.html'))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" #Borrar las url anteriores para que inicie sesión antes de seguir
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    else:
        flash('Debes iniciar sesión primero.')
        return redirect(url_for('inicioSesion'))
    
def base():
    return render_template('base.html')

# ----------------------------------------------------------------------------------------------------------------
# ----------------------------------RECUPERACION/CAMBIO DE CONTRASEÑA---------------------------------------------------
@app.route('/recuperar_contrasena')
def recuperar_contrasena():
    return render_template('recuperar_contrasena.html')

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'naylexstore@gmail.com'   # Email
app.config['MAIL_PASSWORD'] = 'uyywbugfcsfyeaas'      # contraseña de aplicacion (la da google al inscribir el correo)
app.config['MAIL_DEFAULT_SENDER'] = ('NAYLEX Store', 'naylexstore@gmail.com')

mail = Mail(app)

def generar_token(correo):# el boton o tocken unico para recuperar la contraseña
    s = URLSafeTimedSerializer(app.secret_key)
    return s.dumps(correo, salt='recuperacion-clave')

def verificar_token(token, max_age=3600): #verifica que aun sirva
    s = URLSafeTimedSerializer(app.secret_key)
    try:
        correo = s.loads(token, salt='recuperacion-clave', max_age=max_age)
        return correo
    except Exception:
        return None
    
# ----------------------------------------------------------------------------------------------------------------    
#-------------------Template para enviar el correo de recuperación---------------------------------
@app.route('/enviar_instrucciones', methods=['POST']) 
def enviar_instrucciones():
    correo_usuario = request.form['correo']
    nombre_usuario = request.form['username']
    telefono_usuario = request.form['telefono']

    persona = None
    correo_destino = None

    if not (correo_usuario or nombre_usuario or telefono_usuario):
        flash('Debes ingresar al menos uno de los tres campos para recibir el correo de recuperación.')
        return redirect(url_for('recuperar_contrasena'))

    # Buscar por correo
    if correo_usuario:
        persona = Persona.query.filter_by(correo=correo_usuario).first()
        if persona:
            correo_destino = correo_usuario

    # Buscar por nombre de usuario
    if not persona and nombre_usuario:
        usuario = Usuario.query.filter_by(username=nombre_usuario).first()
        if usuario:
            print(f"Usuario encontrado: {usuario.username}")
            persona = Persona.query.filter_by(id_persona=usuario.id_persona).first()
            if persona:
                correo_destino = persona.correo
                print(f"Persona encontrada con correo: {correo_destino}")
            else:
                print("Persona no encontrada con ese id_persona")
        else:
            print("Usuario no encontrado")

    # Buscar por teléfono
    if not persona and telefono_usuario:
        persona = Persona.query.filter_by(telefono=telefono_usuario).first()
        if persona:
            correo_destino = persona.correo

    if persona and correo_destino: #mensaje del correo
        token = generar_token(correo_destino)
        enlace = url_for('restaurar_contrasena', token=token, _external=True)

        msg = Message('Recuperación de contraseña - NAYLEX Store', recipients=[correo_destino])
        msg.html = f"""
        <h2 style="color: #00008B;">Naylex Store - Recuperación de Contraseña</h2>
        <p>Hola,</p>
        <p>Hemos recibido una solicitud para restablecer tu contraseña.</p>
        <p><a href="{enlace}" style="background-color: #4CAF50; padding: 10px 20px; color: white; text-decoration: none; font-size: 18px; border-radius: 8px;">Restablecer contraseña</a></p>
        <p>Este enlace expirará en 1 hora.</p>
        <p>Si tú no solicitaste este cambio, ignora este correo.</p>
        """
        mail.send(msg)
        flash(f'Se han enviado instrucciones de recuperación a {correo_destino}.')
        return redirect(url_for('inicioSesion'))

    flash('No se encontró ningún registro con los datos ingresados.')
    return redirect(url_for('recuperar_contrasena'))

# ----------------------------------------------------------------------------------------------------------------
#-----------------------------------Template despues de ingresar al token------------------------------------

@app.route('/restaurar_contrasena/<token>', methods=['GET', 'POST'])
def restaurar_contrasena(token):
    correo = verificar_token(token)

    if not correo:
        flash('El enlace de recuperación ha expirado o es inválido.')
        return redirect(url_for('inicioSesion'))

    if request.method == 'POST':
        nueva_password = request.form['nueva_password']

        persona = Persona.query.filter_by(correo=correo).first()
        usuario = Usuario.query.filter_by(id_persona=persona.id_persona).first()

        if usuario:
            usuario.password = nueva_password
            db.session.commit()
            flash('Tu contraseña fue actualizada exitosamente.')
            return redirect(url_for('inicioSesion'))
        else:
            flash('No se pudo actualizar la contraseña.')

    return render_template('restaurar_contrasena.html', correo=correo)


# ----------------------------------------------------------------------------------------------------------------
# --------------------------------------REGISTRO USUARIO----------------------------------------------------------------
@app.route('/registro_usuario', methods=['GET', 'POST'])
def registro_usuario():
    if request.method == 'POST':
        cc = request.form['cc'] 
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        username = request.form['username']
        password = request.form['password']
        

        try:
            # Validaciones antes de registrar
            existe_cc = Persona.query.filter_by(cc=cc).first()
            existe_correo = Persona.query.filter_by(correo=correo).first()
            existe_telefono = Persona.query.filter_by(telefono=telefono).first()
            existe_username = Usuario.query.filter_by(username=username).first()

            if len(password) < 6:
                flash('La contraseña debe tener al menos 6 caracteres.', 'warning')
                return render_template('registro_usuario.html', datos_anteriores=request.form)

            if existe_cc:
                flash('La cédula ingresada ya está registrada.', 'warning')
                return render_template('registro_usuario.html', datos_anteriores=request.form)

            if existe_correo:
                flash('El correo electrónico ya está registrado.', 'warning')
                return render_template('registro_usuario.html', datos_anteriores=request.form)

            if existe_telefono:
                flash('El teléfono ya está registrado.', 'warning')
                return render_template('registro_usuario.html', datos_anteriores=request.form)

            if existe_username:
                flash('El nombre de usuario ya está en uso.', 'warning')
                return render_template('registro_usuario.html', datos_anteriores=request.form)
            
            
            # Registro en base de datos despues de validar
            nueva_persona = Persona(
                cc=cc,
                nombre=nombre,
                apellido=apellido,
                correo=correo,
                telefono=telefono,
                direccion=direccion
            )
            db.session.add(nueva_persona)
            db.session.commit()

            nuevo_usuario = Usuario(
                id_persona=nueva_persona.id_persona,
                username=username,
                password=password,
                id_tipo=2,  # Cliente
                id_estado_usuario=1,
                fecha_creacion=datetime.now()
            )
            db.session.add(nuevo_usuario)
            db.session.commit()

            nuevo_cliente = Cliente(
                id_persona=nueva_persona.id_persona,
                fecha_registro=datetime.now(),
                id_usuario=nuevo_usuario.id_usuario,
                id_estado_cliente=1
            )
            db.session.add(nuevo_cliente)
            db.session.commit()

            flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('inicioSesion'))
            

        except Exception as e:
            db.session.rollback()
            # print(f'Error en el registro: {str(e)}', 'danger')
           
    return render_template('registro_usuario.html', datos_anteriores={})

# ----------------------------------------------------------------------------------------------------------------
# --------------------------------------Cerrar sesión en el sistema----------------------------------------------------------------
@app.route('/cerrar_Sesion')
def cerrar_Sesion():
    session.clear()
    flash('Sesión cerrada correctamente.')
    return redirect(url_for('inicioSesion'))



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=2000, debug=True)


# if __name__ == "__main__":
#     app.run(debug=True)
#   informacionip_usuario= request.remote_addr //dirección ip del que consulta
# el request contiene todo lo que se envia desde el navegador al servidor