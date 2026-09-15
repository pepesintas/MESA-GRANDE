/* ═══════════════════════════════════════════════════════════
   Apariciones escalonadas al entrar en pantalla.
   Menos de 1 KB. Sin librerías y sin peticiones de red.

   Si el usuario prefiere menos movimiento, no hace nada y la
   página se ve entera desde el principio.
   ═══════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var quieto = window.matchMedia &&
               window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Solo con JS activo escondemos los bloques para revelarlos.
  // Sin JS la página se lee completa, que es como debe ser.
  if (!quieto) document.documentElement.className += ' js';

  function revelar() {
    var items = document.querySelectorAll('.rv');
    if (!items.length) return;

    if (quieto || !('IntersectionObserver' in window)) {
      for (var i = 0; i < items.length; i++) items[i].classList.add('visible');
      return;
    }

    var obs = new IntersectionObserver(function (entradas) {
      var n = 0;
      entradas.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        var d = el.getAttribute('data-rv');
        // El retardo cuenta dentro de cada tanda visible, no del
        // documento entero: si no, lo de abajo tardaría segundos.
        el.style.transitionDelay = (d !== null ? d : String(n * 80)) + 'ms';
        el.classList.add('visible');
        obs.unobserve(el);
        n++;
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });

    for (var j = 0; j < items.length; j++) obs.observe(items[j]);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', revelar);
  } else {
    revelar();
  }
})();
