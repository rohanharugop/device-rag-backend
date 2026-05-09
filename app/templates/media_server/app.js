async function loadConfig() {
  const res = await fetch("config.json");
  return res.json();
}

async function init() {
  const config = await loadConfig();

  document.getElementById("title").innerText =
    config.device_name + " Media Hub";

  const input = document.getElementById("fileInput");
  const player = document.getElementById("player");

  input.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      player.src = url;
    }
  });
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("service-worker.js");
}

init();