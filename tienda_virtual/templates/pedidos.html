{% extends 'base.html' %}
{% block title %}Pedidos{% endblock %}

{% block head %}
<style>
/* ================== ESTILOS DE PEDIDOS ================== */
.contenedor-pedidos {
  width: 95%;
  max-width: 950px;
  margin: 40px auto 80px auto;
}

/* Tarjeta del pedido */
.pedido-card {
  background-color: #fff;
  border: 1px solid var(--borde);
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 12px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
}

.pedido-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  transform: scale(1.01);
}

/* Columna 1: número y fecha */
.pedido-info {
  font-size: 16px;
  font-weight: 500;
  color: #000;
  margin: 3px 0;
}

/* Columna 2: estado */
.estado {
  font-weight: bold;
  font-size: 15px;
  margin: 3px 0;
}

.badge-estado {
  padding: 5px 10px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-left: 5px;
}

.estado-pendiente { background-color: #FFD700; color: #000; }
.estado-procesado { background-color: #00BFFF; }
.estado-enviado   { background-color: #00008B; }
.estado-entregado { background-color: #28a745; }
.estado-cancelado { background-color: #6c757d; }

/* Columna 3: botones */
.botones-pedido {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-nx {
  border-radius: 8px;
  padding: 5px 12px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.btn-detalle {
  color: var(--azul);
  border: 2px solid var(--azul);
  background: #fff;
}

.btn-detalle:hover {
  background: var(--azul);
  color: #fff;
}

.btn-factura {
  color: #b30000;
  border: 2px solid #b30000;
  background: #fff;
}

.btn-factura:hover {
  background: #b30000;
  color: #fff;
}

/* Mensaje sin pedidos */
.no-pedidos {
  text-align: center;
  background: #eaf4ff;
  color: #0d3a68;
  border-radius: 10px;
  padding: 15px;
  margin: 30px auto;
  width: fit-content;
  font-weight: 500;
}

/* Footer */
footer {
  text-align: center;
  color: #fff;
  background-color: var(--azul);
  padding: 10px 0;
  font-weight: 500;
  border-top: 3px solid var(--dorado);
}
</style>
{% endblock %}

{% block content %}
<div class="contenedor-pedidos">
  {% if pedidos %}
    {% for pedido in pedidos %}
    <div class="pedido-card">
      
      <div class="pedido-info">
        🧾 <b>#{{ pedido.id_pedido }}</b> &nbsp;&nbsp;
        📅 <b>Fecha:</b> {{ pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M') }}
      </div>

      <div class="estado">
        🚦 <b>Estado:</b>
        <span class="badge-estado 
          {% if pedido.estado_pedido.estado == 'Pendiente' %} estado-pendiente
          {% elif pedido.estado_pedido.estado == 'Procesado' %} estado-procesado
          {% elif pedido.estado_pedido.estado == 'Enviado' %} estado-enviado
          {% elif pedido.estado_pedido.estado == 'Entregado' %} estado-entregado
          {% else %} estado-cancelado {% endif %}">
          {{ pedido.estado_pedido.estado }}
        </span>
      </div>

      <div class="botones-pedido">
        <a href="{{ url_for('compras_bp.detalle_pedido', id_pedido=pedido.id_pedido) }}" class="btn-nx btn-detalle">
          📊 Ver detalles
        </a>

        {% if 1 <= pedido.id_estado_pedido <= 4 %}
        <a href="{{ url_for('compras_bp.factura', id_pedido=pedido.id_pedido) }}" class="btn-nx btn-factura" target="_blank">
          🧾 Factura
        </a>
        {% endif %}
      </div>

    </div>
    {% endfor %}
  {% else %}
    <div class="no-pedidos">😔 No tienes pedidos realizados.</div>
  {% endif %}
</div>

<footer>
  Tienda Virtual del Sistema de Inventario TechSolutions
</footer>
{% endblock %}
