document.addEventListener("DOMContentLoaded", function() {
    
    // 1. Mobile Menu Toggle
    var menuIcon = document.getElementById("menu-icon");
    var navLinks = document.getElementById("nav-links");

    if (menuIcon && navLinks) {
        menuIcon.addEventListener("click", function() {
            navLinks.classList.toggle("show-menu");
            
            // Toggle between Hamburger (☰) and Close (✕) icons
            if (navLinks.classList.contains("show-menu")) {
                menuIcon.innerHTML = "&#10005;"; 
            } else {
                menuIcon.innerHTML = "&#9776;"; 
            }
        });
    }

    // 2. Email Obfuscation (Safe from bots)
    var emailElement = document.getElementById("secure-email");
    if (emailElement) {
        var user = "petra";
        var domain = "math.uni-heidelberg.de";
        emailElement.href = "mailto:" + user + "@" + domain;
    }
});
