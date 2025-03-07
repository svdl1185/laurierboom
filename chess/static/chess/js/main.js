// static/chess/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // Enable Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Confirmation dialogs
    const confirmBtns = document.querySelectorAll('[data-confirm]');
    confirmBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });
    
    // Tournament registration form validation
    const tournamentRegForm = document.getElementById('tournament-registration-form');
    if (tournamentRegForm) {
        tournamentRegForm.addEventListener('submit', function(e) {
            const confirmCheck = document.getElementById('id_confirm');
            if (!confirmCheck.checked) {
                e.preventDefault();
                alert('Please confirm your participation by checking the box.');
            }
        });
    }
    
    // Match result form enhancements
    const matchResultForm = document.getElementById('match-result-form');
    if (matchResultForm) {
        const resultSelect = document.getElementById('id_result');
        const previewWhite = document.getElementById('result-preview-white');
        const previewBlack = document.getElementById('result-preview-black');
        
        resultSelect.addEventListener('change', function() {
            const result = this.value;
            
            // Reset classes
            previewWhite.className = 'badge';
            previewBlack.className = 'badge';
            
            if (result === 'white_win') {
                previewWhite.className = 'badge bg-success';
                previewWhite.textContent = 'Win';
                previewBlack.className = 'badge bg-danger';
                previewBlack.textContent = 'Loss';
            } else if (result === 'black_win') {
                previewWhite.className = 'badge bg-danger';
                previewWhite.textContent = 'Loss';
                previewBlack.className = 'badge bg-success';
                previewBlack.textContent = 'Win';
            } else if (result === 'draw') {
                previewWhite.className = 'badge bg-warning';
                previewWhite.textContent = 'Draw';
                previewBlack.className = 'badge bg-warning';
                previewBlack.textContent = 'Draw';
            } else {
                previewWhite.className = 'badge bg-secondary';
                previewWhite.textContent = 'Pending';
                previewBlack.className = 'badge bg-secondary';
                previewBlack.textContent = 'Pending';
            }
        });
        
        // Trigger change event to initialize
        if (resultSelect) {
            resultSelect.dispatchEvent(new Event('change'));
        }
    }
});

/* Add this to your static/chess/js/main.js file */
document.addEventListener('DOMContentLoaded', function() {
// Initialize any select2 dropdowns for better UX
if (typeof $.fn.select2 !== 'undefined') {
    $('#player-select').select2({
    dropdownParent: $('#player-select').closest('.dropdown-menu'),
    width: '100%',
    placeholder: 'Select a player',
    allowClear: true
    });
}

// Handle clicking inside dropdown without closing it
$('.dropdown-menu.p-3').on('click', function(e) {
    e.stopPropagation();
});
});