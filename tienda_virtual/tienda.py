# -*- coding: utf-8 -*-
# NAYLEX Store – Flask seguro (CSRF + CSP + Cookies + HSTS + Recuperación y Reactivación de cuenta)

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, make_response, abort, g
)
from flask_talisman import Talisman
from itsdangerous import URLSafeTimedSerializer
from datetime import timedelta
import os, secrets

# ---------------------------- MÓDULOS PROPIOS ----------------------------
from tienda_virtual import db
from tienda_virtual.Carrito_compras import carrito_compras_bp
from tienda_virtual.productos import productos_bp
from tienda_virtual.Compras import compras_bp
from tienda_virtual.perfil import perfil_bp
from tienda_virtual.models import Persona, Usuario, Cliente
from tienda_virtual.login_interpreter import (
    Contexto, UsuarioExiste, ContraseñaCorrecta, UsuarioActivo, EsCliente, LoginValido
)
from tienda_virtual.email_sender import enviar_correo  # 📩 integrado con Brevo

# -------------------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# -------------------------------------------------------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "clave_segura_dev")

IS_PROD = os.environ.get("RENDER", "0") == "1"

# -------------------------------------------------------------------------
# BASE DE DATOS
# -------------------------------------------------------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# -------------------------------------------------------------------------
# SESIÓN Y COOKIES
# -------------------------------------------------------------------------
app.config.update(
    SESSION_COOKIE_SECURE=IS_PROD,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)

# -------------------------------------------------------------------------
# BLUEPRINTS
# -------------------------------------------------------------------------
db.init_app(app)
app.register_blueprint(productos_bp)
app.register_blueprint(carrito_compras_bp)
app.register_blueprint(compras_bp)
app.register_blueprint(perfil_bp)

