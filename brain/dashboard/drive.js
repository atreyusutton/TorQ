// TorQ dashboard: status display and hold-to-drive keyboard control.
(() => {
  "use strict";

  const SEND_INTERVAL_MS = 100;   // body stops if commands are older than 300 ms
  const SLOW_FACTOR = 0.4;
  const TURN_MIX = 0.5;           // how hard W+A / W+D arcs

  const $ = (id) => document.getElementById(id);
  const held = new Set();
  let ws = null;
  let speedLevel = 3;
  let slow = false;
  let wasDriving = false;
  let status = null;
  let cameraFailedAt = 0;

  // ---- connection -------------------------------------------------------

  function connect() {
    ws = new WebSocket(`ws://${location.host}/ws`);
    ws.onopen = () => setPill("link", "dashboard online", "ok");
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === "status") render(msg);
      } catch (err) {
        console.error("bad status message", err);
      }
    };
    ws.onclose = () => {
      setPill("link", "dashboard offline", "bad");
      setTimeout(connect, 1000);
    };
    ws.onerror = (err) => console.error("websocket error", err);
  }

  function send(msg) {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(msg));
  }

  // ---- driving ------------------------------------------------------------

  function driveVector() {
    const fwd = (held.has("w") ? 1 : 0) - (held.has("s") ? 1 : 0);
    const turn = (held.has("d") ? 1 : 0) - (held.has("a") ? 1 : 0);
    let left, right;
    if (fwd === 0) {
      left = turn; right = -turn;               // pivot in place
    } else {
      left = fwd + turn * TURN_MIX * fwd;        // arc; keeps turn direction when reversing
      right = fwd - turn * TURN_MIX * fwd;
    }
    const scale = (speedLevel / 5) * (slow ? SLOW_FACTOR : 1);
    const clamp = (v) => Math.max(-1, Math.min(1, v));
    return { left: clamp(left) * scale, right: clamp(right) * scale };
  }

  function tick() {
    const driving = ["w", "a", "s", "d"].some((k) => held.has(k));
    if (driving) {
      const v = driveVector();
      send({ type: "drive", left: v.left, right: v.right });
    } else if (wasDriving) {
      send({ type: "stop" });
    }
    wasDriving = driving;
  }

  function releaseAll() {
    held.clear();
    slow = false;
    renderKeys();
    send({ type: "stop" });
    wasDriving = false;
  }

  // Physical key positions (e.code), so layouts and browser shortcuts don't matter.
  const DRIVE_KEYS = {
    KeyW: "w", ArrowUp: "w",
    KeyA: "a", ArrowLeft: "a",
    KeyS: "s", ArrowDown: "s",
    KeyD: "d", ArrowRight: "d",
  };

  // Capture phase on window: runs before buttons, scrolling, or Firefox's find-as-you-type.
  window.addEventListener("keydown", (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    $("last-key").textContent = e.code || e.key;
    const drive = DRIVE_KEYS[e.code];
    if (drive) {
      e.preventDefault();
      e.stopPropagation();
      held.add(drive);
      slow = e.shiftKey;
      if (!e.repeat) tick();   // react on press without waiting for the next tick
    } else if (e.code === "ShiftLeft" || e.code === "ShiftRight") {
      slow = true;
    } else if (e.code === "Space") {
      e.preventDefault();
      releaseAll();
    } else if (e.code === "Escape") {
      e.preventDefault();
      releaseAll();
      send({ type: "estop" });
    } else if (e.code === "KeyR" && !e.repeat) {
      e.preventDefault();
      send({ type: "reset" });
    } else if (e.code === "KeyM" && !e.repeat) {
      e.preventDefault();
      send({ type: "manual", on: !(status && status.manual) });
    } else if (/^Digit[1-5]$/.test(e.code)) {
      e.preventDefault();
      speedLevel = Number(e.code.slice(5));
      renderSpeed();
    }
    renderKeys();
  }, true);

  window.addEventListener("keyup", (e) => {
    const drive = DRIVE_KEYS[e.code];
    if (drive) {
      e.preventDefault();
      held.delete(drive);
    }
    if (e.code === "ShiftLeft" || e.code === "ShiftRight") slow = false;
    renderKeys();
    tick();
  }, true);

  // On-screen keys: hold with mouse or touch.
  document.querySelectorAll(".key").forEach((el) => {
    const k = el.dataset.key;
    const press = (e) => { e.preventDefault(); held.add(k); renderKeys(); tick(); };
    const release = () => { if (held.delete(k)) { renderKeys(); tick(); } };
    el.addEventListener("pointerdown", press);
    el.addEventListener("pointerup", release);
    el.addEventListener("pointerleave", release);
    el.addEventListener("pointercancel", release);
  });

  // Losing focus means we can't see key releases: stop.
  window.addEventListener("blur", releaseAll);
  document.addEventListener("visibilitychange", () => { if (document.hidden) releaseAll(); });

  $("btn-stop").onclick = releaseAll;
  $("btn-estop").onclick = () => { releaseAll(); send({ type: "estop" }); };
  $("btn-reset").onclick = () => send({ type: "reset" });
  $("btn-manual").onclick = () => send({ type: "manual", on: !(status && status.manual) });

  setInterval(tick, SEND_INTERVAL_MS);

  // ---- rendering ----------------------------------------------------------

  function setPill(id, text, cls) {
    const el = $(id);
    el.textContent = text;
    el.className = "pill" + (cls ? " " + cls : "");
  }

  function renderKeys() {
    document.querySelectorAll(".key").forEach((el) => el.classList.toggle("on", held.has(el.dataset.key)));
  }

  function renderSpeed() {
    document.querySelectorAll("#speed span").forEach((el) =>
      el.classList.toggle("on", Number(el.dataset.level) === speedLevel));
  }

  const fmt = (v, unit, digits = 1) => (v === null || v === undefined ? "–" : `${Number(v).toFixed(digits)}${unit}`);

  function render(s) {
    status = s;
    const modeCls = { error: "bad", manual: "warn", driving: "warn" }[s.mode] || "ok";
    setPill("mode", s.mode, modeCls);
    if (!s.body_connected) setPill("arduino", "Pi offline", "bad");
    else if (s.fault) setPill("arduino", "drive fault", "bad");
    else if (s.estop) setPill("arduino", "E-STOPPED", "bad");
    else if (!s.arduino_connected) setPill("arduino", "Arduino offline", "bad");
    else setPill("arduino", "drive ready", "ok");
    setPill("rtt", s.rtt_ms == null ? "ping –" : `ping ${s.rtt_ms} ms`, s.rtt_ms == null ? "" : s.rtt_ms < 50 ? "ok" : "warn");

    $("btn-manual").textContent = `Manual: ${s.manual ? "on" : "off"}`;
    $("btn-manual").classList.toggle("active", s.manual);
    $("btn-reset").hidden = !s.estop && !s.fault;

    const t = s.telemetry || {};
    const m = (t.motors && t.motors.firmware) || null;
    $("t-addr").textContent = s.body_addr || "–";
    $("t-temp").textContent = fmt(t.cpu_temp_c, " °C");
    $("t-volts").textContent = fmt(t.supply_v, " V", 2) + (t.throttled && t.throttled !== "0x0" ? `  (throttled ${t.throttled})` : "");
    $("t-wifi").textContent = t.wifi_dbm == null ? "–" : `${t.wifi_dbm} dBm`;
    $("t-pwm").textContent = m ? `L ${m.pwm[0]}  R ${m.pwm[1]}` : "–";
    $("t-ma").textContent = m ? `L ${m.ma[0]} mA  R ${m.ma[1]} mA` : "–";

    const cam = $("camera");
    let img = cam.querySelector("img");
    if (s.camera_url) {
      const retryDue = Date.now() - cameraFailedAt > 3000;
      if ((!img && retryDue) || (img && img.dataset.src !== s.camera_url)) {
        cam.innerHTML = "";
        img = document.createElement("img");
        img.alt = "TorQ camera";
        img.dataset.src = s.camera_url;
        img.src = s.camera_url;
        img.onerror = () => {
          cameraFailedAt = Date.now();
          cam.innerHTML = "<span>Camera stream unavailable, retrying…</span>";
        };
        cam.appendChild(img);
      }
    } else if (img) {
      cam.innerHTML = '<span>No camera stream</span>';
    }

    $("events").innerHTML = "";
    for (const ev of [...(s.events || [])].reverse()) {
      const li = document.createElement("li");
      li.textContent = `${new Date(ev.t * 1000).toLocaleTimeString()}  ${ev.text}`;
      $("events").appendChild(li);
    }
  }

  renderSpeed();
  connect();
})();
