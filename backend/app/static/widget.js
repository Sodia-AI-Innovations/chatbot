(function () {
  "use strict";

  var script = document.currentScript || document.querySelector('script[src*="widget.js"]');
  if (!script) return;

  var url = new URL(script.src);
  var token = (url.searchParams.get("token") || "").trim();
  var api = url.origin + "/widget/chat";

  if (!token) {
    console.warn("[chatbot] Missing token in script src.");
    return;
  }
  if (document.getElementById("rb-root")) return;

  var CSS = [
    "#rb-root{all:initial;font-family:Inter,system-ui,-apple-system,'Segoe UI',sans-serif}",
    "#rb-root *{box-sizing:border-box;font-family:inherit}",

    /* ---- floating button ---- */
    "#rb-fab{position:fixed;right:22px;bottom:22px;z-index:2147483000;animation:rb-float 3s ease-in-out infinite}",
    "#rb-btn{position:relative;width:62px;height:62px;border:0;border-radius:50%;cursor:pointer;color:#fff;",
      "background:linear-gradient(135deg,#f0abfc,#d946ef);display:grid;place-items:center;",
      "animation:rb-ring 2.4s ease-out infinite;transition:transform .25s cubic-bezier(.34,1.56,.64,1)}",
    "#rb-btn:hover{transform:scale(1.12) rotate(-6deg)}",
    "#rb-btn:active{transform:scale(.94)}",
    "#rb-btn svg{position:absolute;width:28px;height:28px;transition:transform .35s ease,opacity .25s ease}",
    ".rb-ic-close{opacity:0;transform:rotate(-90deg) scale(.5)}",
    "#rb-root.open .rb-ic-chat{opacity:0;transform:rotate(90deg) scale(.5)}",
    "#rb-root.open .rb-ic-close{opacity:1;transform:rotate(0) scale(1)}",
    "#rb-root.open #rb-fab{animation:none}",
    "#rb-root.open #rb-btn{animation:none;box-shadow:0 10px 26px rgba(217,70,239,.4)}",
    "@keyframes rb-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}",
    "@keyframes rb-ring{",
      "0%{box-shadow:0 0 0 0 rgba(217,70,239,.55),0 12px 30px rgba(217,70,239,.4)}",
      "70%{box-shadow:0 0 0 20px rgba(217,70,239,0),0 12px 30px rgba(217,70,239,.4)}",
      "100%{box-shadow:0 0 0 0 rgba(217,70,239,0),0 12px 30px rgba(217,70,239,.4)}}",

    /* ---- greeting bubble ---- */
    "#rb-greet{position:fixed;right:22px;bottom:96px;z-index:2147483000;background:#fff;color:#4a044e;",
      "font-size:13px;font-weight:600;padding:10px 14px;border-radius:14px 14px 4px 14px;cursor:pointer;",
      "box-shadow:0 10px 30px rgba(74,4,78,.18);opacity:0;transform:translateY(10px) scale(.9);",
      "pointer-events:none;transition:opacity .3s ease,transform .3s ease}",
    "#rb-greet.show{opacity:1;transform:none;pointer-events:auto}",

    /* ---- panel ---- */
    "#rb-panel{position:fixed;right:22px;bottom:98px;z-index:2147483000;width:min(380px,calc(100vw - 24px));",
      "height:min(560px,calc(100vh - 120px));display:flex;flex-direction:column;overflow:hidden;",
      "border-radius:28px;background:#fff;box-shadow:0 24px 60px rgba(74,4,78,.28);",
      "transform-origin:bottom right;opacity:0;visibility:hidden;pointer-events:none;",
      "transform:translateY(18px) scale(.92);transition:opacity .25s ease,transform .3s cubic-bezier(.34,1.3,.64,1),visibility 0s .3s}",
    "#rb-root.open #rb-panel{opacity:1;visibility:visible;pointer-events:auto;transform:none;transition-delay:0s}",

    /* ---- header ---- */
    "#rb-head{position:relative;display:flex;align-items:center;gap:6px;padding:14px 16px;color:#fff;",
      "background:linear-gradient(135deg,#f0abfc,#e040fb)}",
    "#rb-title{flex:1;font-size:15px;font-weight:600;padding-left:4px}",
    ".rb-hbtn{width:34px;height:34px;border:0;border-radius:50%;background:transparent;color:#fff;cursor:pointer;",
      "display:grid;place-items:center;transition:background .2s}",
    ".rb-hbtn:hover{background:rgba(255,255,255,.22)}",
    ".rb-hbtn svg{width:20px;height:20px}",
    "#rb-menu{position:absolute;right:48px;top:52px;background:#fff;color:#4a044e;border-radius:12px;",
      "box-shadow:0 10px 30px rgba(74,4,78,.22);padding:6px;display:none;z-index:2}",
    "#rb-menu.show{display:block}",
    "#rb-menu button{border:0;background:transparent;color:inherit;font-size:13px;padding:8px 14px;",
      "border-radius:8px;cursor:pointer;white-space:nowrap}",
    "#rb-menu button:hover{background:#fdf0ff}",

    /* ---- messages ---- */
    "#rb-msgs{flex:1;overflow-y:auto;padding:18px 22px;background:#fff;scroll-behavior:smooth}",
    ".rb-msg{position:relative;max-width:82%;margin:0 0 14px;padding:11px 14px;border-radius:16px;",
      "font-size:13.5px;line-height:1.5;white-space:pre-wrap;word-wrap:break-word;animation:rb-pop .28s ease both}",
    ".rb-bot{margin-right:auto;margin-left:6px;background:#fdd4ff;color:#4a044e;border-bottom-left-radius:4px}",
    ".rb-bot::after{content:'';position:absolute;left:-7px;bottom:0;width:12px;height:12px;background:#fdd4ff;",
      "clip-path:polygon(100% 0,100% 100%,0 100%)}",
    ".rb-user{margin-left:auto;margin-right:6px;background:#f79cff;color:#3b0a40;border-bottom-right-radius:4px}",
    ".rb-user::after{content:'';position:absolute;right:-7px;bottom:0;width:12px;height:12px;background:#f79cff;",
      "clip-path:polygon(0 0,100% 100%,0 100%)}",
    "@keyframes rb-pop{from{opacity:0;transform:translateY(8px) scale(.96)}to{opacity:1;transform:none}}",

    /* ---- typing dots ---- */
    ".rb-typing{display:inline-flex;gap:4px;align-items:center;height:18px}",
    ".rb-typing i{width:7px;height:7px;border-radius:50%;background:#c026d3;opacity:.4;animation:rb-bounce 1.2s infinite}",
    ".rb-typing i:nth-child(2){animation-delay:.15s}",
    ".rb-typing i:nth-child(3){animation-delay:.3s}",
    "@keyframes rb-bounce{0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-5px);opacity:1}}",

    /* ---- input ---- */
    "#rb-foot{border-top:1px solid #f1e6f3;padding:12px 14px;background:#fff}",
    "#rb-form{display:flex;align-items:center;gap:6px;border:1.5px solid #ecdcef;border-radius:999px;",
      "padding:5px 6px 5px 16px;transition:border-color .2s,box-shadow .2s}",
    "#rb-form:focus-within{border-color:#e040fb;box-shadow:0 0 0 3px rgba(224,64,251,.15)}",
    "#rb-input{flex:1;min-width:0;border:0;outline:none;background:transparent;font-size:13.5px;color:#2b0a30;padding:7px 0}",
    "#rb-input::placeholder{color:#b9a3be}",
    "#rb-send{width:36px;height:36px;border:0;border-radius:50%;background:transparent;color:#d946ef;cursor:pointer;",
      "display:grid;place-items:center;transition:transform .2s,background .2s}",
    "#rb-send:hover{background:#fdf0ff;transform:scale(1.1)}",
    "#rb-send:disabled{opacity:.4;cursor:default;transform:none}",
    "#rb-send svg{width:20px;height:20px}",

    "@media (prefers-reduced-motion:reduce){#rb-root *{animation:none!important;transition:none!important}}"
  ].join("");

  var ICON_CHAT = '<svg class="rb-ic-chat" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8z"/></svg>';
  var ICON_X = '<svg class="rb-ic-close" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>';
  var ICON_DOWN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>';
  var ICON_DOTS = '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>';
  var ICON_X_SM = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>';
  var ICON_SEND = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M2.5 20.5l19-8.5-19-8.5v6.6l13 1.9-13 1.9z"/></svg>';

  var WELCOME = "Hi! Ask me anything about the uploded document.";

  function boot() {
    var style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);

    var root = document.createElement("div");
    root.id = "rb-root";
    root.innerHTML =
      '<div id="rb-panel" role="dialog" aria-label="Chat">' +
        '<div id="rb-head">' +
          '<button class="rb-hbtn" id="rb-min" type="button" aria-label="Minimize">' + ICON_DOWN + '</button>' +
          '<div id="rb-title">Ask us anything</div>' +
          '<button class="rb-hbtn" id="rb-more" type="button" aria-label="Menu">' + ICON_DOTS + '</button>' +
          '<button class="rb-hbtn" id="rb-close" type="button" aria-label="Close">' + ICON_X_SM + '</button>' +
          '<div id="rb-menu"><button type="button" id="rb-clear">Clear chat</button></div>' +
        '</div>' +
        '<div id="rb-msgs"></div>' +
        '<div id="rb-foot"><form id="rb-form" autocomplete="off">' +
          '<input id="rb-input" placeholder="Type your message..." maxlength="1000" />' +
          '<button id="rb-send" type="submit" aria-label="Send">' + ICON_SEND + '</button>' +
        '</form></div>' +
      '</div>' +
      '<div id="rb-greet">Need help? Ask me!</div>' +
      '<div id="rb-fab"><button id="rb-btn" type="button" aria-label="Open chat">' + ICON_CHAT + ICON_X + '</button></div>';
    document.body.appendChild(root);

    var $ = function (id) { return root.querySelector(id); };
    var msgs = $("#rb-msgs"), form = $("#rb-form"), input = $("#rb-input"), send = $("#rb-send");
    var btn = $("#rb-btn"), greet = $("#rb-greet"), menu = $("#rb-menu");

    function addBubble(role, text) {
      var div = document.createElement("div");
      div.className = "rb-msg " + (role === "user" ? "rb-user" : "rb-bot");
      div.textContent = text;
      msgs.appendChild(div);
      msgs.scrollTop = msgs.scrollHeight;
      return div;
    }

    function addTyping() {
      var div = document.createElement("div");
      div.className = "rb-msg rb-bot";
      div.innerHTML = '<span class="rb-typing"><i></i><i></i><i></i></span>';
      msgs.appendChild(div);
      msgs.scrollTop = msgs.scrollHeight;
      return div;
    }

    function setOpen(open) {
      root.classList.toggle("open", open);
      greet.classList.remove("show");
      menu.classList.remove("show");
      if (open) setTimeout(function () { input.focus(); }, 300);
    }

    function reset() {
      msgs.innerHTML = "";
      addBubble("bot", WELCOME);
    }

    btn.addEventListener("click", function () { setOpen(!root.classList.contains("open")); });
    greet.addEventListener("click", function () { setOpen(true); });
    $("#rb-min").addEventListener("click", function () { setOpen(false); });
    $("#rb-close").addEventListener("click", function () { setOpen(false); reset(); });
    $("#rb-more").addEventListener("click", function () { menu.classList.toggle("show"); });
    $("#rb-clear").addEventListener("click", function () { menu.classList.remove("show"); reset(); });

    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      var q = input.value.trim();
      if (!q || send.disabled) return;
      input.value = "";
      send.disabled = true;
      addBubble("user", q);
      var typing = addTyping();
      try {
        var res = await fetch(api, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token: token, question: q })
        });
        var data = await res.json();
        typing.remove();
        addBubble("bot", res.ok ? data.answer : (data.message || "Something went wrong."));
      } catch (err) {
        typing.remove();
        addBubble("bot", "Network error. Please try again.");
      }
      send.disabled = false;
      input.focus();
    });

    reset();

    // greeting nudge, once per browser session
    try {
      if (!sessionStorage.getItem("rb-greeted")) {
        setTimeout(function () {
          if (!root.classList.contains("open")) greet.classList.add("show");
          sessionStorage.setItem("rb-greeted", "1");
          setTimeout(function () { greet.classList.remove("show"); }, 6000);
        }, 1800);
      }
    } catch (err) { /* storage blocked: skip the nudge */ }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();