/* ======== FLASH (auto-ocultar desde app.js) ======== */
#mensaje-flash { transition: opacity .25s ease; }

/* ======== FORMULARIOS GENÉRICOS ======== */
.form-card{
  background:#fff; border:2px solid var(--borde); border-radius:14px;
  padding:18px 20px; box-shadow:0 6px 22px rgba(0,0,80,.06);
}
.input-row{
  display:grid; grid-template-columns: 160px 1fr; gap:8px 12px;
  align-items:center; margin-bottom:12px;
}
.input-row > label{ font-weight:600; color:#142879; }
.input-row input, .input-row select{
  width:100%; border:2px solid #000; border-radius:8px;
  padding:8px 10px; font-size:1rem; outline:none;
  font-family:'Times New Roman', Times, serif; background:#fff; color:#000;
}
.input-row input:focus, .input-row select:focus{
  border-color:#2468db; box-shadow:0 0 0 3px rgba(36,104,219,.15);
}
label.required::after{ content:" *"; color:#B22222; }

/* ======== MÉTODO DE PAGO (controlado por JS) ======== */
#metodo{
  border:2px solid var(--azul); border-radius:8px; padding:8px 10px;
  font-size:1rem; background:#fff; color:#000; width:100%;
}
#datos-tarjeta, #datos-pse{
  margin-top:12px; padding:14px; border:2px dashed var(--borde);
  border-radius:10px; background:#fafbff; transition:max-height .25s ease, opacity .2s ease;
}
#datos-tarjeta.hidden, #datos-pse.hidden{ display:none !important; }
.pay-field{ display:grid; grid-template-columns: 150px 1fr; gap:8px 12px; align-items:center; margin-bottom:10px; }
.pay-field input{
  width:100%; border:2px solid #000; border-radius:8px; padding:8px 10px;
  font-size:1rem; background:#fff; color:#000; outline:none;
}
.pay-hint{ font-size:.9rem; color:#4a4a4a; }

/* ======== RECUPERAR / REESTABLECER CONTRASEÑA ======== */
.recovery-form{
  background: linear-gradient(145deg, #0000CD, #00008B);
  padding: 40px 30px; border-radius: 15px; text-align: center; width: 350px;
  color: #fff; box-shadow: 0 4px 12px rgba(0,0,0,.5); border: 10px double #fff;
}
.recovery-form h2{ margin:0 0 12px 0; font-size:30px; }
.recovery-form h1{ margin:6px 0 16px 0; color:#FFD700; font-size:18px; }
.recovery-form input[type="password"],
.recovery-form input[type="email"],
.recovery-form input[type="text"]{
  width: 95%; padding: 8px 10px; border: 4px solid #000; border-radius: 8px;
  font-size: 18px; margin: 6px 0 10px 0; background:#fff; color:#000;
  font-family:'Times New Roman', Times, serif; outline:none;
}
.recovery-form input[type="password"]:focus,
.recovery-form input[type="email"]:focus,
.recovery-form input[type="text"]:focus{
  border-color:#2468db; box-shadow:0 0 0 3px rgba(36,104,219,.15);
}
.recovery-form input[type="submit"],
.recovery-form .btn-nx{
  background:#4CAF50; border:5px double #000; color:#fff; padding:8px 20px;
  font-size:20px; border-radius:8px; cursor:pointer; width:90%; transition:background .3s;
  font-family:'Times New Roman', Times, serif; margin-top:8px;
}
.recovery-form input[type="submit"]:hover,
.recovery-form .btn-nx:hover{ background:#45a049; }

/* ======== UTILIDADES ======== */
.hidden{ display:none !important; } /* usada por app.js */
