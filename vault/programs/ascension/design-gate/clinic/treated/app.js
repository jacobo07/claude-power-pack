(function () {
  "use strict";

  /* ---------------- sample data (inline, illustrative only) ---------------- */

  var NOW = "11:20";
  var TODAY = "2026-11-17";

  var PHYSIOS = ["Nadia Kerr", "Ben Ashworth", "Lucy Tran"];

  // status: done | noshow | insession | arrived | late | booked
  var APPOINTMENTS = [
    { time: "08:00", mins: 45, patient: "Gareth Price",       note: "Returning",       session: "Lower back review",       physio: "Ben Ashworth", room: "Room 1",     status: "done" },
    { time: "08:30", mins: 30, patient: "Eilidh MacLeod",     note: "New patient",     session: "Initial assessment",      physio: "Nadia Kerr",   room: "Room 2",     status: "done" },
    { time: "09:00", mins: 45, patient: "Tomasz Wilk",        note: "Post-op, week 6", session: "ACL rehab",               physio: "Lucy Tran",    room: "Rehab gym",  status: "done" },
    { time: "09:15", mins: 30, patient: "Hannah Szymanska",   note: "Returning",       session: "Shoulder mobility",       physio: "Ben Ashworth", room: "Room 1",     status: "noshow" },
    { time: "09:45", mins: 30, patient: "Rhys Bevan",         note: "Returning",       session: "Ankle sprain follow-up",  physio: "Nadia Kerr",   room: "Room 2",     status: "done" },
    { time: "10:30", mins: 45, patient: "Amara Nwosu",        note: "Returning",       session: "Neck pain treatment",     physio: "Ben Ashworth", room: "Room 1",     status: "done" },
    { time: "10:45", mins: 60, patient: "Callum Reid",        note: "Post-op, week 3", session: "Hip replacement rehab",   physio: "Lucy Tran",    room: "Rehab gym",  status: "insession" },
    { time: "11:00", mins: 45, patient: "Fatima Hussain",     note: "New patient",     session: "Initial assessment",      physio: "Nadia Kerr",   room: "Room 3",     status: "insession" },
    { time: "11:30", mins: 30, patient: "Leon Brandt",        note: "Returning",       session: "Tennis elbow, shockwave", physio: "Ben Ashworth", room: "Room 1",     status: "arrived" },
    { time: "12:00", mins: 30, patient: "Imogen Hale",        note: "Returning",       session: "Plantar fasciitis",       physio: "Nadia Kerr",   room: "Room 2",     status: "booked" },
    { time: "13:30", mins: 45, patient: "Dev Patel",          note: "New patient",     session: "Initial assessment",      physio: "Lucy Tran",    room: "Room 3",     status: "booked" },
    { time: "14:00", mins: 30, patient: "Sofia Marchetti",    note: "Pregnancy-related", session: "Pelvic girdle pain",    physio: "Nadia Kerr",   room: "Room 2",     status: "booked" },
    { time: "14:30", mins: 45, patient: "Owen Carr",          note: "Returning",       session: "Knee strengthening",      physio: "Lucy Tran",    room: "Rehab gym",  status: "booked" },
    { time: "15:15", mins: 30, patient: "Priya Raman",        note: "Returning",       session: "Sports massage",          physio: "Ben Ashworth", room: "Room 1",     status: "booked" },
    { time: "16:00", mins: 45, patient: "Mairead Quinn",      note: "Returning",       session: "Rotator cuff rehab",      physio: "Lucy Tran",    room: "Rehab gym",  status: "booked" },
    { time: "17:30", mins: 30, patient: "Jonah Albright",     note: "New patient",     session: "Initial assessment",      physio: "Ben Ashworth", room: "Room 3",     status: "booked" }
  ];

  var STATUS = {
    done:      { label: "Completed",  cls: "chip-done" },
    noshow:    { label: "No-show",    cls: "chip-noshow" },
    insession: { label: "In session", cls: "chip-insession" },
    arrived:   { label: "Checked in", cls: "chip-arrived" },
    late:      { label: "Running late", cls: "chip-late" },
    booked:    { label: "Booked",     cls: "chip-booked" }
  };

  var DAYS = [
    { key: "mon", label: "Mon 16", slots: 22 },
    { key: "tue", label: "Tue 17", slots: 22, today: true },
    { key: "wed", label: "Wed 18", slots: 22, forecast: true },
    { key: "thu", label: "Thu 19", slots: 22, forecast: true },
    { key: "fri", label: "Fri 20", slots: 22, forecast: true },
    { key: "sat", label: "Sat 21", slots: 8,  forecast: true }
  ];

  // booked 30-minute slots per room per day; null = room closed that day
  var ROOMS = [
    { name: "Room 1",    use: "Treatment",        booked: [19, 18, 17, 20, 15, 7] },
    { name: "Room 2",    use: "Treatment",        booked: [16, 17, 14, 18, 12, 6] },
    { name: "Room 3",    use: "Assessment",       booked: [11, 13, 9, 14, 8, null] },
    { name: "Rehab gym", use: "Classes and rehab", booked: [13, 9, 15, 11, 17, 5] }
  ];

  var FOLLOW_UPS = [
    { id: "f1", name: "Hannah Szymanska", reason: "Missed 09:15 today. Rebook shoulder session.",            last: "10 Nov", phone: "07700 914 382", due: "2026-11-17", physio: "Ben Ashworth" },
    { id: "f2", name: "Martin Okoye",     reason: "Check pain levels after first week of home exercises.",   last: "7 Nov",  phone: "07700 361 047", due: "2026-11-14", physio: "Lucy Tran" },
    { id: "f3", name: "Grace Lindqvist",  reason: "Discharged. Confirm she is managing stairs at home.",      last: "4 Nov",  phone: "07700 528 916", due: "2026-11-15", physio: "Nadia Kerr" },
    { id: "f4", name: "Eilidh MacLeod",   reason: "Send results of today's assessment and book block of 4.", last: "Today",  phone: "07700 802 153", due: "2026-11-17", physio: "Nadia Kerr" },
    { id: "f5", name: "Ravi Chandra",     reason: "Course ended. Offer a review in 6 weeks.",                 last: "12 Nov", phone: "07700 447 690", due: "2026-11-19", physio: "Ben Ashworth" },
    { id: "f6", name: "Beatriz Coelho",   reason: "Insurer needs a progress report. Confirm policy number.",  last: "13 Nov", phone: "07700 275 538", due: "2026-11-18", physio: "Lucy Tran" }
  ];

  /* ---------------- helpers ---------------- */

  function $(id) { return document.getElementById(id); }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function toMin(t) { var p = t.split(":"); return +p[0] * 60 + +p[1]; }
  function endTime(t, mins) {
    var m = toMin(t) + mins;
    return String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0");
  }
  function daysBetween(a, b) { return Math.round((Date.parse(b) - Date.parse(a)) / 86400000); }
  function pct(n, d) { return Math.round((n / d) * 100); }

  var FINISHED = { done: true, noshow: true };

  /* ---------------- appointments ---------------- */

  var physioSelect = $("filter-physio");
  var hideFinished = $("filter-remaining");

  PHYSIOS.forEach(function (p) {
    var o = document.createElement("option");
    o.value = p; o.textContent = p;
    physioSelect.appendChild(o);
  });

  function renderAppointments() {
    var who = physioSelect.value;
    var rows = APPOINTMENTS.filter(function (a) {
      if (who !== "all" && a.physio !== who) return false;
      if (hideFinished.checked && FINISHED[a.status]) return false;
      return true;
    });

    var now = toMin(NOW);
    var html = "";
    var nowPlaced = false;

    rows.forEach(function (a) {
      var start = toMin(a.time);
      if (!nowPlaced && start > now) {
        html += '<tr class="now-row" aria-hidden="true"><td colspan="6"><div class="now-line">Now ' + NOW + "</div></td></tr>";
        nowPlaced = true;
      }
      var st = STATUS[a.status];
      var cls = FINISHED[a.status] ? "is-done" : a.status === "insession" ? "is-now" : "";
      html +=
        '<tr class="' + cls + '">' +
          '<td class="t">' + a.time + "<small>to " + endTime(a.time, a.mins) + "</small></td>" +
          '<td class="who">' + esc(a.patient) + "<small>" + esc(a.note) + '</small><small class="m-only">' + esc(a.physio) + ", " + esc(a.room) + "</small></td>" +
          '<td class="sess">' + esc(a.session) + "<small>" + a.mins + " min</small></td>" +
          '<td class="nw">' + esc(a.physio) + "</td>" +
          '<td class="nw">' + esc(a.room) + "</td>" +
          '<td><span class="chip ' + st.cls + '">' + st.label + "</span></td>" +
        "</tr>";
    });

    $("appts-body").innerHTML = html;
    $("appts-empty").hidden = rows.length > 0;

    var left = rows.filter(function (a) { return !FINISHED[a.status]; }).length;
    $("appts-count").textContent = rows.length === 0
      ? "Nothing to show"
      : rows.length + (rows.length === 1 ? " appointment" : " appointments") + ", " + left + " not yet finished";
  }

  physioSelect.addEventListener("change", renderAppointments);
  hideFinished.addEventListener("change", renderAppointments);

  /* ---------------- utilisation heatmap ---------------- */

  // thresholds for the six sequential steps
  var STEPS = [
    { max: 40,  cls: "h1", label: "under 40%" },
    { max: 55,  cls: "h2", label: "40 to 54%" },
    { max: 70,  cls: "h3", label: "55 to 69%" },
    { max: 80,  cls: "h4", label: "70 to 79%" },
    { max: 90,  cls: "h5", label: "80 to 89%" },
    { max: 101, cls: "h6", label: "90% or more" }
  ];
  function step(p) { for (var i = 0; i < STEPS.length; i++) if (p < STEPS[i].max) return STEPS[i]; return STEPS[STEPS.length - 1]; }

  $("legend-steps").innerHTML = STEPS.map(function (s) {
    return '<span class="' + s.cls + '" title="' + s.label + '"></span>';
  }).join("");

  var head = '<tr><td></td>' + DAYS.map(function (d) {
    return '<th scope="col"' + (d.today ? ' class="is-today"' : "") + ">" + d.label + (d.today ? "<br>today" : "") + "</th>";
  }).join("") + '<th scope="col" class="avg-h">Week</th></tr>';
  $("heat-head").innerHTML = head;
  var cols = '<col class="c-room">' + DAYS.map(function () { return "<col>"; }).join("") + '<col class="c-week">';
  $("heat").insertAdjacentHTML("afterbegin", "<colgroup>" + cols + "</colgroup>");

  var totalBooked = 0, totalSlots = 0;
  var bodyHtml = ROOMS.map(function (r) {
    var rb = 0, rs = 0;
    var cells = r.booked.map(function (b, i) {
      var d = DAYS[i];
      if (b === null) return '<td class="closed">Closed</td>';
      rb += b; rs += d.slots;
      var p = pct(b, d.slots);
      var s = step(p);
      var tip = r.name + ", " + d.label + "|" + b + " of " + d.slots + " slots booked (" + p + "%)" + (d.forecast ? ", bookings so far" : "");
      return '<td class="cell ' + s.cls + (d.forecast ? " is-forecast" : "") + '" tabindex="0" data-tip="' + esc(tip) +
             '" aria-label="' + esc(tip.replace("|", ": ")) + '">' + p + "%</td>";
    }).join("");
    totalBooked += rb; totalSlots += rs;
    return '<tr><th scope="row">' + esc(r.name) + "<small>" + esc(r.use) + '</small><small class="wk-m">Week ' + pct(rb, rs) + "%</small></th>" + cells +
           '<td class="avg">' + pct(rb, rs) + "%</td></tr>";
  }).join("");

  // clinic-wide row
  var dayTotals = DAYS.map(function (d, i) {
    var b = 0, s = 0;
    ROOMS.forEach(function (r) { if (r.booked[i] !== null) { b += r.booked[i]; s += d.slots; } });
    return pct(b, s);
  });
  bodyHtml += '<tr><th scope="row">All rooms<small>Clinic total</small><small class="wk-m">Week ' + pct(totalBooked, totalSlots) + "%</small></th>" +
    dayTotals.map(function (p) { return '<td class="avg">' + p + "%</td>"; }).join("") +
    '<td class="avg">' + pct(totalBooked, totalSlots) + "%</td></tr>";
  $("heat-body").innerHTML = bodyHtml;

  var tooltip = $("tooltip");
  var panel = tooltip.parentElement;
  function showTip(cell) {
    var parts = cell.getAttribute("data-tip").split("|");
    tooltip.innerHTML = "<strong>" + esc(parts[0]) + "</strong>" + esc(parts[1]);
    var pr = panel.getBoundingClientRect(), cr = cell.getBoundingClientRect();
    tooltip.style.left = (cr.left - pr.left + cr.width / 2) + "px";
    tooltip.style.top = (cr.top - pr.top) + "px";
    tooltip.hidden = false;
  }
  function hideTip() { tooltip.hidden = true; }
  var heat = $("heat");
  heat.addEventListener("mouseover", function (e) { var c = e.target.closest("td.cell"); if (c) showTip(c); });
  heat.addEventListener("mouseleave", hideTip);
  heat.addEventListener("focusin", function (e) { var c = e.target.closest("td.cell"); if (c) showTip(c); });
  heat.addEventListener("focusout", hideTip);

  /* ---------------- follow-up calls ---------------- */

  var called = [];

  function dueLabel(due) {
    var d = daysBetween(TODAY, due);
    if (d < 0) return { text: "Overdue " + -d + (d === -1 ? " day" : " days"), cls: "due-over", rank: 0 };
    if (d === 0) return { text: "Due today", cls: "due-today", rank: 1 };
    if (d === 1) return { text: "Due tomorrow", cls: "due-later", rank: 2 };
    return { text: "Due in " + d + " days", cls: "due-later", rank: 2 };
  }

  function renderCalls() {
    var open = FOLLOW_UPS.filter(function (f) { return called.indexOf(f.id) === -1; })
      .sort(function (a, b) { return Date.parse(a.due) - Date.parse(b.due); });

    $("calls-list").innerHTML = open.map(function (f) {
      var due = dueLabel(f.due);
      return '<li class="call" data-id="' + f.id + '">' +
          '<p class="call-name">' + esc(f.name) + "</p>" +
          '<p class="due ' + due.cls + '">' + due.text + "</p>" +
          '<p class="call-reason">' + esc(f.reason) + "</p>" +
          '<p class="call-meta"><a href="tel:' + f.phone.replace(/\s/g, "") + '">' + esc(f.phone) + "</a>" +
            "<span>Last seen " + esc(f.last) + "</span><span>" + esc(f.physio) + "</span></p>" +
          '<div class="call-actions"><button type="button" class="btn btn-outline" data-act="called">Mark as called</button></div>' +
        "</li>";
    }).join("");

    $("calls-empty").hidden = open.length > 0;

    var urgent = open.filter(function (f) { return dueLabel(f.due).rank <= 1; }).length;
    var over = open.filter(function (f) { return dueLabel(f.due).rank === 0; }).length;
    $("calls-count").textContent = open.length === 0
      ? "Nothing waiting"
      : open.length + " waiting, " + over + " overdue";

    $("kpi-calls").textContent = urgent;
    $("kpi-calls-note").textContent = over > 0 ? over + " overdue, oldest first in the list" : "None overdue";

    var done = FOLLOW_UPS.filter(function (f) { return called.indexOf(f.id) !== -1; });
    $("called-wrap").hidden = done.length === 0;
    $("called-summary").textContent = "Called today (" + done.length + ")";
    $("called-list").innerHTML = done.map(function (f) {
      return '<li><span>' + esc(f.name) + '</span><button type="button" class="btn btn-quiet" data-act="undo" data-id="' +
             f.id + '">Undo</button></li>';
    }).join("");
  }

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  $("calls-list").addEventListener("click", function (e) {
    var btn = e.target.closest('button[data-act="called"]');
    if (!btn) return;
    var li = btn.closest(".call");
    var id = li.getAttribute("data-id");
    var commit = function () { called.push(id); renderCalls(); };
    if (reduceMotion.matches) { commit(); return; }
    li.classList.add("leaving");
    setTimeout(commit, 200);
  });

  $("called-list").addEventListener("click", function (e) {
    var btn = e.target.closest('button[data-act="undo"]');
    if (!btn) return;
    var id = btn.getAttribute("data-id");
    called = called.filter(function (c) { return c !== id; });
    renderCalls();
  });

  /* ---------------- KPIs ---------------- */

  function renderKpis() {
    var total = APPOINTMENTS.length;
    var finished = APPOINTMENTS.filter(function (a) { return a.status === "done"; }).length;
    var noshow = APPOINTMENTS.filter(function (a) { return a.status === "noshow"; }).length;
    $("kpi-appts").textContent = total;
    $("kpi-appts-note").textContent = finished + " completed, " + noshow + " no-show";

    var now = toMin(NOW);
    var upcoming = APPOINTMENTS.filter(function (a) { return a.status === "booked" || a.status === "late"; });
    $("kpi-remaining").textContent = upcoming.length;
    var next = upcoming.filter(function (a) { return toMin(a.time) >= now; })[0];
    $("kpi-next").textContent = next ? "Next: " + next.patient + " at " + next.time : "No more arrivals today";

    $("kpi-util").textContent = pct(totalBooked, totalSlots) + "%";
    var lowest = ROOMS.map(function (r) {
      var b = 0, s = 0;
      r.booked.forEach(function (v, i) { if (v !== null) { b += v; s += DAYS[i].slots; } });
      return { name: r.name, p: pct(b, s) };
    }).sort(function (a, b) { return a.p - b.p; })[0];
    $("kpi-util-note").textContent = "Most free capacity: " + lowest.name + " (" + lowest.p + "%)";
  }

  renderAppointments();
  renderCalls();
  renderKpis();
})();
