// Muestra solo los campos que aplican al tipo de pedido elegido.
(function () {
  var tipo = document.getElementById('id_tipo');
  if (!tipo) return;
  var bloques = document.querySelectorAll('[data-tipos]');
  function actualizar() {
    bloques.forEach(function (b) {
      b.hidden = b.dataset.tipos.split(' ').indexOf(tipo.value) === -1;
    });
  }
  tipo.addEventListener('change', actualizar);
  actualizar();
})();
