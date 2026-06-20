/**
 * Fuzio || Sports Club  HTML Template
 *
 * @author themeVillage (www.theme-village.com)
 * @version 1.0.0
 **/

"use strict"

window.addEventListener("load", function () {
  var preloader = document.getElementById("preloader")
  preloader.style.display = "none"
  document.body.style.overflow = "visible"
})

/**
 * Scroll to Top
 */
const backTotop = (function () {
  let scrollpos = window.scrollY
  let backBtn = document.querySelector(".back-top")
  if (backBtn) {
    let add_class_on_scroll = () => backBtn.classList.add("back-top-show")
    let remove_class_on_scroll = () => backBtn.classList.remove("back-top-show")

    window.addEventListener("scroll", function () {
      scrollpos = window.scrollY
      if (scrollpos >= 800) {
        add_class_on_scroll()
      } else {
        remove_class_on_scroll()
      }
    })

    backBtn.addEventListener("click", () =>
      window.scrollTo({
        top: 0,
        behavior: "smooth",
      })
    )
  }
})();


if (document.querySelectorAll(".wow").length > 0) {
  var wow = new WOW({
    boxClass: "wow",
    animateClass: "animated", // ← use "animate__animated" if you're on Animate.css v4
    offset: 0,
    mobile: true,
    live: true,
  });
  wow.init();
}

let revealContainers = document.querySelectorAll(".reveal");

if (revealContainers.length) {
  revealContainers.forEach((container) => {
    let image = container.querySelector("img");

    let tl = gsap.timeline({
      scrollTrigger: {
        trigger: container,
        toggleActions: "play none none none"
      }
    });

    tl.set(container, { autoAlpha: 1 });

    tl.from(container, {
      duration: 1,
      xPercent: -100,
      ease: Power2.out
    });

    tl.from(image, {
      duration: 1,
      xPercent: 100,
      scale: 1,
      delay: -1,
      ease: Power2.out
    });
  });
}

/**
 * Text Animation
 */

if (document.querySelectorAll('.text-anim').length > 0) {
  let staggerAmount = 0.05,
    delayValue = 0.5,
    animatedTextElements = document.querySelectorAll('.text-anim');

  animatedTextElements.forEach((element) => {
    let animationSplitText = new SplitText(element, { type: "chars, words" });
    gsap.from(animationSplitText.words, {
      duration: 1,
      delay: delayValue,
      x: 20,
      autoAlpha: 0,
      stagger: staggerAmount,
      scrollTrigger: {
        trigger: element,
        start: "top 85%"
      },
    });
  });
}


let animatedTextElements = document.querySelectorAll('.sec-title');

if (animatedTextElements.length) {  
  let staggerAmount = 0.03,
    translateXValue = 20,
    delayValue = 0.1,
    easeType = "power2.out";

  animatedTextElements.forEach((element) => {
    let animationSplitText = new SplitText(element, { type: "chars, words" });
    gsap.from(animationSplitText.chars, {
      duration: 1,
      delay: delayValue,
      x: translateXValue,
      autoAlpha: 0,
      stagger: staggerAmount,
      ease: easeType,
      scrollTrigger: { trigger: element, start: "top 85%" },
    });
  });
}

/**
 * Counter Up
 */
new PureCounter({
  selector: ".purecounter",
  delay: 200,
})
/**
 * Jarallax Parallax
 */
jarallax(document.querySelectorAll(".jarallax"), {
  speed: 0.5,
  imgPosition: "50% -30%",
  imgSize: "cover",
})

jarallax(document.querySelectorAll('.promo-sec.jarallax'), {
  speed: 0.1,
});
/**
 * Tooltip
 */
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})
/**
 * Testimonial Slider
 */

const testimonial = new Swiper(".testimonial-slider", {
  navigation: {
    nextEl: ".swiper-button-next",
    prevEl: ".swiper-button-prev",
  },
})
/**
 * Brand Slider Home (Cricket)
 */
const brand = new Swiper(".brand-slider", {
  spaceBetween: 20,
  autoplay: {
    delay: 1500,
  },
  loop: true,
  breakpoints: {
    // when window width is >= 320px
    320: {
      slidesPerView: 1,
    },
    480: {
      slidesPerView: 2,
    },
    768: {
      slidesPerView: 3,
    },
    992: {
      slidesPerView: 5,
    },
  },
})
/**
 * Match Schdule Carousel (Cricket)
 */
const matchCarousel = new Swiper(".match-carousel", {
  spaceBetween: 30,
  autoplay: {
    delay: 1500,
  },
  loop: true,
  pagination: {
    el: ".swiper-pagination",
    clickable: true,
  },
  breakpoints: {
    // when window width is >= 320px
    320: {
      slidesPerView: 1,
      spaceBetween: 0,
    },
    // when window width is >= 480px
    768: {
      slidesPerView: 2,
    },
    // when window width is >= 640px
    992: {
      slidesPerView: 3,
    },
  },
})