# -------------------------------------------------------------------------
# CABECERAS DE SEGURIDAD (Talisman)
# -------------------------------------------------------------------------
CSP = {
    "default-src": ["'self'"],
    "img-src": ["'self'", "data:"],
    "script-src": ["'self'"],
    "style-src": ["'self'"],
    "font-src": ["'self'", "data:"],
    "connect-src": ["'self'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "frame-ancestors": ["'none'"],
}

Talisman(
    app,
    content_security_policy=CSP,
    force_https=IS_PROD,
    strict_transport_security=IS_PROD,
    strict_transport_security_max_age=31536000,
    frame_options="DENY",
    referrer_policy="strict-origin-when-cross-origin",
)

@app.after_request
def add_security_headers(resp):
    resp.headers.setdefault("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
    resp.headers.setdefault("Pragma", "no-cache")
    resp.headers.setdefault("Expires", "0")
    return resp

# -------------------------------------------------------------------------
# CSRF
# -------------------------------------------------------------------------
def _get_csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token

@app.before_request
def _ensure_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)

def _validate_csrf():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        form_token = request.form.get("_csrf_token") or request.headers.get("X-CSRF-Token")
        sess_token = session.get("_csrf_token")
        if not form_token or not sess_token or form_token != sess_token:
            abort(400, description="CSRF token inválido o ausente")

@app.before_request
def _csrf_protect_hook():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        _validate_csrf()

app.jinja_env.globals["csrf_token"] = _get_csrf_token

# -------------------------------------------------------------------------
# INICIO DE SESIÓN
# -------------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def inicioSesion():
    if request.method == "POST":
        username = request.form.get("nombreUsuario", "").strip()
        password = request.form.get("contrasena", "").strip()

        if not username or not password:
            flash("Usuario y contraseña son obligatorios.", "danger")
            return render_template("inicioSesion.html", hide_navbar=True)

        usuario = Usuario.query.filter_by(username=username).first()
        contexto = Contexto(usuario, password)
        reglas_login = LoginValido(UsuarioExiste(), ContraseñaCorrecta(), UsuarioActivo(), EsCliente())

        if not reglas_login.interpretar(contexto):
            flash("Credenciales incorrectas o usuario inactivo.", "danger")
            return render_template("inicioSesion.html", hide_navbar=True)

        session.clear()
        session["usuario_id"] = usuario.id_usuario
        session["usuario_nombre"] = usuario.username
        cliente = Cliente.query.filter_by(id_usuario=usuario.id_usuario).first()
        if cliente:
            session["id_cliente"] = cliente.id_cliente
        flash(f"¡Bienvenido {usuario.username}!", "success")
        return redirect(url_for("inicio"))

    return render_template("inicioSesion.html", hide_navbar=True)

@app.route("/inicio")
def inicio():
    if "usuario_id" in session:
        return make_response(render_template("inicio.html"))
    flash("Debes iniciar sesión primero.")
    return redirect(url_for("inicioSesion"))

# -------------------------------------------------------------------------
# RECUPERAR Y RESTAURAR CONTRASEÑA (con Brevo)
# -------------------------------------------------------------------------
@app.route("/recuperar_contrasena", methods=["GET", "POST"])
def recuperar_contrasena():
    if request.method == "POST":
        correo_usuario = (request.form.get("correo") or "").strip()
        nombre_usuario = (request.form.get("username") or "").strip()
        telefono_usuario = (request.form.get("telefono") or "").strip()

        persona = None
        correo_destino = None

        # Buscar usuario por correo, username o teléfono
        if correo_usuario:
            persona = Persona.query.filter_by(correo=correo_usuario).first()
            if persona:
                correo_destino = correo_usuario
        if not persona and nombre_usuario:
            usuario = Usuario.query.filter_by(username=nombre_usuario).first()
            if usuario:
                persona = Persona.query.filter_by(id_persona=usuario.id_persona).first()
                if persona:
                    correo_destino = persona.correo
        if not persona and telefono_usuario:
            persona = Persona.query.filter_by(telefono=telefono_usuario).first()
            if persona:
                correo_destino = persona.correo

        if persona and correo_destino:
            s = URLSafeTimedSerializer(app.secret_key)
            token = s.dumps(correo_destino, salt="recuperacion-clave")
            enlace = url_for("restaurar_contrasena", token=token, _external=True)

            html = f"""
            <h2 style='color:#0044cc'>NAYLEX Store</h2>
            <p>Hola {persona.nombre},</p>
            <p>Haz clic para restablecer tu contraseña:</p>
            <a href="{enlace}" style='background:#0066ff;color:white;padding:10px 20px;text-decoration:none;border-radius:8px;'>Restablecer contraseña</a>
            <p>El enlace expirará en 1 hora.</p>
            """

            ok = enviar_correo(
                destinatario=correo_destino,
                asunto="🔑 Recuperación de contraseña - NAYLEX Store",
                html=html,
                texto=f"Restablece tu contraseña aquí: {enlace}"
            )
            if ok:
                flash(f"✅ Se enviaron instrucciones a {correo_destino}.", "success")
            else:
                flash("⚠️ No se pudo enviar el correo en este momento.", "warning")
            return redirect(url_for("inicioSesion"))
        else:
            flash("⚠️ No se encontró ningún registro con esos datos.", "danger")

    return render_template("recuperar_contrasena.html", hide_navbar=True)


@app.route("/restaurar_contrasena/<token>", methods=["GET", "POST"])
def restaurar_contrasena(token):
    s = URLSafeTimedSerializer(app.secret_key)
    try:
        correo = s.loads(token, salt="recuperacion-clave", max_age=3600)
    except Exception:
        flash("El enlace ha expirado o no es válido.", "danger")
        return redirect(url_for("inicioSesion"))

    if request.method == "POST":
        nueva_password = (request.form.get("nueva_password") or "").strip()
        if len(nueva_password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "warning")
            return render_template("restaurar_contrasena.html", correo=correo, hide_navbar=True)

        persona = Persona.query.filter_by(correo=correo).first()
        usuario = Usuario.query.filter_by(id_persona=persona.id_persona).first()

        if usuario:
            usuario.password = nueva_password  # ⚠️ en prod: usa hash
            db.session.commit()
            flash("Tu contraseña fue actualizada exitosamente.", "success")
            return redirect(url_for("inicioSesion"))
        flash("No se pudo actualizar la contraseña.", "danger")

    return render_template("restaurar_contrasena.html", correo=correo, hide_navbar=True)

# -------------------------------------------------------------------------
@app.route("/cerrar_Sesion")
def cerrar_Sesion():
    session.clear()
    flash("Sesión cerrada correctamente.")
    return redirect(url_for("inicioSesion"))

# -------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=not IS_PROD)
