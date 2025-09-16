/**
 * Director Dashboard JavaScript functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeDirectorDashboard();
    initializeMentorAssignment();
    initializeUserManagement();
});

function initializeDirectorDashboard() {
    console.log('Director dashboard initialized');
    initializeRealTimeUpdates();
}

function initializeMentorAssignment() {
    const mentorForm = document.querySelector('.mentor-form');
    if (!mentorForm) return;
    
    const userSelect = mentorForm.querySelector('select[name="user_id"]');
    const mentorSelect = mentorForm.querySelector('select[name="mentor_id"]');
    
    if (userSelect && mentorSelect) {
        form.addEventListener('submit', function(e) {
            const userId = userSelect.value;
            const mentorId = mentorSelect.value;
            
            if (!userId || !mentorId) {
                e.preventDefault();
                alert('Please select both a student and a mentor.');
                return false;
            }
            
            if (!confirm('Are you sure you want to assign this mentor to the selected student?')) {
                e.preventDefault();
                return false;
            }
        });
    }
}

function initializeUserManagement() {
    const table = document.querySelector('.data-table');
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach((row, index) => {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'user-checkbox';
        checkbox.setAttribute('data-user-id', row.getAttribute('data-user-id'));
        
        const cell = document.createElement('td');
        cell.appendChild(checkbox);
        row.insertBefore(cell, row.firstChild);
    });
}

function initializeRealTimeUpdates() {
    setInterval(updateStats, 30000);
}

function updateStats() {
    // Update dashboard stats
    console.log('Updating stats...');
}

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
        background: var(--neon);
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}