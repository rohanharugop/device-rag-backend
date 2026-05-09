async function loadConfig() {
  const res = await fetch("config.json");
  return res.json();
}

async function startCamera() {
  try {
    const config = await loadConfig();

    document.getElementById("title").innerText =
      config.device_name + " - Camera";

    const video = document.getElementById("video");

    const stream = await navigator.mediaDevices.getUserMedia({
      video: true
    });

    video.srcObject = stream;

  } catch (err) {
    alert("Camera access failed: " + err.message);
  }
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("service-worker.js");
}

startCamera();