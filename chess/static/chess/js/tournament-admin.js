/**
 * Enhanced Tournament Admin Control Panel
 * This script improves the admin control panel during active tournament rounds
 * with better styling, match ordering, and result management.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Store all changes before submitting
    const pendingChanges = new Map();
    
    // Add board numbers to match rows and ensure consistent ordering
    function addBoardNumbersAndEnsureOrder() {
        // Find all round tables in the accordion
        const roundSections = document.querySelectorAll('.accordion-item');
        
        roundSections.forEach(section => {
            const roundNumber = section.querySelector('.accordion-button').textContent.trim().match(/Round (\d+)/)[1];
            const table = section.querySelector('table');
            
            if (!table) return;
            
            // Get all match rows excluding empty placeholder rows
            const rows = Array.from(table.querySelectorAll('tbody tr:not(.empty-row)'));
            
            // Check if we need to add the board column header
            const headerRow = table.querySelector('thead tr');
            if (headerRow && !headerRow.querySelector('.board-header')) {
                const boardHeader = document.createElement('th');
                boardHeader.className = 'board-header text-center';
                boardHeader.style.width = '50px';
                boardHeader.textContent = '#';
                headerRow.insertBefore(boardHeader, headerRow.firstChild);
            }
            
            // Sort rows based on white player name to ensure consistent ordering
            // This maintains the same order as in the tournament container
            const currentRoundNumber = document.querySelector('.tournament-panel-title').textContent.match(/Round (\d+)/)?.[1];
            
            // For the current round, get the order from the main pairings display
            if (roundNumber === currentRoundNumber) {
                const mainPairingsTable = document.querySelector('.tournament-table');
                if (mainPairingsTable) {
                    const mainPairingsRows = Array.from(mainPairingsTable.querySelectorAll('tbody tr'));
                    
                    // Create a mapping of white player name to board number
                    const boardOrder = {};
                    mainPairingsRows.forEach((row, index) => {
                        const whitePlayerName = row.cells[1].textContent.trim().split('\n')[0].trim();
                        boardOrder[whitePlayerName] = index + 1;
                    });
                    
                    // Sort accordion rows based on this mapping
                    rows.sort((a, b) => {
                        const aWhitePlayer = a.cells[1].textContent.trim();
                        const bWhitePlayer = b.cells[1].textContent.trim();
                        
                        return (boardOrder[aWhitePlayer] || 999) - (boardOrder[bWhitePlayer] || 999);
                    });
                }
            }
            
            // Remove all rows from table
            const tbody = table.querySelector('tbody');
            rows.forEach(row => tbody.removeChild(row));
            
            // Add rows back in sorted order with board numbers
            rows.forEach((row, index) => {
                // Check if we already added a board number cell
                if (!row.querySelector('.board-number')) {
                    // Create the board number cell
                    const boardNumberCell = document.createElement('td');
                    boardNumberCell.className = 'board-number text-center';
                    boardNumberCell.style.width = '50px';
                    boardNumberCell.style.fontWeight = 'bold';
                    boardNumberCell.textContent = (index + 1);
                    
                    // Insert as first cell
                    row.insertBefore(boardNumberCell, row.firstChild);
                } else {
                    // Update existing board number
                    row.querySelector('.board-number').textContent = (index + 1);
                }
                
                // Add row back to table
                tbody.appendChild(row);
            });
        });
    }
    
    // Create a unified save button in the admin controls panel
    function createUnifiedSaveButton() {
        // Remove any existing save buttons
        document.querySelectorAll('.batch-update-container, #unified-save-button').forEach(el => {
            el.remove();
        });
        
        // Find the admin controls panel
        const adminPanel = document.querySelector('.admin-controls .card-body');
        if (!adminPanel) return;
        
        // Create the unified save button
        const saveButton = document.createElement('button');
        saveButton.id = 'unified-save-button';
        saveButton.type = 'button';
        saveButton.className = 'btn btn-primary me-3';
        saveButton.innerHTML = '<i class="fas fa-save me-2"></i>Save All Changes';
        saveButton.disabled = true;
        
        // Create status counter
        const statusCounter = document.createElement('span');
        statusCounter.className = 'ms-2 badge bg-secondary changes-counter';
        statusCounter.textContent = '0 changes';
        saveButton.appendChild(statusCounter);
        
        // Add event listener for saving changes
        saveButton.addEventListener('click', submitAllChanges);
        
        // Insert at the beginning of the admin controls
        adminPanel.insertBefore(saveButton, adminPanel.firstChild);
        
        // Add a divider between save button and other controls
        const divider = document.createElement('div');
        divider.className = 'admin-divider';
        adminPanel.insertBefore(divider, saveButton.nextSibling);
    }
    
    // Update the highlight function to work with a unified button
    function highlightPendingChanges() {
        // Reset all highlights first
        document.querySelectorAll('tr.pending-change').forEach(row => {
            row.classList.remove('pending-change');
        });
        
        // Count total changes
        const totalChanges = pendingChanges.size;
        
        // Highlight rows with pending changes
        pendingChanges.forEach((newValue, selectId) => {
            const select = document.getElementById(selectId);
            if (select) {
                const row = select.closest('tr');
                if (row) {
                    row.classList.add('pending-change');
                }
            }
        });
        
        // Update the unified save button
        const saveButton = document.getElementById('unified-save-button');
        if (saveButton) {
            saveButton.disabled = totalChanges === 0;
            
            const counter = saveButton.querySelector('.changes-counter');
            if (counter) {
                counter.textContent = `${totalChanges} change${totalChanges !== 1 ? 's' : ''}`;
                
                // Update counter style based on number of changes
                counter.className = 'ms-2 badge changes-counter';
                counter.classList.add(totalChanges > 0 ? 'bg-warning text-dark' : 'bg-secondary');
                
                // Update the button color based on changes
                if (totalChanges > 0) {
                    saveButton.classList.remove('btn-primary');
                    saveButton.classList.add('btn-success');
                    
                    // Add pulse animation for emphasis
                    saveButton.classList.add('pulse-animation');
                } else {
                    saveButton.classList.remove('btn-success', 'pulse-animation');
                    saveButton.classList.add('btn-primary');
                }
            }
        }
    }
    
    // Unified submit function for all changes
    async function submitAllChanges() {
        const totalChanges = pendingChanges.size;
        if (totalChanges === 0) return;
        
        // Get unified save button
        const saveButton = document.getElementById('unified-save-button');
        if (!saveButton) return;
        
        // Show loading state
        saveButton.disabled = true;
        saveButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
        
        // Process all pending changes
        const promises = [];
        
        pendingChanges.forEach((newValue, selectId) => {
            const select = document.getElementById(selectId);
            if (!select) return;
            
            // Get the form and create the request
            const form = select.closest('form');
            if (!form) return;
            
            const matchId = select.getAttribute('data-match-id');
            
            // Create a request promise
            const requestPromise = fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    return { success: true, matchId };
                } else {
                    return { success: false, matchId, error: data.error };
                }
            })
            .catch(error => {
                return { success: false, matchId, error: error.toString() };
            });
            
            promises.push(requestPromise);
        });
        
        // Wait for all requests to complete
        const results = await Promise.all(promises);
        
        // Check results and handle errors
        const failures = results.filter(result => !result.success);
        
        if (failures.length > 0) {
            // Show error message for failures
            const errorToast = createToast('Error', `Failed to update ${failures.length} matches. Please try again.`, 'danger');
            document.body.appendChild(errorToast);
            
            // Log detailed errors to console
            console.error('Failed updates:', failures);
            
            saveButton.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Some Updates Failed';
            
            // Only remove successful changes from pending changes
            const failedMatchIds = failures.map(f => f.matchId);
            
            pendingChanges.forEach((value, selectId) => {
                const select = document.getElementById(selectId);
                if (!select) return;
                
                const matchId = select.getAttribute('data-match-id');
                if (!failedMatchIds.includes(matchId)) {
                    pendingChanges.delete(selectId);
                }
            });
        } else {
            // All successful - clear all pending changes
            pendingChanges.clear();
            
            // Show success message
            saveButton.innerHTML = '<i class="fas fa-check-circle me-2"></i>Saved Successfully!';
            
            // Show success toast
            const successToast = createToast('Success', `${totalChanges} match ${totalChanges === 1 ? 'result' : 'results'} saved successfully!`, 'success');
            document.body.appendChild(successToast);
        }
        
        // Update UI
        highlightPendingChanges();
        
        // Reload the page after successful save (give time to see the success message)
        if (failures.length === 0) {
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            saveButton.disabled = false;
        }
    }
    
    // Create a toast notification
    function createToast(title, message, type = 'success') {
        const toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '1050';
        
        const toast = document.createElement('div');
        toast.className = `toast show border-0`;
        toast.style.backgroundColor = type === 'success' ? '#19e893' : '#dc3545';
        toast.style.color = type === 'success' ? '#000' : '#fff';
        
        toast.innerHTML = `
            <div class="toast-header" style="background-color: ${type === 'success' ? '#19e893' : '#dc3545'}; color: ${type === 'success' ? '#000' : '#fff'};">
                <strong class="me-auto">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
                    ${title}
                </strong>
                <button type="button" class="btn-close btn-close-${type === 'success' ? 'dark' : 'white'}" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toastContainer.style.opacity = '0';
            toastContainer.style.transition = 'opacity 0.5s ease';
            setTimeout(() => {
                if (toastContainer.parentNode) {
                    toastContainer.parentNode.removeChild(toastContainer);
                }
            }, 500);
        }, 5000);
        
        // Enable manual dismiss
        const closeBtn = toast.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                if (toastContainer.parentNode) {
                    toastContainer.parentNode.removeChild(toastContainer);
                }
            });
        }
        
        return toastContainer;
    }
    
    // Set up event listeners for all result select dropdowns
    function setupResultSelects() {
        const resultSelects = document.querySelectorAll('.result-select');
        
        resultSelects.forEach(select => {
            // Generate a unique ID for this select if it doesn't have one
            if (!select.id) {
                select.id = `result-select-${select.getAttribute('data-match-id')}`;
            }
            
            // Store the original value
            select.setAttribute('data-original-value', select.value);
            
            // Remove any existing listeners to prevent duplicates
            const newSelect = select.cloneNode(true);
            if (select.parentNode) {
                select.parentNode.replaceChild(newSelect, select);
            }
            
            // Add Bootstrap styling to the select
            newSelect.classList.add('form-select-sm');
            
            // Add change event listener to the new select
            newSelect.addEventListener('change', function() {
                const originalValue = this.getAttribute('data-original-value');
                const selectId = this.id;
                
                if (this.value !== originalValue) {
                    // Add to pending changes
                    pendingChanges.set(selectId, this.value);
                    
                    // Add visual feedback
                    this.classList.add('border-warning');
                } else {
                    // Remove from pending changes if changed back to original
                    pendingChanges.delete(selectId);
                    this.classList.remove('border-warning');
                }
                
                // Update UI to reflect pending changes
                highlightPendingChanges();
            });
        });
    }
    
    // Improve the admin controls section layout and styling
    function improveAdminControlsLayout() {
        const adminControls = document.querySelector('.admin-controls');
        if (!adminControls) return;
        
        // Update the heading
        const heading = adminControls.querySelector('h3');
        if (heading) {
            heading.innerHTML = '<i class="fas fa-shield-alt me-2"></i> Tournament Administration';
            heading.className = 'admin-heading';
        }
        
        // Enhance the card
        const card = adminControls.querySelector('.card');
        if (card) {
            card.className = 'card border-0 shadow-sm';
            card.style.borderRadius = '15px';
            card.style.overflow = 'hidden';
        }
        
        // Improve card body layout
        const cardBody = adminControls.querySelector('.card-body');
        if (cardBody) {
            cardBody.className = 'card-body d-flex flex-wrap gap-3 align-items-center p-4';
        }
        
        // Enhance buttons
        const buttons = adminControls.querySelectorAll('button');
        buttons.forEach(button => {
            // Skip unified save button which is styled separately
            if (button.id === 'unified-save-button') return;
            
            // Enhance other buttons
            button.classList.add('fw-bold', 'rounded-pill');
            
            // For round completion button
            if (button.textContent.includes('Complete Current Round')) {
                button.className = 'btn btn-warning fw-bold rounded-pill';
                button.innerHTML = '<i class="fas fa-flag-checkered me-2"></i>Complete Current Round';
            }
            
            // For tournament end button
            if (button.textContent.includes('End Tournament')) {
                button.className = 'btn btn-danger fw-bold rounded-pill';
                button.innerHTML = '<i class="fas fa-trophy me-2"></i>End Tournament';
            }
        });
    }
    
    // Add CSS styles for the admin controls
    function addStyles() {
        // Check if styles already exist
        if (document.getElementById('tournament-admin-styles')) return;
        
        const styleElement = document.createElement('style');
        styleElement.id = 'tournament-admin-styles';
        styleElement.innerHTML = `
            /* Admin controls layout */
            .admin-controls {
                margin-top: 2rem;
                margin-bottom: 2rem;
            }
            
            .admin-heading {
                color: #ffffff;
                font-size: 1.75rem;
                margin-bottom: 1rem;
                font-weight: 600;
                font-family: 'Playfair Display', serif;
            }
            
            .admin-divider {
                height: 35px;
                width: 1px;
                background-color: rgba(255, 255, 255, 0.2);
                margin: 0 0.5rem;
            }
            
            /* Matches with pending changes */
            tr.pending-change {
                background-color: rgba(255, 193, 7, 0.15) !important;
                box-shadow: 0 0 0 1px rgba(255, 193, 7, 0.5);
                transition: all 0.3s ease;
            }
            
            tr.pending-change td {
                font-weight: 600;
            }
            
            /* Results dropdown styling */
            .result-select {
                min-width: 180px;
                border-radius: 6px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .result-select:focus {
                box-shadow: 0 0 0 0.25rem rgba(25, 232, 147, 0.25);
                border-color: #19e893;
            }
            
            .result-select.border-warning {
                box-shadow: 0 0 0 0.25rem rgba(255, 193, 7, 0.25);
            }
            
            /* Board number styling */
            .board-number {
                background-color: #f8f9fa;
                border-right: 2px solid #dee2e6;
                font-weight: 600 !important;
            }
            
            .board-header {
                background-color: #f8f9fa;
                border-right: 2px solid #dee2e6;
            }
            
            /* Round accordion styling */
            .accordion-item {
                border: none;
                margin-bottom: 0.5rem;
                border-radius: 8px !important;
                overflow: hidden;
            }
            
            .accordion-button {
                background-color: #f8f9fa;
                border: none;
                border-radius: 8px !important;
                font-weight: 600;
                padding: 1rem 1.5rem;
            }
            
            .accordion-button:not(.collapsed) {
                background-color: #19e893;
                color: #000;
            }
            
            .accordion-button:focus {
                box-shadow: none;
                border-color: rgba(0,0,0,.125);
            }
            
            /* Button animations */
            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(25, 232, 147, 0.7); }
                70% { box-shadow: 0 0 0 10px rgba(25, 232, 147, 0); }
                100% { box-shadow: 0 0 0 0 rgba(25, 232, 147, 0); }
            }
            
            .pulse-animation {
                animation: pulse 1.5s infinite;
            }
            
            /* Unified save button */
            #unified-save-button {
                min-width: 200px;
                font-weight: 600;
                border-radius: 8px;
            }
            
            #unified-save-button.btn-success {
                background-color: #19e893;
                border-color: #19e893;
                color: #000;
            }
            
            #unified-save-button.btn-success:hover {
                background-color: #15cb7f;
                border-color: #15cb7f;
            }
            
            /* Table improvements */
            .table-responsive {
                border-radius: 8px;
                overflow: hidden;
            }
            
            .table {
                margin-bottom: 0;
            }
            
            .table th {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                font-weight: 600;
                color: #000;
            }
            
            .table td {
                vertical-align: middle;
            }
            
            /* Toast notifications */
            .toast-container {
                z-index: 1060;
            }
            
            .toast {
                border-radius: 8px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            
            /* Fix for card in admin controls */
            .admin-controls .card {
                background-color: #19e893;
            }
        `;
        document.head.appendChild(styleElement);
    }
    
    // Enhance the rounds accordion
    function enhanceRoundsAccordion() {
        const accordion = document.getElementById('roundsAccordion');
        if (!accordion) return;
        
        // Add a header to the accordion section
        const accordionContainer = accordion.closest('.col-12');
        if (accordionContainer) {
            const accordionHeading = accordionContainer.querySelector('h3');
            if (accordionHeading) {
                accordionHeading.innerHTML = '<i class="fas fa-chess-board me-2"></i> Tournament Rounds';
                accordionHeading.className = 'admin-heading';
            }
            
            // Enhance the card
            const card = accordionContainer.querySelector('.card');
            if (card) {
                card.className = 'card border-0 shadow-sm';
                card.style.borderRadius = '15px';
                card.style.overflow = 'hidden';
            }
        }
        
        // Enhance each accordion item
        const accordionItems = accordion.querySelectorAll('.accordion-item');
        accordionItems.forEach(item => {
            // Get the round number and status
            const button = item.querySelector('.accordion-button');
            const headingText = button.textContent.trim();
            const roundNumber = headingText.match(/Round (\d+)/)[1];
            const isCompleted = headingText.includes('Completed');
            
            // Enhance the button appearance
            button.innerHTML = `
                <div class="d-flex align-items-center justify-content-between w-100">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-chess me-2"></i>
                        <span>Round ${roundNumber}</span>
                    </div>
                    <span class="badge ${isCompleted ? 'bg-success' : 'bg-warning text-dark'} ms-2">
                        ${isCompleted ? 'Completed' : 'In Progress'}
                    </span>
                </div>
            `;
            
            // Add a custom complete button to the accordion body if round is not completed
            if (!isCompleted) {
                const accordionBody = item.querySelector('.accordion-body');
                if (accordionBody) {
                    // Check if all matches have results
                    const matches = accordionBody.querySelectorAll('.result-select');
                    let allMatchesHaveResults = true;
                    
                    matches.forEach(select => {
                        if (select.value === 'pending') {
                            allMatchesHaveResults = false;
                        }
                    });
                    
                    // Add the complete round button if not already present
                    if (!accordionBody.querySelector('.complete-round-btn') && allMatchesHaveResults) {
                        const completeBtn = document.createElement('button');
                        completeBtn.className = 'btn btn-success complete-round-btn mt-3';
                        completeBtn.innerHTML = '<i class="fas fa-flag-checkered me-2"></i>Complete Round';
                        completeBtn.addEventListener('click', function() {
                            // Find the complete round form in the admin controls
                            const completeRoundForm = document.querySelector(`form[action*="/tournament/${getTournamentId()}/round/${roundNumber}/complete/"]`);
                            if (completeRoundForm) {
                                completeRoundForm.submit();
                            } else {
                                alert('Could not find the complete round form. Please use the main admin controls.');
                            }
                        });
                        
                        accordionBody.appendChild(completeBtn);
                    }
                }
            }
        });
    }
    
    // Helper function to get tournament ID from URL
    function getTournamentId() {
        const path = window.location.pathname;
        const match = path.match(/\/tournament\/(\d+)\//);
        return match ? match[1] : null;
    }
    
    // Add a "quick set results" button to make all pending matches draws
    function addQuickSetResultsButton() {
        const adminPanel = document.querySelector('.admin-controls .card-body');
        if (!adminPanel) return;
        
        // Create the quick set button if there are any pending matches
        const pendingMatches = document.querySelectorAll('.result-select[value="pending"]');
        if (pendingMatches.length > 0) {
            const quickSetButton = document.createElement('button');
            quickSetButton.type = 'button';
            quickSetButton.className = 'btn btn-outline-light rounded-pill fw-bold';
            quickSetButton.innerHTML = '<i class="fas fa-magic me-2"></i>Set All to Draw';
            
            quickSetButton.addEventListener('click', function() {
                // Ask for confirmation
                if (confirm(`Set all ${pendingMatches.length} pending matches to draws?`)) {
                    // Set all pending matches to draw
                    pendingMatches.forEach(select => {
                        select.value = 'draw';
                        select.dispatchEvent(new Event('change'));
                    });
                    
                    // Show notification
                    const toast = createToast('Quick Set', `${pendingMatches.length} matches set to draw. Click "Save All Changes" to confirm.`, 'success');
                    document.body.appendChild(toast);
                }
            });
            
            // Add after the admin divider if it exists
            const adminDivider = adminPanel.querySelector('.admin-divider');
            if (adminDivider) {
                adminPanel.insertBefore(quickSetButton, adminDivider.nextSibling);
            } else {
                adminPanel.appendChild(quickSetButton);
            }
        }
    }
    
    // Initialize all components
    function initializeAdminControls() {
        // Add styles
        addStyles();
        
        // Improve admin controls layout
        improveAdminControlsLayout();
        
        // Enhance rounds accordion
        enhanceRoundsAccordion();
        
        // Add board numbers and ensure consistent ordering
        addBoardNumbersAndEnsureOrder();
        
        // Create the unified save button in admin panel
        createUnifiedSaveButton();
        
        // Add quick set results button
        addQuickSetResultsButton();
        
        // Setup result selects
        setupResultSelects();
        
        // Initial update of UI
        highlightPendingChanges();
    }
    
    // Initialize the admin controls if we're on a tournament page with active rounds
    const isTournamentWithActiveRounds = document.querySelector('.tournament-panel-title') && 
                                        document.querySelector('.tournament-panel-title').textContent.includes('Round') &&
                                        document.querySelector('.admin-controls');
                                        
    if (isTournamentWithActiveRounds) {
        initializeAdminControls();
    }
});