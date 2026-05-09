self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open("dashboard-cache").then((cache) => {
      return cache.addAll(["./", "index.html", "app.js"]);
    })
  );
});