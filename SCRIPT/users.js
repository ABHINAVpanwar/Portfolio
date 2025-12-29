// Add this to all page links
document.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    document.body.classList.add("fade-out");
    setTimeout(() => (window.location = link.href), 500);
  });
});

// Real-Time Active Users Tracker (v2.2 - Removed Ping Logic)
class ActiveUsersTracker {
  static init() {
    this.API_URL = "https://abhinavpanwar.onrender.com/api/active_users";
    this.POLL_INTERVAL = 5000;
    this.EXIT_DELAY = 2000;
    this.ANIMATION_DURATION = 800;

    this.deviceId = this.getCookie("device_id") || crypto.randomUUID();
    this.lastActive = Date.now();
    this.exitTimer = null;
    this.counterElement = document.getElementById("activeUsers");

    this.startSession();
    this.setupEventListeners();
    this.startPolling();
  }

  static startSession() {
    if (!this.getCookie("device_id")) {
      document.cookie = `device_id=${this.deviceId}; max-age=${
        365 * 24 * 60 * 60
      }; path=/; Secure; SameSite=None`;
    }
  }

  static setupEventListeners() {
    const activityEvents = [
      "mousemove",
      "scroll",
      "click",
      "keydown",
      "touchstart",
    ];
    activityEvents.forEach((evt) => {
      document.addEventListener(evt, () => {
        this.lastActive = Date.now();
        this.cancelExitCheck();
      });
    });

    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        this.scheduleExitCheck();
      } else {
        this.cancelExitCheck();
      }
    });

    window.addEventListener("beforeunload", () => this.endSession());
    window.addEventListener("pagehide", () => this.endSession());
  }

  static startPolling() {
    this.updateCounter();
    setInterval(() => this.updateCounter(), this.POLL_INTERVAL);
  }

  static async updateCounter() {
    try {
      const response = await fetch(this.API_URL, {
        method: "GET",
        credentials: "include",
        headers: { Accept: "application/json" },
        cache: "no-store",
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      this.animateCounter(data.active_users);
    } catch (error) {
      console.error("Counter update failed:", error);
      if (this.counterElement) this.counterElement.textContent = "~";
    }
  }

  static async endSession() {
    try {
      await fetch(`${this.API_URL}/end`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ device_id: this.deviceId }),
        keepalive: true,
      });
    } catch (error) {
      console.error("Session end failed:", error);
      navigator.sendBeacon(
        `${this.API_URL}/end`,
        JSON.stringify({ device_id: this.deviceId })
      );
    }
  }

  static scheduleExitCheck() {
    this.cancelExitCheck();
    this.exitTimer = setTimeout(() => {
      if (document.hidden) this.endSession();
    }, this.EXIT_DELAY);
  }

  static cancelExitCheck() {
    if (this.exitTimer) clearTimeout(this.exitTimer);
  }

  static animateCounter(newCount) {
    if (!this.counterElement) return;
    const current = parseInt(this.counterElement.textContent) || 0;
    const startTime = performance.now();

    const updateFrame = (timestamp) => {
      const progress = Math.min(
        (timestamp - startTime) / this.ANIMATION_DURATION,
        1
      );
      this.counterElement.textContent = Math.floor(
        current + (newCount - current) * progress
      );
      if (progress < 1) requestAnimationFrame(updateFrame);
    };
    requestAnimationFrame(updateFrame);
  }

  static getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
  }
}

// Initialize with error handling
document.addEventListener("DOMContentLoaded", () => {
  try {
    ActiveUsersTracker.init();
  } catch (error) {
    console.error("Tracker initialization failed:", error);
  }
});

// Add this to your main JavaScript file
window.addEventListener("pageshow", function (event) {
  // If the page was loaded from cache (back/forward navigation)
  if (event.persisted) {
    window.location.reload();
  }
});
