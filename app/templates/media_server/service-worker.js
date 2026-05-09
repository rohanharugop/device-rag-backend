self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open("media-cache").then((cache) => {
      return cache.addAll(["./", "index.html", "app.js"]);
    })
  );
});