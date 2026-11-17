// Turia Yoga: schedule tabs and the free-class booking form.
// The weekly schedule in index.html is the single source of truth; the form reads it from the DOM.
(function () {
  "use strict";
  document.documentElement.classList.add("js");

  document.addEventListener("DOMContentLoaded", function () {
    initTabs();
    initBooking();
  });

  function initTabs() {
    var tablist = document.querySelector(".tabs");
    if (!tablist) return;
    var tabs = Array.prototype.slice.call(tablist.querySelectorAll("[role=tab]"));
    var panels = Array.prototype.slice.call(document.querySelectorAll(".day"));
    tablist.hidden = false;

    function select(tab, focus) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
      });
      panels.forEach(function (p) { p.hidden = p.id !== tab.getAttribute("aria-controls"); });
      if (focus) tab.focus();
    }

    tabs.forEach(function (tab, i) {
      tab.addEventListener("click", function () { select(tab, false); });
      tab.addEventListener("keydown", function (e) {
        var next = null;
        if (e.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
        else if (e.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
        else if (e.key === "Home") next = tabs[0];
        else if (e.key === "End") next = tabs[tabs.length - 1];
        if (next) { e.preventDefault(); select(next, true); }
      });
    });

    // Open on today's day (Sunday falls back to Monday, the studio is closed).
    var today = new Date().getDay();
    select(tabs[today >= 1 && today <= 6 ? today - 1 : 0], false);
  }


  function sessionsByDay() {
    var map = {};
    document.querySelectorAll(".day").forEach(function (day) {
      var list = [];
      day.querySelectorAll("li[data-time]").forEach(function (li) {
        list.push({ time: li.getAttribute("data-time"), name: li.getAttribute("data-class") });
      });
      map[day.getAttribute("data-day")] = { name: day.getAttribute("data-name"), sessions: list };
    });
    return map;
  }

  function isoDate(d) {
    var m = String(d.getMonth() + 1).padStart(2, "0");
    var day = String(d.getDate()).padStart(2, "0");
    return d.getFullYear() + "-" + m + "-" + day;
  }

  function parseDate(value) {
    var parts = value.split("-").map(Number);
    if (parts.length !== 3 || parts.some(isNaN)) return null;
    return new Date(parts[0], parts[1] - 1, parts[2]);
  }

  function initBooking() {
    var form = document.getElementById("booking-form");
    if (!form) return;
    var success = document.getElementById("booking-success");
    var summary = document.getElementById("success-summary");
    var resetBtn = document.getElementById("booking-reset");
    var fecha = form.elements.fecha;
    var clase = form.elements.clase;
    var schedule = sessionsByDay();

    var today = new Date();
    var max = new Date(today.getFullYear(), today.getMonth() + 2, today.getDate());
    fecha.min = isoDate(today);
    fecha.max = isoDate(max);

    function setError(field, msg) {
      var err = document.getElementById(field.id + "-error");
      if (msg) {
        err.textContent = msg;
        err.hidden = false;
        field.setAttribute("aria-invalid", "true");
      } else {
        err.textContent = "";
        err.hidden = true;
        field.removeAttribute("aria-invalid");
      }
    }

    function fillClasses() {
      clase.innerHTML = "";
      var d = fecha.value ? parseDate(fecha.value) : null;
      var day = d ? schedule[String(d.getDay())] : null;
      var placeholder = document.createElement("option");
      placeholder.value = "";
      if (!d) placeholder.textContent = "Elige primero el día";
      else if (!day) placeholder.textContent = "Ese día no hay clases";
      else placeholder.textContent = "Elige una clase";
      clase.appendChild(placeholder);
      if (!day) { clase.disabled = !!d; return; }
      clase.disabled = false;
      day.sessions.forEach(function (s) {
        var opt = document.createElement("option");
        opt.value = s.time + " " + s.name;
        opt.textContent = s.time + "  " + s.name;
        clase.appendChild(opt);
      });
    }

    function checkFecha() {
      if (!fecha.value) return "Elige el día de tu clase.";
      var d = parseDate(fecha.value);
      if (!d) return "Escribe una fecha válida.";
      var start = parseDate(fecha.min);
      if (d < start) return "Elige un día a partir de hoy.";
      if (d > parseDate(fecha.max)) return "Por ahora reservamos con un máximo de dos meses de antelación.";
      if (d.getDay() === 0) return "Los domingos el estudio está cerrado. Elige otro día.";
      return "";
    }

    var rules = {
      nombre: function (f) { return f.value.trim().length >= 2 ? "" : "Dinos tu nombre."; },
      email: function (f) {
        var v = f.value.trim();
        if (!v) return "Necesitamos tu correo para confirmarte la plaza.";
        return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v) ? "" : "Revisa el correo, parece que falta algo (ejemplo: nombre@correo.es).";
      },
      telefono: function (f) {
        var v = f.value.replace(/[\s().-]/g, "");
        if (!v) return "";
        return /^\+?\d{9,13}$/.test(v) ? "" : "Revisa el teléfono: deben ser al menos 9 cifras.";
      },
      fecha: function () { return checkFecha(); },
      clase: function (f) { return f.value ? "" : "Elige la clase a la que quieres venir."; },
      privacidad: function (f) { return f.checked ? "" : "Necesitamos tu permiso para guardar la reserva."; }
    };

    fecha.addEventListener("change", function () {
      fillClasses();
      setError(fecha, checkFecha());
      if (clase.getAttribute("aria-invalid")) setError(clase, "");
    });

    Object.keys(rules).forEach(function (name) {
      var field = form.elements[name];
      field.addEventListener("blur", function () {
        if (field.getAttribute("aria-invalid") === "true") setError(field, rules[name](field));
      });
      field.addEventListener("input", function () {
        if (field.getAttribute("aria-invalid") === "true") setError(field, rules[name](field));
      });
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var firstBad = null;
      Object.keys(rules).forEach(function (name) {
        var field = form.elements[name];
        var msg = rules[name](field);
        setError(field, msg);
        if (msg && !firstBad) firstBad = field;
      });
      if (firstBad) { firstBad.focus(); return; }

      var d = parseDate(fecha.value);
      var dayName = schedule[String(d.getDay())].name;
      var fechaTxt = dayName + " " + d.getDate() + "/" + (d.getMonth() + 1) + "/" + d.getFullYear();
      var nombre = form.elements.nombre.value.trim();
      var body = [
        "Hola, quiero reservar mi primera clase gratis.",
        "",
        "Nombre: " + nombre,
        "Correo: " + form.elements.email.value.trim(),
        "Teléfono: " + (form.elements.telefono.value.trim() || "no indicado"),
        "Día: " + fechaTxt,
        "Clase: " + clase.value,
        "Comentarios: " + (form.elements.mensaje.value.trim() || "ninguno")
      ].join("\n");

      // Static site: the request travels as a pre-written email the visitor sends.
      window.location.href = "mailto:hola@turiayoga.es?subject=" +
        encodeURIComponent("Primera clase gratis: " + clase.value + ", " + fechaTxt) +
        "&body=" + encodeURIComponent(body);

      summary.textContent = nombre + ", has elegido " + clase.value + " el " + fechaTxt + ".";
      form.hidden = true;
      success.hidden = false;
      success.focus();
    });

    resetBtn.addEventListener("click", function () {
      form.reset();
      fillClasses();
      success.hidden = true;
      form.hidden = false;
      form.elements.nombre.focus();
    });

    fillClasses();
  }
})();
