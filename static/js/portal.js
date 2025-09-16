/**
 * Portal JavaScript functionality
 * 
 * This file contains JavaScript for the portal pages including
 * home, academics, contact, and director dashboard functionality.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize portal functionality
    initializePortal();
    
    // Initialize animations
    initializeAnimations();
    
    // Initialize interactive elements
    initializeInteractiveElements();
});

/**
 * Initialize portal functionality
 */
function initializePortal() {
    console.log('Portal initialized');
    
    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize status indicators
    initializeStatusIndicators();
}

/**
 * Initialize animations and transitions
 */
function initializeAnimations() {
    // Fade in elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.action-card, .program-card, .contact-card, .mentor-card').forEach(el => {
        observer.observe(el);
    });
    
    // Initialize counter animations
    initializeCounterAnimations();
}

/**
 * Initialize interactive elements
 */
function initializeInteractiveElements() {
    // Initialize FAQ accordion
    initializeFAQAccordion();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize filter functionality
    initializeFilters();
    
    // Initialize mentor assignment form
    initializeMentorAssignmentForm();
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            showTooltip(this);
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

/**
 * Show tooltip
 */
function showTooltip(element) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = element.getAttribute('data-tooltip');
    tooltip.style.cssText = `
        position: absolute;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 14px;
        z-index: 1000;
        pointer-events: none;
        white-space: nowrap;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
}

/**
 * Hide tooltip
 */
function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

/**
 * Initialize status indicators
 */
function initializeStatusIndicators() {
    const statusElements = document.querySelectorAll('.status, .status-badge');
    
    statusElements.forEach(element => {
        if (element.classList.contains('verified')) {
            element.style.animation = 'pulse 2s infinite';
        } else if (element.classList.contains('pending')) {
            element.style.animation = 'blink 1.5s infinite';
        }
    });
}

/**
 * Initialize counter animations
 */
function initializeCounterAnimations() {
    const counters = document.querySelectorAll('.stat-number');
    
    counters.forEach(counter => {
        const target = parseInt(counter.textContent);
        const duration = 2000; // 2 seconds
        const increment = target / (duration / 16); // 60fps
        let current = 0;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            counter.textContent = Math.floor(current);
        }, 16);
    });
}

/**
 * Initialize FAQ accordion
 */
function initializeFAQAccordion() {
    const faqItems = document.querySelectorAll('.faq-item h4');
    
    faqItems.forEach(item => {
        item.addEventListener('click', function() {
            const faqItem = this.parentElement;
            const content = faqItem.querySelector('p');
            
            // Toggle active class
            faqItem.classList.toggle('active');
            
            // Toggle content visibility
            if (faqItem.classList.contains('active')) {
                content.style.maxHeight = content.scrollHeight + 'px';
                this.style.transform = 'rotate(180deg)';
            } else {
                content.style.maxHeight = '0';
                this.style.transform = 'rotate(0deg)';
            }
        });
    });
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    const searchInput = document.querySelector('.search-input');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        const query = this.value.toLowerCase();
        const searchableElements = document.querySelectorAll('[data-searchable]');
        
        searchableElements.forEach(element => {
            const text = element.textContent.toLowerCase();
            if (text.includes(query)) {
                element.style.display = '';
                element.classList.add('search-highlight');
            } else {
                element.style.display = 'none';
                element.classList.remove('search-highlight');
            }
        });
    });
}

/**
 * Initialize filter functionality
 */
function initializeFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const filterableElements = document.querySelectorAll('[data-filter]');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.getAttribute('data-filter');
            
            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Filter elements
            filterableElements.forEach(element => {
                if (filter === 'all' || element.getAttribute('data-filter') === filter) {
                    element.style.display = '';
                    element.classList.add('fade-in');
                } else {
                    element.style.display = 'none';
                    element.classList.remove('fade-in');
                }
            });
        });
    });
}

/**
 * Initialize mentor assignment form
 */
function initializeMentorAssignmentForm() {
    const form = document.querySelector('.mentor-form');
    if (!form) return;
    
    const userSelect = form.querySelector('select[name="user_id"]');
    const mentorSelect = form.querySelector('select[name="mentor_id"]');
    
    if (userSelect && mentorSelect) {
        // Update mentor options based on user selection
        userSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            if (selectedOption.text.includes('Already has mentor')) {
                showNotification('This student already has a mentor assigned.', 'warning');
            }
        });
        
        // Form validation
        form.addEventListener('submit', function(e) {
            const userId = userSelect.value;
            const mentorId = mentorSelect.value;
            
            if (!userId || !mentorId) {
                e.preventDefault();
                showNotification('Please select both a student and a mentor.', 'error');
                return false;
            }
            
            if (!confirm('Are you sure you want to assign this mentor to the selected student?')) {
                e.preventDefault();
                return false;
            }
        });
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
        max-width: 300px;
    `;
    
    // Set background color based on type
    switch (type) {
        case 'success':
            notification.style.background = 'linear-gradient(90deg, #10b981, #059669)';
            break;
        case 'error':
            notification.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';
            break;
        case 'warning':
            notification.style.background = 'linear-gradient(90deg, #f59e0b, #d97706)';
            break;
        default:
            notification.style.background = 'linear-gradient(90deg, #3b82f6, #2563eb)';
    }
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

/**
 * Initialize data table functionality
 */
function initializeDataTable() {
    const tables = document.querySelectorAll('.data-table');
    
    tables.forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            row.addEventListener('click', function() {
                // Toggle selection
                this.classList.toggle('selected');
                
                // Update selection count
                const selectedRows = table.querySelectorAll('tbody tr.selected');
                updateSelectionCount(selectedRows.length);
            });
        });
    });
}

