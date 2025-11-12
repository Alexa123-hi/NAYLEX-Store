/* Auto-ocultar flashes */
document.addEventListener("DOMContentLoaded", function(){
  const flash = document.getElementById("mensaje-flash");
  if (flash){ setTimeout(()=> flash.style.display = "none", 3000); }

  /* Confirm genérico para botones/FORMs con data-confirm */
  document.querySelectorAll("[data-confirm]").forEach(el=>{
    el.addEventListener("submit", function(e){
      const msg = this.getAttribute("data-confirm");
      if (!window.confirm(msg)) e.preventDefault();
    });
    el.addEventListener("click", function(e){
      // por si el atributo está en un <a> o <button>
      const msg = this.getAttribute("data-confirm");
      if (msg && !window.confirm(msg)) e.preventDefault();
    });
  });

  /* Mostrar campos según método de pago */
  const selMetodo = document.getElementById("metodo");
  const tarjeta = document.getElementById("datos-tarjeta");
  const pse = document.getElementById("datos-pse");

  function mostrarCamposPago(){
    if (!selMetodo || !tarjeta || !pse) return;
    const selectedText = selMetodo.options[selMetodo.selectedIndex] ? selMetodo.options[selMetodo.selectedIndex].text.trim() : "";
    tarjeta.classList.add("hidden");
    pse.classList.add("hidden");
    document.querySelectorAll("#datos-tarjeta input, #datos-pse input").forEach(i=>i.required=false);

    if (selectedText === "Tarjeta de Crédito"){
      tarjeta.classList.remove("hidden");
      document.querySelectorAll("#datos-tarjeta input").forEach(i=>i.required=true);
    } else if (selectedText === "PSE" || selectedText === "Transferencia PSE"){
      pse.classList.remove("hidden");
      document.querySelectorAll("#datos-pse input").forEach(i=>i.required=true);
    }
  }
  if (selMetodo){ selMetodo.addEventListener("change", mostrarCamposPago); mostrarCamposPago(); }
});
