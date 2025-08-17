const textContainer = document.querySelector(".text-container");
const texts = document.querySelectorAll(".text");
let currentIndex = 0;

function toggleText() {
  const currentText = texts[currentIndex];
  const nextIndex = (currentIndex + 1) % texts.length;
  const nextText = texts[nextIndex];

  // Remove the flip class from the current text
  currentText.classList.remove("flip");

  // Add the flip class to the next text after a small delay to trigger the flip animation
  setTimeout(() => {
    nextText.classList.add("flip");
  }, 10); // A small delay to ensure the flip animation applies

  currentIndex = nextIndex;
}

// Toggle the text every 2 seconds (2000 milliseconds)
setInterval(toggleText, 2000);

let b = document.getElementById("footimg1");
document.body.addEventListener("keydown", (press) => {
  if (press.key == "Escape") {
    window.location.href = "../index.html";
  }
});

const container = document.getElementById("body");
const divs = document.querySelectorAll(".a");

let currentIndeX = 0;

function scrollToIndex(index) {
  if (index >= 0 && index < divs.length) {
    divs[currentIndeX].classList.remove("highlighted");
    currentIndeX = index;
    divs[currentIndeX].classList.add("highlighted");
    divs[currentIndeX].scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  }
}

// body.addEventListener("click",function()=> {

// })

container.addEventListener("keydown", (event) => {
  if (event.key == "Enter" && currentIndeX == 0) {
    window.open(
      "https://abhinavpanwar.github.io/AMAZON_PRIME_CLONE/",
      "_blank"
    );
  }
  if (event.key == "Enter" && currentIndeX == 1) {
    window.open("https://utkarshpanwar.netlify.app/", "_blank");
  }
  if (event.key == "Enter" && currentIndeX == 2) {
    window.open("https://kingofcards.netlify.app/", "_blank");
  }
  if (event.key == "Enter" && currentIndeX == 3) {
    window.open("https://mediapedia.onrender.com", "_blank");
  }
  if (event.key == "Enter" && currentIndeX == 4) {
    window.open("https://onlinemultiplayer-tictactoe.onrender.com", "_blank");
  }
  if (event.key == "Enter" && currentIndeX == 5) {
    window.open("https://abhinavpanwar.github.io/Parallax/", "_blank");
  }
  if (event.key == "Enter" && currentIndeX == 6) {
    window.open("https://abhinavpanwar.github.io/AOT_QUIZ/", "_blank");
  }
  if (event.key == "Enter" && currentIndeX == 7) {
    window.open("https://mytierlist.netlify.app/", "_blank");
  }
  if (event.key == "Enter" && currentIndeX == 8) {
    window.open("https://virtua1assistant.netlify.app/", "_blank");
  }
  if (event.key === "ArrowUp") {
    scrollToIndex(currentIndeX - 1);
  } else if (event.key === "ArrowDown") {
    scrollToIndex(currentIndeX + 1);
  }
});

// Initial highlighting
divs[currentIndeX].classList.add("highlighted");

// section2

var slideIndex = 1;
var urls = [
  "https://github.com/ABHINAVpanwar/OCT-IMAGE-CLASSIFICATION",
  "https://github.com/ABHINAVpanwar/Enhanced-Surveillance-with-Real-Time-Object-Detection",
  "https://github.com/ABHINAVpanwar/Employee-management-system",
];
var captions = [
  "OCT Image Classification",
  "Real Time Object Detection",
  "Employee Management System",
];
showDivs(slideIndex);

function plusDivs(n) {
  showDivs((slideIndex += n));
}

function showDivs(n) {
  var i;
  var x = document.getElementsByClassName("mySlides");
  if (n > x.length) {
    slideIndex = 1;
  }
  if (n < 1) {
    slideIndex = x.length;
  }
  for (i = 0; i < x.length; i++) {
    x[i].style.display = "none";
    x[i].onclick = null;
  }
  x[slideIndex - 1].style.display = "block";
  x[slideIndex - 1].onclick = function () {
    window.open(urls[slideIndex - 1], "_blank");
  };
  document.getElementById("h2proj").innerText = captions[slideIndex - 1];
}

// Add event listeners for left and right arrow keys
document.addEventListener("keydown", function (event) {
  if (event.key === "ArrowLeft") {
    plusDivs(-1);
  } else if (event.key === "ArrowRight") {
    plusDivs(1);
  }
});