/**
 * Update selection count
 */
function updateSelectionCount(count) {
    let counter = document.querySelector('.selection-counter');
    if (!counter) {
        counter = document.createElement('div');
        counter.className = 'selection-counter';
        counter.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--neon);
            color: #001018;
            padding: 10px 15px;
            border-radius: 20px;
            font-weight: bold;
            z-index: 1000;
        `;
        document.body.appendChild(counter);
    }
    
    counter.textContent = `${count} selected`;
    counter.style.display = count > 0 ? 'block' : 'none';
}

/**
 * Initialize responsive navigation
 */
function initializeResponsiveNavigation() {
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.portal-nav');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            this.classList.toggle('active');
        });
    }
}

/**
 * Initialize theme toggle
 */
function initializeThemeToggle() {
    const themeToggle = document.querySelector('.theme-toggle');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            
            // Save theme preference
            const isDark = document.body.classList.contains('dark-theme');
            localStorage.setItem('darkTheme', isDark);
        });
        
        // Load saved theme
        const savedTheme = localStorage.getItem('darkTheme');
        if (savedTheme === 'true') {
            document.body.classList.add('dark-theme');
        }
    }
}

/**
 * Initialize lazy loading for images
 */
function initializeLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

/**
 * Initialize performance monitoring
 */
function initializePerformanceMonitoring() {
    // Monitor page load time
    window.addEventListener('load', function() {
        const loadTime = performance.now();
        console.log(`Page loaded in ${loadTime.toFixed(2)}ms`);
        
        // Send performance data to analytics (if configured)
        if (typeof gtag !== 'undefined') {
            gtag('event', 'page_load_time', {
                'value': Math.round(loadTime)
            });
        }
    });
    
    // Monitor user interactions
    document.addEventListener('click', function(e) {
        const element = e.target;
        const elementType = element.tagName.toLowerCase();
        const elementClass = element.className;
        
        // Track button clicks
        if (elementType === 'button' || elementClass.includes('btn')) {
            console.log(`Button clicked: ${element.textContent.trim()}`);
        }
    });
}

// Initialize all functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializePortal();
    initializeAnimations();
    initializeInteractiveElements();
    initializeDataTable();
    initializeResponsiveNavigation();
    initializeThemeToggle();
    initializeLazyLoading();
    initializePerformanceMonitoring();
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.3; }
    }
    
    .fade-in-up {
        animation: fadeInUp 0.6s ease-out;
    }
    
    .search-highlight {
        background: rgba(103, 232, 249, 0.2);
        border-radius: 4px;
        padding: 2px 4px;
    }
    
    .faq-item.active p {
        max-height: 0;
        overflow: hidden;
        transition: max-height 0.3s ease;
    }
    
    .faq-item.active p {
        max-height: 200px;
    }
    
    .faq-item h4 {
        transition: transform 0.3s ease;
        cursor: pointer;
    }
    
    .filter-btn.active {
        background: var(--neon);
        color: #001018;
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .lazy {
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .lazy.loaded {
        opacity: 1;
    }
`;
document.head.appendChild(style);