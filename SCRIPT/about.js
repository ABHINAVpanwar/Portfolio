let hamMenuIcon = document.getElementById("ham-menu");
let navBar = document.getElementById("nav-bar");
let navLinks = navBar.querySelectorAll("li");
let midsec = document.getElementById("midsec");
let handles = document.getElementById("handles");

hamMenuIcon.addEventListener("click", () => {
  navBar.classList.toggle("active");
  hamMenuIcon.classList.toggle("fa-times");
  midsec.style.display = midsec.style.display === "none" ? "flex" : "none";
  handles.style.display = handles.style.display === "none" ? "flex" : "none";
  document.getElementById("FH").style.display =
    document.getElementById("FH").style.display === "none" ? "flex" : "none";
  document.getElementById("SH").style.display =
    document.getElementById("SH").style.display === "none" ? "flex" : "none";
  document.getElementById("B1").style.display =
    document.getElementById("B1").style.display === "none" ? "flex" : "none";
  document.getElementById("B2").style.display =
    document.getElementById("B2").style.display === "none" ? "flex" : "none";
  document.getElementById("chai-section").style.display =
    document.getElementById("chai-section").style.display === "none" ? "flex" : "none";
});
navLinks.forEach((navLinks) => {
  navLinks.addEventListener("click", () => {
    navBar.classList.remove("active");
    hamMenuIcon.classList.toggle("fa-times");
  });
});

// document.addEventListener("DOMContentLoaded", function () {
//   const header = document.querySelector("header");
//   const stickyNav = document.createElement("nav");
//   stickyNav.className = "sticky-nav"; // Add the same class as the transparent navigation

//   // Create a container for the logo and navigation links
//   const navContainer = document.createElement("div");
//   navContainer.className = "nav-container"; // Add a class for styling
//   navContainer.style.display = "flex"; // Apply display: flex
//   navContainer.style.justifyContent = "space-between"; // Apply justify-content: space-between
//   navContainer.style.alignItems = "center"; // Apply align-items: center

//   // Clone the logo from the main navigation and add a class to it
//   const logo = document.querySelector("a#logo").cloneNode(true);
//   logo.className = "logo"; // Add a class for styling

//   // Clone the navigation links from your main navigation
//   const navLinks = document.querySelector("ul#nav-bar").cloneNode(true);

//   // Append the logo to the navContainer
//   navContainer.appendChild(logo);

//   // Append the navigation links to the navContainer
//   navContainer.appendChild(navLinks);

//   // Append the navContainer to the sticky navigation
//   stickyNav.appendChild(navContainer);

//   // Apply styles to the sticky navigation container
//   stickyNav.style.position = "fixed"; // Change to "fixed" if needed
//   stickyNav.style.width = "100%";
//   stickyNav.style.top = "0";
//   stickyNav.style.left = "0";
//   stickyNav.style.backgroundColor = "rgba(0, 0, 0, 0.5)"; // Adjust this to your desired background color
//   stickyNav.style.padding = "3rem 5rem"; // Adjust the padding as needed
//   stickyNav.style.zIndex = "9999"; // Adjust the z-index as needed
//   stickyNav.style.display = "none"; // Initially hidden

//   // Add the sticky navigation to the body
//   document.body.appendChild(stickyNav);

//   // Function to show or hide the sticky navigation based on scroll position
//   function toggleStickyNav() {
//     if (window.pageYOffset > header.offsetHeight) {
//       stickyNav.style.display = "block";
//     } else {
//       stickyNav.style.display = "none";
//     }
//   }

//   // Initial check for the sticky navigation
//   toggleStickyNav();

//   // Listen to scroll events to toggle the sticky navigation
//   window.addEventListener("scroll", toggleStickyNav);
// });

// Function to animate the skill bar
function increaseSkillBar(id, targetWidth) {
  const bar = document.getElementById(id);
  let width = 0;

  const interval = setInterval(function () {
    if (width >= targetWidth) {
      clearInterval(interval);
    } else {
      width++;
      bar.style.width = width + "%";
    }
  }, 10); // Increase the value inside setTimeout for a faster/slower animation
}

let skillBarsAnimated = true;

function toggleSkillbar() {
  if (skillBarsAnimated && window.pageYOffset > S1.offsetHeight * 1.5) {
    increaseSkillBar("F", 80);
    increaseSkillBar("SM", 60);
    increaseSkillBar("TM", 70);
    increaseSkillBar("PS", 80);
    increaseSkillBar("DM", 60);
    increaseSkillBar("C", 70);

    skillBarsAnimated = false;
  }
}

toggleSkillbar();

window.addEventListener("scroll", toggleSkillbar);

let One = document.getElementById("exp");
let Two = document.getElementById("edu");
let Three = document.getElementById("int");
let first = document.getElementById("experience");
let middle = document.getElementById("education");
let last = document.getElementById("interest");

function f1() {
  Two.style.display = "none";
  Three.style.display = "none";
  One.style.display = "block";
  middle.style.backgroundColor = "white";
  last.style.backgroundColor = "white";
  first.style.backgroundColor = "#4caf50";
}

function f2() {
  One.style.display = "none";
  Three.style.display = "none";
  Two.style.display = "block";
  first.style.backgroundColor = "white";
  last.style.backgroundColor = "white";
  middle.style.backgroundColor = "#4caf50";
}

function f3() {
  One.style.display = "none";
  Two.style.display = "none";
  Three.style.display = "block";
  first.style.backgroundColor = "white";
  middle.style.backgroundColor = "white";
  last.style.backgroundColor = "#4caf50";
}

let slideIndex = 1;
showSlides(slideIndex);

function plusSlides(n) {
  showSlides((slideIndex += n));
}

function currentSlide(n) {
  showSlides((slideIndex = n));
}

function showSlides(n) {
  let i;
  let slides = document.getElementsByClassName("mySlides");
  if (n > slides.length) {
    slideIndex = 1;
  }
  if (n < 1) {
    slideIndex = slides.length;
  }
  for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";
  }
  slides[slideIndex - 1].style.display = "block";
}
