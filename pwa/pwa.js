if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker
        .register("/pwa/service-worker.js")
        .then(() => console.log("✅ Service Worker registered"))
        .catch((err) => console.error("SW registration failed: ", err));
    });
  }
  