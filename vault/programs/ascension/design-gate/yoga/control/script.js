(function () {
  'use strict';

  var STUDIO_EMAIL = 'hola@casallumioga.es';

  // Menú móvil
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
      toggle.textContent = open ? 'Cerrar' : 'Menú';
    });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A' && nav.classList.contains('open')) {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.textContent = 'Menú';
      }
    });
  }

  var year = document.getElementById('year');
  if (year) year.textContent = String(new Date().getFullYear());

  // Formulario de reserva
  var form = document.getElementById('booking');
  if (!form) return;

  var status = document.getElementById('form-status');
  var fecha = document.getElementById('fecha');

  function isoDate(d) {
    var m = String(d.getMonth() + 1).padStart(2, '0');
    var day = String(d.getDate()).padStart(2, '0');
    return d.getFullYear() + '-' + m + '-' + day;
  }

  var today = new Date();
  today.setHours(0, 0, 0, 0);
  fecha.min = isoDate(today);

  function parseDate(value) {
    var p = value.split('-');
    if (p.length !== 3) return null;
    var d = new Date(Number(p[0]), Number(p[1]) - 1, Number(p[2]));
    return isNaN(d.getTime()) ? null : d;
  }

  var rules = {
    nombre: function (v) {
      return v.trim().length >= 2 ? '' : 'Escribe tu nombre.';
    },
    email: function (v) {
      if (!v.trim()) return 'Necesitamos un correo para confirmarte la plaza.';
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()) ? '' : 'Este correo no parece válido. Revisa que tenga @ y dominio.';
    },
    telefono: function (v) {
      if (!v.trim()) return '';
      return /^[+\d][\d\s-]{8,}$/.test(v.trim()) ? '' : 'Revisa el teléfono: usa solo números, espacios o +34.';
    },
    clase: function (v) {
      return v ? '' : 'Elige una clase (o deja que te recomendemos).';
    },
    fecha: function (v) {
      if (!v) return 'Elige un día.';
      var d = parseDate(v);
      if (!d) return 'Elige un día válido.';
      if (d < today) return 'Elige un día a partir de hoy.';
      if (d.getDay() === 0) return 'Los domingos el estudio está cerrado. Elige otro día.';
      return '';
    },
    privacidad: function (_, el) {
      return el.checked ? '' : 'Necesitamos tu permiso para gestionar la reserva.';
    }
  };

  function validateField(name) {
    var el = form.elements[name];
    var msg = rules[name](el.value, el);
    var errEl = document.getElementById(name + '-error');
    errEl.textContent = msg;
    if (msg) {
      el.setAttribute('aria-invalid', 'true');
      el.setAttribute('aria-describedby', name + '-error');
    } else {
      el.removeAttribute('aria-invalid');
      el.removeAttribute('aria-describedby');
    }
    return !msg;
  }

  Object.keys(rules).forEach(function (name) {
    var el = form.elements[name];
    var evt = el.type === 'checkbox' || el.tagName === 'SELECT' ? 'change' : 'blur';
    el.addEventListener(evt, function () {
      if (el.getAttribute('aria-invalid') === 'true' || el.value) validateField(name);
    });
  });

  function formatDate(value) {
    var d = parseDate(value);
    return d.toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' });
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var firstInvalid = null;
    Object.keys(rules).forEach(function (name) {
      if (!validateField(name) && !firstInvalid) firstInvalid = form.elements[name];
    });
    if (firstInvalid) {
      status.hidden = true;
      firstInvalid.focus();
      return;
    }

    var data = {
      nombre: form.elements.nombre.value.trim(),
      email: form.elements.email.value.trim(),
      telefono: form.elements.telefono.value.trim(),
      clase: form.elements.clase.value,
      fecha: formatDate(form.elements.fecha.value),
      mensaje: form.elements.mensaje.value.trim()
    };

    var body = [
      'Hola, quiero reservar mi primera clase gratis.',
      '',
      'Nombre: ' + data.nombre,
      'Correo: ' + data.email,
      'Teléfono: ' + (data.telefono || 'no indicado'),
      'Clase: ' + data.clase,
      'Día preferido: ' + data.fecha,
      data.mensaje ? 'Comentarios: ' + data.mensaje : ''
    ].filter(function (line, i, arr) { return line !== '' || i === 1; }).join('\n');

    var href = 'mailto:' + STUDIO_EMAIL +
      '?subject=' + encodeURIComponent('Reserva primera clase gratis - ' + data.nombre) +
      '&body=' + encodeURIComponent(body);

    status.innerHTML = '';
    var p1 = document.createElement('p');
    p1.textContent = 'Tu reserva está lista para ' + data.clase + ' el ' + data.fecha + '. Envía el correo que se ha abierto para confirmarla.';
    var p2 = document.createElement('p');
    p2.appendChild(document.createTextNode('¿No se ha abierto tu correo? Escríbenos a '));
    var a = document.createElement('a');
    a.href = href;
    a.textContent = STUDIO_EMAIL;
    p2.appendChild(a);
    p2.appendChild(document.createTextNode(' o llámanos al 961 23 45 67.'));
    status.appendChild(p1);
    status.appendChild(p2);
    status.hidden = false;

    window.location.href = href;
  });
})();
