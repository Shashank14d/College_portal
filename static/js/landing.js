// Simple auto-animate hero content on landing
document.addEventListener('DOMContentLoaded', () => {
	const content = document.querySelector('.landing .hero .content');
	if (!content) return;
	content.animate([
		{ transform: 'translateY(8px)', opacity: 0 },
		{ transform: 'translateY(0)', opacity: 1 }
	], { duration: 900, easing: 'cubic-bezier(.2,.8,.2,1)', fill: 'forwards' });
});



