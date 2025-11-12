# -*- coding: utf-8 -*-
# NAYLEX Store – Flask seguro (CSRF + CSP + Cookies + HSTS)

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, make_response, abort, g
)
from flask_mail import Mail, Message
from flask_talisman import Talisman
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta
import os, re, secrets

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

# -------------------------------------------------------------------------
# CONFIGURACIÓN BÁSICA DE LA APP
# -------------------------------------------------------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "cambia_esto_en_produccion")

IS_PROD = (
    os.environ.get("RENDER", "0") == "1" or
    os.environ.get("FLASK_ENV") == "production" or
    os.environ.get("ENV") == "production"
)

# ---------------------------- BASE DE DATOS ----------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = (
    os.environ.get("DATABASE_URL")
    or "postgresql+psycopg2://naylex_bd_iqap_user:19UWCPUfhiZHHyyLtLkxHEqVlhtldY1D"
       "@dpg-d46l3t2li9vc73at09c0-a.oregon-postgres.render.com/naylex_bd_iqap?sslmode=require"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ---------------------------- SESIÓN Y COOKIES ----------------------------
app.config.update(
    SESSION_COOKIE_SECURE=True if IS_PROD else False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)

# ---------------------------- BLUEPRINTS ----------------------------
db.init_app(app)
app.register_blueprint(productos_bp)
app.register_blueprint(carrito_compras_bp)
app.register_blueprint(compras_bp)
app.register_blueprint(perfil_bp)

# ---------------------------- CORREO ----------------------------
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", "587"))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "naylexstore@gmail.com")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "uyywbugfcsfyeaas")  # mover a variable de entorno en prod
app.config["MAIL_DEFAULT_SENDER"] = (
    os.environ.get("MAIL_DEFAULT_NAME", "NAYLEX Store"),
    os.environ.get("MAIL_DEFAULT_EMAIL", app.config["MAIL_USERNAME"]),
)
mail = Mail(app)

# -------------------------------------------------------------------------
# CABECERAS DE SEGURIDAD Y CSP (TALISMAN)
# -------------------------------------------------------------------------
CSP = {
    "default-src": ["'self'"],
    "img-src": ["'self'", "data:"],
    "script-src": ["'self'", "https://cdn.jsdelivr.net"],
    "style-src": ["'self'", "https://cdn.jsdelivr.net"],
    "font-src": ["'self'", "https://cdn.jsdelivr.net", "data:"],
    "connect-src": ["'self'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "frame-ancestors": ["'none'"],
}

talisman = Talisman(
    app,
    content_security_policy=CSP,
    content_security_policy_nonce_in=["script-src"],
    force_https=True if IS_PROD else False,
    strict_transport_security=True if IS_PROD else False,
    strict_transport_security_max_age=31536000,
    frame_options="DENY",
    referrer_policy="strict-origin-when-cross-origin",
    x_content_type_options=True,
)

@app.context_processor
def security_ctx():
    def _csp_nonce():
        return getattr(g, "csp_nonce", "")
    return {"csp_nonce": _csp_nonce}

@app.after_request
def add_security_headers(resp):
    resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")
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
# RUTAS
# -------------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def inicioSesion():
    if request.method == "POST":
        username = (request.form.get("nombreUsuario") or "").strip()
        password = (request.form.get("contrasena") or "").strip()

        if not username or not password:
            flash("Usuario y contraseña son obligatorios.", "danger")
            return render_template("inicioSesion.html", hide_navbar=True)

        usuario = Usuario.query.filter_by(username=username).first()
        contexto = Contexto(usuario, password)
        reglas_login = LoginValido(UsuarioExiste(), ContraseñaCorrecta(), UsuarioActivo(), EsCliente())

        if not reglas_login.interpretar(contexto):
            if not UsuarioExiste().interpretar(contexto):
                flash("El usuario no existe en el sistema.", "danger")
            elif not ContraseñaCorrecta().interpretar(contexto):
                flash("Contraseña incorrecta. Intente nuevamente.", "danger")
            elif not UsuarioActivo().interpretar(contexto):
                flash("Su cuenta está inactiva. Debe reactivarla para ingresar.", "warning")
            elif not EsCliente().interpretar(contexto):
                tipo = {1: "Administrador", 3: "Vendedor"}.get(usuario.id_tipo, "Usuario")
                flash(f"El usuario '{usuario.username}' está registrado como {tipo}.", "info")
            return render_template("inicioSesion.html", hide_navbar=True)

        session.clear()
        session.permanent = True
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


@app.route("/recuperar_contrasena")
def recuperar_contrasena():
    return render_template("recuperar_contrasena.html", hide_navbar=True)


@app.route("/registro_usuario", methods=["GET", "POST"])
def registro_usuario():
    if request.method == "GET":
        _get_csrf_token()

    if request.method == "POST":
        # (igual que antes)
        ...
    return render_template("registro_usuario.html", hide_navbar=True, datos_anteriores={})


@app.route("/restaurar_contrasena/<token>", methods=["GET", "POST"])
def restaurar_contrasena(token):
    correo = verificar_token(token)
    if not correo:
        flash("El enlace de recuperación ha expirado o es inválido.")
        return redirect(url_for("inicioSesion"))

    if request.method == "POST":
        ...
    return render_template("restaurar_contrasena.html", correo=correo, hide_navbar=True)


@app.route("/cerrar_Sesion")
def cerrar_Sesion():
    session.clear()
    flash("Sesión cerrada correctamente.")
    return redirect(url_for("inicioSesion"))

# -------------------------------------------------------------------------
# RUN
# -------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=not IS_PROD)
