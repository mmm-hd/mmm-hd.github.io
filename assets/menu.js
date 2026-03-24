document.addEventListener("DOMContentLoaded", function() {
    
    // 1. Mobile Menu Toggle
    const menuIcon = document.getElementById("menu-icon");
    const navLinks = document.getElementById("nav-links");

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
    const emailElement = document.getElementById("secure-email");
    if (emailElement) {
        const user   = "petra";
        const domain = "math.uni-heidelberg.de";
        emailElement.href   = "mailto:" + user + "@" + domain;
    }

    // 3. ToC toggle logic for employee pages
    const tocToggle = document.getElementById('toc-toggle');
    const tocNav = document.getElementById('toc-nav');

    if (tocToggle && tocNav) {
        // Toggle the menu open/closed when the button is tapped
        tocToggle.addEventListener('click', () => {
            tocNav.classList.toggle('active');
        });

        // Automatically close the menu when any link inside it is clicked
        const tocLinks = tocNav.querySelectorAll('a');
        tocLinks.forEach(link => {
            link.addEventListener('click', () => {
                tocNav.classList.remove('active');
            });
        });
    }
});
