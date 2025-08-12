// Preloader and initial setup
window.addEventListener("load", function () {
  // Hide preloader first
  this.document.getElementById("preloader").style.display = "none";

  // Then hide other elements
  this.document.getElementById("PL").style.display = "none";
  this.document.getElementById("ASHOK_CHAKRA").style.display = "none";

  // Show popup immediately after preloader
  setTimeout(function () {
    showPopup();
  }, 0);

  // Close popup after 4 seconds
  setTimeout(function () {
    closePopup();
  }, 4000);

  // Show images after popup closes
  setTimeout(function () {
    var img = document.getElementById("contactmeimg");
    var img2 = document.getElementById("joystickimg");
    var activeusers = document.getElementById("active-users-counter");
    img.classList.add("visible");
    img2.classList.add("visible");
    activeusers.classList.add("visible");
    setTimeout(function () {
      img.classList.add("hover-effect");
      img2.classList.add("hover-effect");
      activeusers.classList.add("hover-effect");
    }, 0);
    // Show overlay after delay
    setTimeout(() => {
      if (document.getElementById("survey-options").children.length > 0) {
        document.getElementById("survey-overlay").style.display = "flex";
        if (window.innerWidth <= 767) {
          document.getElementById("ham-menu").style.display = "block";
        }
      }
    }, 5000); // 5 sec delay
    if (document.getElementById("survey-options").children.length == 0) {
      if (window.innerWidth <= 767) {
        document.getElementById("ham-menu").style.display = "block";
      }
    }
  }, 5000);

  // Show headings after delay
  const delay = 5000;
  const elements = ["h1", "h2", "h3"]
    .map((id) => document.getElementById(id))
    .filter((el) => el !== null);

  setTimeout(() => {
    elements.forEach((el) => el.classList.add("visible"));
  }, delay);
});

// Video background handling
document.addEventListener("DOMContentLoaded", function () {
  const video = document.getElementById("video-bg");
  video.addEventListener("error", function () {
    document.body.classList.add("no-video");
  });

  // For mobile devices where autoplay might be blocked
  if (video.paused) {
    document.body.classList.add("no-video");
  }
});

// Sound effects
function playSound() {
  document
    .getElementById("preloadSound")
    .play()
    .catch((error) => {
      console.error("Error playing sound:", error);
    });
}

document.getElementById("PL").addEventListener("click", playSound);
document.getElementById("ASHOK_CHAKRA").addEventListener("click", playSound);

// Popup functions
function showPopup() {
  TP.style.display = "none";
  document.getElementById("Post").style.display = "none";
  document.getElementById("overlay").style.display = "block";
  document.getElementById("popup").style.display = "block";
  document.body.style.cursor = "pointer";
  setTimeout(function () {
    document.getElementById("popup").classList.add("popup-show");
  }, 100);
}

function closePopup() {
  document.getElementById("popup").classList.remove("popup-show");
  setTimeout(function () {
    document.getElementById("overlay").style.display = "none";
    document.getElementById("popup").style.display = "none";
    TP.style.display = "block";
    document.getElementById("Post").style.display = "block";
    document.body.style.cursor = "default";
  }, 500);
}

// Hamburger menu functionality
let hamMenuIcon = document.getElementById("ham-menu");
let navBar = document.getElementById("nav-bar");
let navLinks = navBar.querySelectorAll("li");
let TP = document.getElementById("TP");
let Post = document.getElementById("Post");
let CMI = document.getElementById("contactmeimg");
var overlay = document.getElementById("overlay2");
var formContainer = document.getElementById("S7");

hamMenuIcon.addEventListener("click", () => {
  navBar.classList.toggle("active");
  hamMenuIcon.classList.toggle("fa-times");
  TP.style.display = TP.style.display === "none" ? "block" : "none";
  Post.style.display = Post.style.display === "none" ? "block" : "none";
  CMI.style.display = CMI.style.display === "none" ? "block" : "none";
  if (document.getElementById("survey-overlay").style.display === "flex") {
    document.getElementById("survey-overlay").style.display = "none";
  }
  if (overlay.style.display === "block") {
    overlay.style.display = "none";
  }
  if (formContainer.style.display === "block") {
    formContainer.style.display = "none";
  }
});

