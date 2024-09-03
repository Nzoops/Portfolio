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