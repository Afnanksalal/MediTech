$(document).ready(function () {
  let slideIndex = 0;
  const images = $(".image-carousel img");
  const prevBtn = $(".image-carousel .prev");
  const nextBtn = $(".image-carousel .next");

  function showSlide(index) {
    images.removeClass("active").eq(index).addClass("active");
  }

  function nextSlide() {
    slideIndex = (slideIndex + 1) % images.length;
    showSlide(slideIndex);
  }

  function prevSlide() {
    slideIndex = (slideIndex - 1 + images.length) % images.length;
    showSlide(slideIndex);
  }

  nextBtn.on("click", nextSlide);
  prevBtn.on("click", prevSlide);

  setInterval(nextSlide, 5000); // Auto-slide every 5 seconds
});