navLinks.forEach((navLinks) => {
  navLinks.addEventListener("click", () => {
    navBar.classList.remove("active");
    hamMenuIcon.classList.toggle("fa-times");
  });
});

// Contact form functionality
document.getElementById("contactmeimg").addEventListener("click", function () {
  var isVisible = formContainer.style.display === "block";

  if (isVisible) {
    formContainer.style.opacity = "0";
    setTimeout(function () {
      formContainer.style.display = "none";
      overlay.style.display = "none";
    }, 500);
  } else {
    formContainer.style.display = "block";
    overlay.style.display = "block";
    setTimeout(function () {
      formContainer.style.opacity = "1";
    }, 10);
  }
});

document.getElementById("overlay2").addEventListener("click", function () {
  var overlay = document.getElementById("overlay2");
  var formContainer = document.getElementById("S7");

  formContainer.style.opacity = "0";
  setTimeout(function () {
    formContainer.style.display = "none";
    overlay.style.display = "none";
  }, 500);
});

document.addEventListener("DOMContentLoaded", async () => {
  try {
    // Fetch and display the headline
    const response = await fetch(
      "https://abhinavpanwar.onrender.com/api/get_h3"
    );
    const { h3_text } = await response.json();
    document.getElementById("h3").textContent = h3_text;
  } catch (error) {
    console.error("Error loading headline:", error);
    document.getElementById("h3").textContent = "";
  }
});

// Load and display survey
async function loadSurvey() {
  try {
    const response = await fetch(
      "https://abhinavpanwar.onrender.com/api/current_poll"
    );

    if (!response.ok) {
      // window.addEventListener("load", function () {
      //   setTimeout(() => {
      //     if (window.innerWidth <= 767) {
      //       document.getElementById("ham-menu").style.display = "block";
      //     }
      //   }, 5000); // 5 sec delay
      // });
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.error) {
      console.log("No active poll available");
      return;
    }

    // Display survey question and options
    document.getElementById("survey-question").textContent = data.question;
    const optionsContainer = document.getElementById("survey-options");
    optionsContainer.innerHTML = "";

    data.options.forEach((option, index) => {
      const button = document.createElement("button");
      button.textContent = option;

      button.addEventListener("click", async () => {
        await submitResponse(index, button);
      });

      optionsContainer.appendChild(button);
    });
  } catch (error) {
    console.error("Error loading survey:", error);
  }
}

// Submit survey response
async function submitResponse(index, button) {
  const optionsContainer = document.getElementById("survey-options");

  try {
    button.disabled = true;
    button.style.opacity = "0.7";

    const response = await fetch(
      "https://abhinavpanwar.onrender.com/api/submit_response",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ option_index: index }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || "Failed to submit response");
    }

    // Show thank-you message (will stay until user closes manually)
    optionsContainer.innerHTML =
      '<p style="text-align:center; color:#4caf50;">Thank you for your feedback!</p>';
  } catch (error) {
    console.error("Error submitting response:", error);
    button.disabled = false;
    button.style.opacity = "1";

    const errorElement = document.createElement("p");
    errorElement.style.color = "#f44336";
    errorElement.style.textAlign = "center";
    errorElement.textContent =
      error.message || "Submission failed. Please try again.";
    optionsContainer.appendChild(errorElement);

    setTimeout(() => {
      if (errorElement.parentNode) {
        errorElement.remove();
      }
    }, 5000);
  }
}

// Manual close button handler
document.getElementById("survey-close").addEventListener("click", () => {
  const overlay = document.getElementById("survey-overlay");
  overlay.style.opacity = "0";

  setTimeout(() => {
    overlay.style.display = "none";
    overlay.style.opacity = "1";
  }, 500); // fast fade-out
});

// Load survey when DOM is ready
window.addEventListener("DOMContentLoaded", loadSurvey);
