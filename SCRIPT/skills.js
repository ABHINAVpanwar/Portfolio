// Mobile Menu Toggle
const hamMenuIcon = document.getElementById("ham-menu");
const navBar = document.getElementById("nav-bar");
const navLinks = navBar.querySelectorAll("li");

hamMenuIcon.addEventListener("click", () => {
  navBar.classList.toggle("active");
  hamMenuIcon.classList.toggle("fa-times");
  document.getElementById("skills-section").style.display =
    document.getElementById("skills-section").style.display === "none"
      ? "block"
      : "none";
});

navLinks.forEach((navLink) => {
  navLink.addEventListener("click", () => {
    navBar.classList.remove("active");
    hamMenuIcon.classList.remove("fa-times");
  });
});