/**
 * VenoBox Init
 */

let cricketBG = new VenoBox({
  selector: ".cover-video",
  autoplay: true,
  maxWidth: "1000px",
})
let cricketGallery = new VenoBox({
  selector: ".my-image-links",
  numeration: true,
  infinigall: true,
  share: true,
  spinner: "rotating-plane",
})

/**
 * Nice Select 2
 */
let niceSelector = document.getElementById("select")
if (niceSelector) {
  NiceSelect.bind(niceSelector, {
    placeholder: "Language",
  })
}

let formSelect = document.getElementById("select-options")
if (formSelect) {
  NiceSelect.bind(formSelect)
}

// Result Select (Shop)
let resultSelect = document.getElementById("result-select")
if (resultSelect) {
  NiceSelect.bind(resultSelect, {
    placeholder: "1",
  })
}
// Result Select (Shop)
let resultSort = document.getElementById("result-sort")
if (resultSort) {
  NiceSelect.bind(resultSort, {
    placeholder: "Sort by Latest",
  })
}

/**
 * Select Choosen Color (Product Details)
 */
const allColor = document.querySelectorAll(".color")
const selectedColorElement = document.getElementById("selectedColor")
// Add click event listener to each color element
allColor.forEach(function (element) {
  element.addEventListener("click", function () {
    toggleActive(this, "active")
    displaySelectedColor(this.textContent)
  })
})

function toggleActive(element, className) {
  allColor.forEach(function (el) {
    el.classList.remove(className)
  })
  element.classList.add(className)
}

function displaySelectedColor(colorName) {
  selectedColorElement.textContent = "Color: " + colorName
}

/*====================================
    Product Quantity (cart)
======================================*/

const productQuantity = (selector) => {
  const quantity = document.querySelectorAll(selector)

  quantity.forEach((element) => {
    const quantityIncrease = element.querySelector(".qty-plus")
    const quantityDecrease = element.querySelector(".qty-minus")
    const quantityInput = element.querySelector(".qty-count")

    let count = 1

    quantityIncrease.addEventListener("click", () => {
      count++
      count = count < 10 ? "0" + count : count
      quantityInput.value = count
    })
    quantityDecrease.addEventListener("click", () => {
      if (count > 1) {
        count--
        count = count < 10 ? "0" + count : count
        quantityInput.value = count
      }
    })
  })
}

productQuantity(".cart-number, .cart-quanty")
/* =================================  
Remove Cart Item
==================================== */

let removeBtns = document.querySelectorAll(".remove")
removeBtns.forEach(function (removeBtn) {
  removeBtn.addEventListener("click", function (e) {
    e.preventDefault()
    this.closest(".cart_item").remove()
  })
})

const checkoutShipping = (selector) => {
  const checkoutVisible = document.querySelector(selector)
  const shipping = document.querySelectorAll("#billform-dirrentswitch")

  if (checkoutVisible) {
    shipping.forEach((element) => {
      element.addEventListener("click", (e) => {
        toggleSlide(checkoutVisible)
      })
    })
  }
}

checkoutShipping("#checkoutCouponform1")

/**===================================
 *  Venobox Lightbox
 */
let imagePopup = new VenoBox({
  selector: ".venobox",
  autoplay: true,
  maxWidth: "1000px",
})

/* ====================================
 Venobox Popup
*/
let videoPoup = new VenoBox({
  selector: ".my-video-links,.video-popup",
  autoplay: true,
  maxWidth: "1000px",
})

/**
 * Nav Toggler Mobile
 */

// Select navbar and offcanvas elements
const navbar = document.querySelector(".navbar")
const navOffCanvasBtn = document.querySelectorAll(".offcanvas-nav-btn")
const navOffCanvas = document.querySelector(".navbar:not(.navbar-clone) .offcanvas-nav")
let bsOffCanvas

// Function to toggle the offcanvas
function toggleOffCanvas() {
  if (bsOffCanvas) {
    bsOffCanvas._isShown ? bsOffCanvas.hide() : bsOffCanvas.show()
  }
}

// Initialize offcanvas if it exists
if (navOffCanvas) {
  bsOffCanvas = new bootstrap.Offcanvas(navOffCanvas, { scroll: true })
  navOffCanvasBtn.forEach((button) => {
    button.addEventListener("click", toggleOffCanvas)
  })
}

