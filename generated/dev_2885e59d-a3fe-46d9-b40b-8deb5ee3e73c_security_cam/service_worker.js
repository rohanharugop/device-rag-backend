self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open("camera-cache").then((cache) => {
      return cache.addAll(["./", "index.html", "app.js"]);
    })
  );
});