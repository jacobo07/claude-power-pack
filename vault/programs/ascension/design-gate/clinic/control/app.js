(function () {
  "use strict";

  // ---- Sample data -------------------------------------------------------
  // Times are local "HH:MM" for today.
  var appointments = [
    { time: "08:30", patient: "Maria Lopez",     treatment: "Lower back assessment", length: 45, practitioner: "Dr. Hannah Reid", room: "Room 1", status: "done" },
    { time: "09:00", patient: "Tom Ashworth",    treatment: "ACL rehab, week 6",     length: 30, practitioner: "Sam Okafor",      room: "Gym",    status: "done" },
    { time: "09:30", patient: "Priya Shah",      treatment: "Shoulder mobilisation", length: 30, practitioner: "Dr. Hannah Reid", room: "Room 2", status: "cancelled" },
    { time: "10:15", patient: "George Bennett",  treatment: "Sports massage",        length: 45, practitioner: "Lucia Ferrer",    room: "Room 3", status: "checked" },
    { time: "11:00", patient: "Aisha Rahman",    treatment: "Post-op knee review",   length: 30, practitioner: "Sam Okafor",      room: "Room 1", status: "booked" },
    { time: "11:45", patient: "Daniel Kim",      treatment: "Neck pain follow-up",   length: 30, practitioner: "Dr. Hannah Reid", room: "Room 2", status: "late" },
    { time: "13:30", patient: "Elena Petrova",   treatment: "Hydrotherapy",          length: 45, practitioner: "Lucia Ferrer",    room: "Pool",   status: "booked" },
    { time: "14:30", patient: "Jack Morrison",   treatment: "Ankle sprain, initial", length: 45, practitioner: "Sam Okafor",      room: "Room 1", status: "booked" },
    { time: "15:30", patient: "Fatima Noor",     treatment: "Pelvic health",         length: 60, practitioner: "Dr. Hannah Reid", room: "Room 2", status: "booked" },
    { time: "16:45", patient: "Oliver Grant",    treatment: "Gait retraining",       length: 30, practitioner: "Lucia Ferrer",    room: "Gym",    status: "booked" }
  ];

  // Booked hours this week per room; open hours are 10 h x 5 days = 50 h.
  var OPEN_HOURS = 50;
  var rooms = [
    { name: "Room 1", booked: 41.5 },
    { name: "Room 2", booked: 37 },
    { name: "Room 3", booked: 22.5 },
    { name: "Gym",    booked: 30 },
    { name: "Pool",   booked: 11 }
  ];

  // daysSince = days since last visit; dueInDays < 0 means the call is overdue.
  var followUps = [
    { patient: "Rachel Evans",  phone: "07700 900 412", reason: "Discharged, check 2-week progress", lastVisit: 16, dueInDays: -2 },
    { patient: "Samuel Turner", phone: "07700 900 087", reason: "Missed appointment on Monday",      lastVisit: 9,  dueInDays: -1 },
    { patient: "Chloe Martin",  phone: "07700 900 653", reason: "Scan results back, rebook review",  lastVisit: 5,  dueInDays: 0 },
    { patient: "Ahmed Yusuf",   phone: "07700 900 229", reason: "Home exercise check-in",            lastVisit: 7,  dueInDays: 1 },
    { patient: "Linda Hughes",  phone: "07700 900 771", reason: "Insurance pre-authorisation needed", lastVisit: 3, dueInDays: 3 }
  ];

  var STATUS_LABEL = {
    done: "Completed",
    checked: "Checked in",
    booked: "Booked",
    late: "Running late",
    cancelled: "Cancelled"
  };

  // ---- Helpers -----------------------------------------------------------
  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function minutes(hhmm) {
    var parts = hhmm.split(":");
    return Number(parts[0]) * 60 + Number(parts[1]);
  }

  function endTime(hhmm, length) {
    var total = minutes(hhmm) + length;
    var h = Math.floor(total / 60);
    var m = total % 60;
    return String(h).padStart(2, "0") + ":" + String(m).padStart(2, "0");
  }

  function dueText(days) {
    if (days < 0) return Math.abs(days) + (days === -1 ? " day overdue" : " days overdue");
    if (days === 0) return "Due today";
    return "Due in " + days + (days === 1 ? " day" : " days");
  }

  // ---- Header + dates ----------------------------------------------------
  var now = new Date();
  document.getElementById("today-label").textContent = now.toLocaleDateString("en-GB", {
    weekday: "long", day: "numeric", month: "long", year: "numeric"
  });

  var monday = new Date(now);
  monday.setDate(now.getDate() - ((now.getDay() + 6) % 7));
  var friday = new Date(monday);
  friday.setDate(monday.getDate() + 4);
  var fmt = { day: "numeric", month: "short" };
  document.getElementById("week-label").textContent =
    monday.toLocaleDateString("en-GB", fmt) + " – " + friday.toLocaleDateString("en-GB", fmt);

  // ---- Appointments ------------------------------------------------------
  var tbody = document.getElementById("appt-body");
  var emptyAppt = document.getElementById("appt-empty");
  var filter = document.getElementById("practitioner-filter");

  var practitioners = appointments
    .map(function (a) { return a.practitioner; })
    .filter(function (p, i, arr) { return arr.indexOf(p) === i; })
    .sort();
  practitioners.forEach(function (p) {
    var opt = el("option", null, p);
    opt.value = p;
    filter.appendChild(opt);
  });

  function renderAppointments() {
    var who = filter.value;
    var rows = appointments.filter(function (a) { return who === "all" || a.practitioner === who; });
    var nowMin = now.getHours() * 60 + now.getMinutes();
    var nextIndex = -1;
    rows.forEach(function (a, i) {
      if (nextIndex === -1 && a.status !== "cancelled" && a.status !== "done" && minutes(a.time) >= nowMin) nextIndex = i;
    });

    tbody.textContent = "";
    rows.forEach(function (a, i) {
      var tr = el("tr");
      if (a.status === "done" || a.status === "cancelled") tr.className = "is-past";
      if (i === nextIndex) tr.className = "is-next";

      var time = el("td", "time", a.time);
      time.appendChild(el("span", "sub", "to " + endTime(a.time, a.length)));
      tr.appendChild(time);

      tr.appendChild(el("td", null, a.patient));
      tr.appendChild(el("td", null, a.treatment));
      tr.appendChild(el("td", null, a.practitioner));
      tr.appendChild(el("td", null, a.room));

      var statusCell = el("td");
      statusCell.appendChild(el("span", "badge badge-" + a.status, STATUS_LABEL[a.status]));
      tr.appendChild(statusCell);

      tbody.appendChild(tr);
    });
    emptyAppt.hidden = rows.length > 0;
  }

  filter.addEventListener("change", renderAppointments);
  renderAppointments();

  var active = appointments.filter(function (a) { return a.status !== "cancelled"; });
  document.getElementById("stat-total").textContent = active.length;
  document.getElementById("stat-checked").textContent =
    appointments.filter(function (a) { return a.status === "checked"; }).length;

  // ---- Rooms -------------------------------------------------------------
  var roomList = document.getElementById("rooms-list");
  var totalBooked = 0;
  rooms.forEach(function (r) {
    totalBooked += r.booked;
    var pct = Math.round((r.booked / OPEN_HOURS) * 100);
    var li = el("li");

    var row = el("div", "room-row");
    row.appendChild(el("span", null, r.name));
    row.appendChild(el("span", "pct", pct + "%"));
    li.appendChild(row);

    var bar = el("div", "bar");
    bar.setAttribute("role", "img");
    bar.setAttribute("aria-label", r.name + " " + pct + "% booked");
    var fill = el("div", "bar-fill" + (pct >= 80 ? " is-high" : pct < 40 ? " is-low" : ""));
    fill.style.width = Math.min(pct, 100) + "%";
    bar.appendChild(fill);
    li.appendChild(bar);

    li.appendChild(el("p", "room-hours", r.booked + " of " + OPEN_HOURS + " h booked"));
    roomList.appendChild(li);
  });
  document.getElementById("stat-util").textContent =
    Math.round((totalBooked / (OPEN_HOURS * rooms.length)) * 100) + "%";

  // ---- Follow-ups --------------------------------------------------------
  var fuList = document.getElementById("fu-list");
  var fuEmpty = document.getElementById("fu-empty");
  var fuCount = document.getElementById("fu-count");
  var statCalls = document.getElementById("stat-calls");

  function renderFollowUps() {
    var pending = followUps
      .filter(function (f) { return !f.called; })
      .sort(function (a, b) { return a.dueInDays - b.dueInDays; });

    fuList.textContent = "";
    pending.forEach(function (f) {
      var li = el("li", "fu");
      var info = el("div");
      info.appendChild(el("p", "fu-name", f.patient));
      info.appendChild(el("p", "fu-meta", f.reason));

      var meta = el("p", "fu-meta");
      meta.appendChild(el("span", "fu-phone", f.phone));
      meta.appendChild(document.createTextNode(" · last visit " + f.lastVisit + " days ago · "));
      meta.appendChild(el("span", f.dueInDays < 0 ? "fu-overdue" : null, dueText(f.dueInDays)));
      info.appendChild(meta);
      li.appendChild(info);

      var btn = el("button", "fu-btn", "Mark called");
      btn.type = "button";
      btn.setAttribute("aria-label", "Mark " + f.patient + " as called");
      btn.addEventListener("click", function () {
        f.called = true;
        renderFollowUps();
      });
      li.appendChild(btn);
      fuList.appendChild(li);
    });

    fuEmpty.hidden = pending.length > 0;
    fuCount.textContent = pending.length + " to call";
    statCalls.textContent = pending.length;
  }

  renderFollowUps();
})();
