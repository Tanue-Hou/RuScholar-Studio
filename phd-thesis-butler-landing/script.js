document.addEventListener('DOMContentLoaded', () => {
    // Scroll Reveal Animation
    const reveals = document.querySelectorAll('.reveal');

    const revealOnScroll = () => {
        const windowHeight = window.innerHeight;
        const elementVisible = 100;

        reveals.forEach((reveal) => {
            const elementTop = reveal.getBoundingClientRect().top;
            if (elementTop < windowHeight - elementVisible) {
                reveal.classList.add('active');
            }
        });
    };

    // Initial check
    setTimeout(() => {
        revealOnScroll();
    }, 100);

    window.addEventListener('scroll', revealOnScroll);

    // Parallax effect for Hero Image
    const heroBg = document.querySelector('.hero-bg img');
    window.addEventListener('scroll', () => {
        const scrollPosition = window.pageYOffset;
        if(heroBg && scrollPosition < window.innerHeight) {
            heroBg.style.transform = `translateY(${scrollPosition * 0.4}px)`;
            heroBg.style.opacity = 0.7 - (scrollPosition / window.innerHeight) * 0.5;
        }
    });

    // Smooth Scrolling for Anchors
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if(target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});