// Function to handle dropdown toggle
function handleDropdownToggle(event) {
  const dropdownToggle = event.currentTarget
  const submenu = dropdownToggle.nextElementSibling

  // Close all open submenus
  if (!submenu.classList.contains("show")) {
    dropdownToggle
      .closest(".dropdown-menu")
      .querySelectorAll(".show")
      .forEach((el) => el.classList.remove("show"))
  }

  // Toggle the current submenu
  submenu.classList.toggle("show")

  // Handle closing of submenus on dropdown hide event
  const parentDropdown = dropdownToggle.closest("li.nav-item.dropdown.show")
  if (parentDropdown) {
    parentDropdown.addEventListener("hidden.bs.dropdown", () => {
      document.querySelectorAll(".dropdown-submenu .show").forEach((el) => el.classList.remove("show"))
    })
  }

  // Prevent the default action and stop event propagation
  event.preventDefault()
  event.stopPropagation()
}

// Attach event listeners to dropdown toggles
document.querySelectorAll(".dropdown-menu a.dropdown-toggle").forEach((toggle) => {
  toggle.addEventListener("click", handleDropdownToggle)
})

/**
 *  Sticky Menu
 */
let header = document.querySelector("header nav.navbar")
let win = window

win.addEventListener("scroll", function () {
  let scroll = win.scrollY || win.pageYOffset
  if (scroll < 1) {
    header.classList.remove("scroll-on")
  } else {
    header.classList.add("scroll-on")
  }
})

/**
 * Review Slider
 */

let reviewSlider = new Swiper(".review-slider", {
  direction: "vertical",
  freeMode: true,
  loop: true,
  spaceBetween: 240,
  slidesPerView: 2,
  navigation: {
    nextEl: ".swiper-button-next",
    prevEl: ".swiper-button-prev",
  },
})
/**
 * Services Slider
 */
const serviceSlider = new Swiper(".services-slide", {
  spaceBetween: 30,
  loop: false,
  breakpoints: {
    320: {
      slidesPerView: 1,
    },
    768: {
      slidesPerView: 2,
    },
    992: {
      slidesPerView: 3,
    },
  },
})

/**
 * Price Filter
 */
var slider = document.getElementById("priceRange")
if (slider) {
  const priceRange = noUiSlider.create(slider, {
    connect: true,
    start: [10, 150],
    range: {
      min: 10,
      max: 250,
    },
  })

  var priceValue = document.getElementById("priceRange-value")
  slider.noUiSlider.on("update", function (e) {
    priceValue.innerHTML = e.join(" - ")
  })
}
/**
 * Product Thumb Gallery
 */
var productThumb = new Swiper(".product-thumb", {
  spaceBetween: 10,
  slidesPerView: 4,
  freeMode: true,
  watchSlidesProgress: true,
  navigation: {
    nextEl: ".swiper-button-next",
    prevEl: ".swiper-button-prev",
  },
  breakpoints: {
    // when window width is >= 640px
    320: {
      direction: "horizontal",
      slidesPerView: 3,
    },
    576: {
      direction: "vertical",
      slidesPerView: 4,
    },
  },
})
/**
 * Product Cover Gallery
 */
var swiper2 = new Swiper(".coverItem", {
  spaceBetween: 10,
  thumbs: {
    swiper: productThumb,
  },
})

/**
 * Portfolio Isotope
 */
var portfolio = document.querySelector(".gallery-masionary")
if (portfolio) {
  var iso = new Isotope(".grid", {
    itemSelector: ".grid-item",
    percentPosition: true,
    masonry: {
      // use outer width of grid-sizer for columnWidth
      columnWidth: ".grid-sizer",
    },
  })
}

/**
 * Contact Form Js
 */
// Get the form.
var form = document.getElementById("contact-form")

// Get the messages div.
var formMessages = document.querySelector(".ajax-response")
var formClass = document.querySelectorAll(".open-popup, .offcanvas-overlay")

// Ensure the form exists before adding an event listener.
if (form) {
  // Set up an event listener for the contact form.
  form.addEventListener("submit", function (e) {
    // Stop the browser from submitting the form.
    e.preventDefault()

    // Serialize the form data.
    var formData = new FormData(form)

    // Submit the form using AJAX.
    fetch(form.action, {
      method: "POST",
      body: formData,
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Network response was not ok")
        }
        return response.text()
      })
      .then(function (responseText) {
        // Make sure the formMessages exists.
        if (formMessages) {
          formMessages.classList.remove("error")
          formMessages.classList.add("success")
          formMessages.textContent = responseText
        }

        // Add the 'success' class to formClass elements.
        formClass.forEach(function (element) {
          if (element) {
            element.classList.add("success")
          }
        })

        // Clear the form.
        form.reset()
      })
      .catch(function (error) {
        // Make sure the formMessages exists.
        if (formMessages) {
          formMessages.classList.remove("success")
          formMessages.classList.add("error")
          formMessages.textContent = error.message || "Oops! An error occurred and your message could not be sent."
        }
      })
  })
}

// Add click event to elements to remove 'success' class.
formClass.forEach(function (button) {
  if (button) {
    button.addEventListener("click", function () {
      formClass.forEach(function (element) {
        if (element) {
          element.classList.remove("success")
        }
      })
    })
  }
})
//# sourceMappingURL=custom.js.map
