document.addEventListener('DOMContentLoaded', () => {
    // 1. Element References
    const menuIcon = document.getElementById('menu-icon');
    const navLinks = document.getElementById('nav-links');

    const tocToggle = document.getElementById('toc-toggle');
    const tocNav = document.getElementById('toc-nav');

    // 2. Toggle Main Menu
    if (menuIcon && navLinks) {
        menuIcon.addEventListener('click', () => {
            navLinks.classList.toggle('show-menu');
        });
    }

    // 3. Toggle Table of Contents (FAB)
    if (tocToggle && tocNav) {
        tocToggle.addEventListener('click', () => {
            tocNav.classList.toggle('active');
        });

        // Close ToC when a link is clicked
        const tocLinks = tocNav.querySelectorAll('a');
        tocLinks.forEach(link => {
            link.addEventListener('click', () => {
                tocNav.classList.remove('active');
            });
        });
    }

    // 4. Click Outside to Close Logic
    document.addEventListener('click', (event) => {

        // Handle Main Navigation Menu
        if (navLinks && navLinks.classList.contains('show-menu')) {
            // If click is NOT inside the menu AND NOT on the hamburger icon
            if (!navLinks.contains(event.target) && !menuIcon.contains(event.target)) {
                navLinks.classList.remove('show-menu');
            }
        }

        // Handle Table of Contents Navigation
        if (tocNav && tocNav.classList.contains('active')) {
            // If click is NOT inside the popup AND NOT on the FAB toggle
            if (!tocNav.contains(event.target) && !tocToggle.contains(event.target)) {
                tocNav.classList.remove('active');
            }
        }
    });

    // 5. Email Obfuscation (safe from bots)
    const emailElement = document.getElementById("secure-email");
    if (emailElement) {
        const user   = "petra";
        const domain = "math.uni-heidelberg.de";
        emailElement.href   = "mailto:" + user + "@" + domain;
    }

    // 6. Dynamic Header Height Calculation
    const header = document.querySelector('.header');

    function updateHeaderHeight() {
        if (header) {
            // Get the exact height of the header in pixels
            const headerHeight = header.offsetHeight;
            // Write it to a CSS variable named --header-height
            document.documentElement.style.setProperty('--header-height', `${headerHeight}px`);
        }
    }

    // Run on load and whenever the window is resized
    updateHeaderHeight();
    window.addEventListener('resize', updateHeaderHeight);
});
