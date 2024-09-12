const carousel = document.querySelector('.carousel');
let scrollAmount = 0;

function scrollLeft() {
  carousel.scrollBy({
    top: 0,
    left: -150, // Adjust scroll distance
    behavior: 'smooth'
  });
}

function scrollRight() {
  carousel.scrollBy({
    top: 0,
    left: 150, // Adjust scroll distance
    behavior: 'smooth'
  });
}

document.querySelector('.scroll-left').addEventListener('click', scrollLeft);
document.querySelector('.scroll-right').addEventListener('click', scrollRight);

//script.js

// The text you want to display in typewriter effect
const text = "I love building tech products that make technical topics look simple.";

// Select the paragraph element where text will appear
const typewriterElement = document.querySelector('#typewriter p');

let index = 0;

// Function to gradually display the text character by character
function type() {
  if (index < text.length) {
    typewriterElement.textContent += text.charAt(index); // Add one character at a time
    index++;
    setTimeout(type, 100); // Adjust typing speed by changing the timeout value
  }
}

// Call the type function when the window loads
window.onload = type;