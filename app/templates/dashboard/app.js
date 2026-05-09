async function loadConfig() {
  const res = await fetch("config.json");
  return res.json();
}

function startClock() {
  setInterval(() => {
    document.getElementById("clock").innerText =
      new Date().toLocaleTimeString();
  }, 1000);
}

async function init() {
  const config = await loadConfig();

  document.getElementById("device").innerText =
    config.device_name + " Dashboard";

  document.getElementById("note").innerText =
    "Capabilities: " + config.capabilities.join(", ");

  startClock();
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("service-worker.js");
}

init();