from werkzeug.security import check_password_hash


# ----------------------------------------
# Patrón INTERPRETER para validación de login
# ----------------------------------------

class Contexto:
    """Contiene el contexto del usuario que se intenta autenticar."""
    def __init__(self, usuario, password_introducido):
        self.usuario = usuario
        self.password_introducido = password_introducido


# ----------- Clases base del patrón -----------

class Expresion:
    """Interfaz base para todas las expresiones."""
    def interpretar(self, contexto):
        raise NotImplementedError("Debe implementarse el método interpretar().")


# ----------- Expresiones concretas -----------

class UsuarioExiste(Expresion):
    """Verifica que el usuario exista en la base de datos."""
    def interpretar(self, contexto):
        return contexto.usuario is not None


class ContraseñaCorrecta(Expresion):
    """Verifica que la contraseña ingresada sea correcta."""
    def interpretar(self, contexto):
        if not contexto.usuario:
            return False
        try:
            return check_password_hash(contexto.usuario.password, contexto.password_introducido)
        except Exception:
            return contexto.usuario.password == contexto.password_introducido


class UsuarioActivo(Expresion):
    """Verifica que el usuario tenga estado activo (1)."""
    def interpretar(self, contexto):
        if not contexto.usuario:
            return False
        return contexto.usuario.id_estado_usuario == 1


class EsCliente(Expresion):
    """Verifica que el usuario sea de tipo cliente (2)."""
    def interpretar(self, contexto):
        if not contexto.usuario:
            return False
        return contexto.usuario.id_tipo == 2


class LoginValido(Expresion):
    """Combina varias reglas de validación para el inicio de sesión."""
    def __init__(self, *reglas):
        self.reglas = reglas

    def interpretar(self, contexto):
        return all(regla.interpretar(contexto) for regla in self.reglas)
