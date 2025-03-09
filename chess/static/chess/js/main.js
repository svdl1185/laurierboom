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
    
    // Tournament form - handle showing/hiding the rounds field
    const tournamentTypeSelect = document.getElementById('id_tournament_type');
    const roundsFieldContainer = document.getElementById('rounds-field-container');
    
    // Function to toggle rounds field visibility based on tournament type
    function toggleRoundsField() {
        if (!tournamentTypeSelect || !roundsFieldContainer) return;
        
        const selectedType = tournamentTypeSelect.value;
        
        // Hide rounds field if no type is selected or if type is round robin
        if (selectedType === '' || selectedType === 'round_robin' || selectedType === 'double_round_robin') {
            roundsFieldContainer.style.display = 'none';
            
            // Clear the input value when hidden for round robin types
            if (selectedType === 'round_robin' || selectedType === 'double_round_robin') {
                const roundsInput = document.getElementById('id_num_rounds');
                if (roundsInput) roundsInput.value = '';
            }
        } else {
            // Show for Swiss tournaments
            roundsFieldContainer.style.display = 'block';
            
            // Set default value if empty
            const roundsInput = document.getElementById('id_num_rounds');
            if (roundsInput && roundsInput.value === '') {
                roundsInput.value = '10';
            }
        }
    }
    
    // Run on initial load
    if (tournamentTypeSelect) {
        // Set a short timeout to ensure the DOM is fully ready
        setTimeout(toggleRoundsField, 0);
        
        // Add event listener for changes
        tournamentTypeSelect.addEventListener('change', toggleRoundsField);
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // Make tournament table rows clickable
    const clickableRows = document.querySelectorAll('.tournaments-table tbody tr.clickable-row');
    
    clickableRows.forEach(row => {
      row.addEventListener('click', function(e) {
        // Prevent clicking on buttons or links within the row from triggering the row click
        if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON' || 
            e.target.closest('a') || e.target.closest('button')) {
          return;
        }
        
        // Get the URL from data attribute
        const url = this.dataset.href;
        if (url) {
          window.location.href = url;
        }
      });
      
      // Add hover styling for the cursor
      row.style.cursor = 'pointer';
    });
  });

document.addEventListener('DOMContentLoaded', function() {
// Make tournament items clickable
const tournamentItems = document.querySelectorAll('.simple-tournament-item');

tournamentItems.forEach(item => {
    item.addEventListener('click', function(e) {
    // Don't redirect if user clicked on a link or button inside the item
    if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON' || 
        e.target.closest('a') || e.target.closest('button')) {
        return;
    }
    
    // Get the URL from onclick attribute
    const url = this.getAttribute('onclick').replace("window.location.href='", "").replace("'", "");
    if (url) {
        window.location.href = url;
    }
    });
});
});