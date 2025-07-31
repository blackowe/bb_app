// Global variables
let selectedTemplate = null;
let currentEditingAntigram = null;
let allAntigrams = [];
let antigenSystemData = {}; // Store antigen system information
let antigenSystemDataCache = null; // Cache for antigen system data
let antigenSystemDataCacheTime = null; // Cache timestamp
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds

document.addEventListener("DOMContentLoaded", function () {
    loadTemplates();
    loadAntigrams();

    // Template selection
    const templateSelect = document.getElementById("templateSelect");
    if (templateSelect) templateSelect.addEventListener("change", onTemplateSelect);

    // Save antigram
    const saveAntigramBtn = document.getElementById("save-antigram-btn");
    if (saveAntigramBtn) saveAntigramBtn.addEventListener("click", saveAntigram);
    
    // Add real-time validation for form fields
    setupFormValidation();

    // Search functionality
    const searchBtn = document.getElementById("searchBtn");
    if (searchBtn) searchBtn.addEventListener("click", searchAntigrams);
    const clearSearchBtn = document.getElementById("clearSearchBtn");
    if (clearSearchBtn) clearSearchBtn.addEventListener("click", clearSearch);
    const searchAntigramsInput = document.getElementById("searchAntigrams");
    if (searchAntigramsInput) searchAntigramsInput.addEventListener("keypress", function(e) {
        if (e.key === "Enter") searchAntigrams();
    });

    // Modal functionality
    setupModalCloseListeners();
    const saveEditBtn = document.getElementById("saveEditBtn");
    if (saveEditBtn) saveEditBtn.addEventListener("click", saveEditChanges);

    // Close modal when clicking outside
    window.addEventListener("click", function(event) {
        const modal = document.getElementById("editModal");
        if (event.target === modal) {
            closeModal();
        }
    });
});

// Cached antigen system data loader
async function loadAntigenSystemDataCached() {
    const now = Date.now();
    
    // Check if we have valid cached data
    if (antigenSystemDataCache && antigenSystemDataCacheTime && 
        (now - antigenSystemDataCacheTime) < CACHE_DURATION) {
        console.log("Using cached antigen system data");
        antigenSystemData = antigenSystemDataCache;
        return antigenSystemDataCache;
    }
    
    // Cache is invalid or expired, fetch fresh data
    console.log("Fetching fresh antigen system data");
    try {
        const response = await fetch("/api/antigens/valid");
        const validAntigens = await response.json();
        
        // Create antigen system mapping
        const newAntigenSystemData = {};
        validAntigens.forEach(antigen => {
            newAntigenSystemData[antigen.name] = antigen.system;
        });
        
        // Update cache
        antigenSystemDataCache = newAntigenSystemData;
        antigenSystemDataCacheTime = now;
        antigenSystemData = newAntigenSystemData;
        
        return newAntigenSystemData;
    } catch (error) {
        console.error("Error loading antigen system data:", error);
        throw error;
    }
}

// Form Validation Setup
function setupFormValidation() {
    const templateSelect = document.getElementById("templateSelect");
    const lotNumberInput = document.getElementById("lotNumber");
    const expirationDateInput = document.getElementById("expirationDate");
    
    // Add real-time validation listeners
    if (templateSelect) {
        templateSelect.addEventListener('input', validateField);
        templateSelect.addEventListener('blur', validateField);
    }
    
    if (lotNumberInput) {
        lotNumberInput.addEventListener('input', validateField);
        lotNumberInput.addEventListener('blur', validateField);
    }
    
    if (expirationDateInput) {
        expirationDateInput.addEventListener('input', validateField);
        expirationDateInput.addEventListener('blur', validateField);
    }
}

function validateField(event) {
    const field = event.target;
    
    // Remove existing validation styling
    field.classList.remove('is-valid', 'is-invalid');
    
    // Check if field is valid
    if (field.checkValidity()) {
        field.classList.add('is-valid');
    } else {
        field.classList.add('is-invalid');
    }
}

// Template Management
function loadTemplates() {
    fetch("/api/templates")
        .then(response => response.json())
        .then(data => {
            let dropdown = document.getElementById("templateSelect");
            dropdown.innerHTML = "<option value=''>-- Select a Template --</option>";
            data.forEach(template => {
                let option = document.createElement("option");
                option.value = template.id;
                option.textContent = template.name;
                dropdown.appendChild(option);
            });
        })
        .catch(error => console.error("Error loading templates:", error));
}

async function onTemplateSelect() {
    let templateId = document.getElementById("templateSelect").value;
    if (!templateId) {
        document.getElementById("reactions-section").style.display = "none";
        return;
    }

    try {
        // Load template and antigen system data (cached) in parallel
        const [templateResponse, antigenSystemData] = await Promise.all([
            fetch(`/api/templates/${templateId}`),
            loadAntigenSystemDataCached()
        ]);

        const template = await templateResponse.json();

        selectedTemplate = template;
        generateAntigramTable(template);
        document.getElementById("reactions-section").style.display = "block";
    } catch (error) {
        console.error("Error fetching template details:", error);
        alert("Failed to fetch template details.");
    }
}

// Create Antigram
function createAntigram() {
    let templateId = document.getElementById("templateSelect").value;
    let lotNumber = document.getElementById("lotNumber").value;
    let expirationDate = document.getElementById("expirationDate").value;

    if (!templateId || !lotNumber || !expirationDate) {
        alert("Please complete all fields before creating.");
        return;
    }

    if (!selectedTemplate) {
        alert("Please select a template first.");
        return;
    }

    // Show the reactions section
    document.getElementById("reactions-section").style.display = "block";
    generateAntigramTable(selectedTemplate);
}

// Generate Antigram Table
function generateAntigramTable(template) {
    let table = document.getElementById("antigram-table");
    let header = document.getElementById("antigram-header");
    let body = document.getElementById("antigram-body");

    // Clear previous data
    header.innerHTML = "";
    body.innerHTML = "";

    // Create system header row
    let systemHeaderRow = "<tr><th>Cell #</th>";
    let i = 0;
    let systemBorders = []; // Track where system borders should be
    
    while (i < template.antigen_order.length) {
        const agName = template.antigen_order[i];
        const sys = antigenSystemData[agName] || 'Unknown';
        let span = 1;
        for (let j = i + 1; j < template.antigen_order.length; j++) {
            const nextAg = template.antigen_order[j];
            const nextSys = antigenSystemData[nextAg] || 'Unknown';
            if (nextSys === sys) span++;
            else break;
        }
        
        // Add border classes for system separation
        let borderClasses = "antigen-system-header";
        if (i > 0) borderClasses += " system-border-left";
        if (i + span < template.antigen_order.length) borderClasses += " system-border-right";
        
        systemHeaderRow += `<th colspan="${span}" class="${borderClasses}">${sys}</th>`;
        
        // Track border positions for body cells
        if (i > 0) systemBorders.push(i);
        if (i + span < template.antigen_order.length) systemBorders.push(i + span);
        
        i += span;
    }
    systemHeaderRow += "</tr>";
    header.innerHTML = systemHeaderRow;

    // Create antigen name header row
    let antigenHeaderRow = "<tr><th>Cell #</th>";
    template.antigen_order.forEach((antigen, index) => {
        let borderClasses = "";
        if (systemBorders.includes(index)) borderClasses = "system-border-left";
        antigenHeaderRow += `<th class="${borderClasses}">${antigen}</th>`;
    });
    antigenHeaderRow += "</tr>";
    header.innerHTML += antigenHeaderRow;

    // Populate body with input fields
    let bodyHtml = "";
    
    // Determine cell numbers to use
    let cellNumbers = [];
    if (template.cell_range && template.cell_range.length === 2) {
        // Use cell_range if available
        for (let i = template.cell_range[0]; i <= template.cell_range[1]; i++) {
            cellNumbers.push(i);
        }
    } else {
        // Fallback to sequential numbers starting from 1
        for (let i = 1; i <= template.cell_count; i++) {
            cellNumbers.push(i);
        }
    }
    
    cellNumbers.forEach(cellNumber => {
        bodyHtml += `<tr><td>${cellNumber}</td>`; // Cell number column

        template.antigen_order.forEach((antigen, index) => {
            let borderClasses = "";
            if (systemBorders.includes(index)) borderClasses = "system-border-left";
            
            bodyHtml += `  
                <td class="${borderClasses}">
                    <input 
                        type="text" 
                        class="reaction-input" 
                        data-cell="${cellNumber}" 
                        data-antigen="${antigen}" 
                        maxlength="1" 
                        oninput="validateReactionInput(this)"
                        onkeydown="handleKeyNavigation(event, this)"
                        autocomplete="off"
                    />
                </td>`;
        });

        bodyHtml += "</tr>";
    });
    body.innerHTML = bodyHtml;

    // Add instruction text below the table
    const instructionDiv = document.getElementById('antigen-instruction');
    if (instructionDiv) {
        instructionDiv.innerHTML = '<span>💡 <strong>Valid inputs:</strong> Enter "0" for negative reactions or "+" for positive reactions only. Use arrow keys to navigate between cells. Larger input boxes for easier data entry.</span>';
    }

    // Show the save button
    document.getElementById("save-antigram-btn").style.display = "block";

    // Add input highlight logic
    document.querySelectorAll('.reaction-input').forEach(input => {
        input.addEventListener('input', function() {
            highlightAntigenInput(input);
        });
        input.addEventListener('blur', function() {
            highlightAntigenInput(input);
        });
        highlightAntigenInput(input);
    });
}

function highlightAntigenInput(input) {
    const val = input.value.trim();
    
    // Remove any existing validation classes
    input.classList.remove('valid-input', 'invalid-input', 'empty-input');
    
    if (val === "0" || val === "+") {
        input.classList.add('valid-input');
        input.style.borderColor = '#28a745';
        input.style.backgroundColor = '#d4edda';
        input.style.color = '#155724';
    } else if (val === "") {
        input.classList.add('empty-input');
        input.style.borderColor = '#ddd';
        input.style.backgroundColor = '#fff';
        input.style.color = '#000';
    } else {
        input.classList.add('invalid-input');
        input.style.borderColor = '#dc3545';
        input.style.backgroundColor = '#f8d7da';
        input.style.color = '#721c24';
    }
}

// Keyboard navigation function
function handleKeyNavigation(event, input) {
    const inputs = Array.from(document.querySelectorAll('.reaction-input'));
    const currentIndex = inputs.indexOf(input);
    
    switch(event.key) {
        case 'ArrowRight':
            event.preventDefault();
            if (currentIndex < inputs.length - 1) {
                inputs[currentIndex + 1].focus();
            }
            break;
        case 'ArrowLeft':
            event.preventDefault();
            if (currentIndex > 0) {
                inputs[currentIndex - 1].focus();
            }
            break;
        case 'ArrowDown':
            event.preventDefault();
            const currentCell = parseInt(input.getAttribute('data-cell'));
            const currentAntigen = input.getAttribute('data-antigen');
            const antigenIndex = selectedTemplate.antigen_order.indexOf(currentAntigen);
            
            // Find the input in the next cell with the same antigen
            const nextInput = inputs.find(inp => 
                parseInt(inp.getAttribute('data-cell')) === currentCell + 1 && 
                inp.getAttribute('data-antigen') === currentAntigen
            );
            if (nextInput) {
                nextInput.focus();
            }
            break;
        case 'ArrowUp':
            event.preventDefault();
            const currentCellUp = parseInt(input.getAttribute('data-cell'));
            const currentAntigenUp = input.getAttribute('data-antigen');
            
            // Find the input in the previous cell with the same antigen
            const prevInput = inputs.find(inp => 
                parseInt(inp.getAttribute('data-cell')) === currentCellUp - 1 && 
                inp.getAttribute('data-antigen') === currentAntigenUp
            );
            if (prevInput) {
                prevInput.focus();
            }
            break;
        case 'Tab':
            // Allow default tab behavior but add visual feedback
            input.classList.add('nav-highlight');
            setTimeout(() => {
                input.classList.remove('nav-highlight');
            }, 200);
            break;
    }
}

// Validation
function validateReactionInput(input) {
    const validValues = ["+", "0"];
    if (!validValues.includes(input.value)) {
        // No alert, just highlight as invalid
        input.value = input.value.replace(/[^+0]/g, ''); // Remove invalid chars
    }
    highlightAntigenInput(input);
    checkAllFieldsFilled();
}

function checkAllFieldsFilled() {
    let allFilled = true;

    document.querySelectorAll(".reaction-input").forEach(input => {
        if (!input.value.trim() || (input.value !== "+" && input.value !== "0")) {
            allFilled = false;
        }
    });

    document.getElementById("save-antigram-btn").disabled = !allFilled;
}

// Utility function to show alerts
function showAlert(message, type = 'success', autoDismiss = false) {
    const alertArea = document.getElementById('alert-area');
    if (!alertArea) return;
    const alertId = 'alert-' + Date.now();
    alertArea.innerHTML = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    if (autoDismiss) {
        setTimeout(() => {
            const alertElem = document.getElementById(alertId);
            if (alertElem) alertElem.classList.remove('show');
        }, 7000);
    }
}

// Save Antigram
function saveAntigram() {
    console.log('Save Antigram button clicked');
    
    // Get form elements
    const form = document.querySelector('.form-container');
    const templateSelect = document.getElementById("templateSelect");
    const lotNumberInput = document.getElementById("lotNumber");
    const expirationDateInput = document.getElementById("expirationDate");
    
    // Use HTML5 form validation
    if (!form.checkValidity()) {
        // Trigger browser validation UI
        form.reportValidity();
        return;
    }
    
    let templateId = templateSelect.value;
    let lotNumber = lotNumberInput.value;
    let expirationDate = expirationDateInput.value;

    if (!selectedTemplate) {
        showAlert('Please select a template first.', 'danger', false);
        return;
    }

    let cells = [];
    let allFieldsFilled = true;

    document.querySelectorAll(".reaction-input").forEach(input => {
        let cellNumber = input.getAttribute("data-cell");
        let antigen = input.getAttribute("data-antigen");
        let reaction = input.value.trim();

        if (!reaction) {
            allFieldsFilled = false;
        }

        if (!cells[cellNumber - 1]) {
            cells[cellNumber - 1] = { cellNumber: parseInt(cellNumber), reactions: {} };
        }

        cells[cellNumber - 1].reactions[antigen] = reaction;
    });

    if (!allFieldsFilled) {
        showAlert('Please complete all reaction inputs before saving.', 'danger', false);
        return;
    }

    let payload = {
        templateId: templateId,
        lotNumber: lotNumber,
        expirationDate: expirationDate,
        templateName: selectedTemplate.name,
        antigenOrder: selectedTemplate.antigen_order,
        cells: cells.filter(Boolean)
    };

    fetch("/api/antigrams", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('Error saving antigram: ' + data.error, 'danger', false);
        } else {
            showAlert('Antigram saved successfully!', 'success', true);
            // Reset form and reload antigrams
            resetForm();
            loadAntigrams();
        }
    })
    .catch(error => {
        showAlert('Failed to save antigram.', 'danger', false);
    });
}

// View Antigrams
function loadAntigrams() {
    fetch("/api/antigrams")
        .then(response => response.json())
        .then(data => {
            allAntigrams = data;
            displayAntigrams(data);
        })
        .catch(error => console.error("Error loading antigrams:", error));
}

function displayAntigrams(antigrams) {
    let tbody = document.getElementById("antigrams-body");
    tbody.innerHTML = "";

    if (antigrams.length === 0) {
        tbody.innerHTML = "<tr><td colspan='4' class='no-data'>No antigrams found</td></tr>";
        return;
    }

    // Sort by expiration date (descending), then lot number (descending)
    antigrams.sort((a, b) => {
        const dateA = new Date(a.expiration_date);
        const dateB = new Date(b.expiration_date);
        if (dateA > dateB) return -1;
        if (dateA < dateB) return 1;
        // If same expiration, sort by lot number descending
        if (a.lot_number > b.lot_number) return -1;
        if (a.lot_number < b.lot_number) return 1;
        return 0;
    });

    antigrams.forEach(antigram => {
        // Format expiration date as MM/DD/YYYY
        const expirationDate = new Date(antigram.expiration_date);
        const formattedDate = expirationDate.toLocaleDateString('en-US', {
            month: '2-digit',
            day: '2-digit',
            year: 'numeric'
        });
        let row = document.createElement("tr");
        row.innerHTML = `
            <td>${antigram.lot_number}</td>
            <td>${formattedDate}</td>
            <td>${antigram.template_name || antigram.name}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editAntigram(${antigram.id})">Edit</button>
                <button class="btn btn-sm btn-danger" onclick="deleteAntigram(${antigram.id})">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Search functionality
function searchAntigrams() {
    let searchTerm = document.getElementById("searchAntigrams").value.trim();
    if (!searchTerm) {
        displayAntigrams(allAntigrams);
        return;
    }

    let filtered = allAntigrams.filter(antigram => 
        antigram.lot_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (antigram.template_name && antigram.template_name.toLowerCase().includes(searchTerm.toLowerCase()))
    );
    displayAntigrams(filtered);
}

function clearSearch() {
    document.getElementById("searchAntigrams").value = "";
    displayAntigrams(allAntigrams);
}

// Edit functionality
async function editAntigram(antigramId) {
    try {
        // Load antigram and antigen system data (cached) in parallel
        const [antigramResponse, antigenSystemData] = await Promise.all([
            fetch(`/api/antigrams/${antigramId}`),
            loadAntigenSystemDataCached()
        ]);

        const antigram = await antigramResponse.json();

        currentEditingAntigram = antigram;
        populateEditModal(antigram);
        document.getElementById("editModal").style.display = "block";
    } catch (error) {
        console.error("Error fetching antigram:", error);
        alert("Failed to fetch antigram details.");
    }
}

// Edit Modal Table Highlighting
function populateEditModal(antigram) {
    // Populate form fields
    document.getElementById("editLotNumber").value = antigram.lot_number;
    document.getElementById("editExpirationDate").value = antigram.expiration_date;

    // Generate edit table
    let header = document.getElementById("edit-antigram-header");
    let body = document.getElementById("edit-antigram-body");

    // Clear previous data
    header.innerHTML = "";
    body.innerHTML = "";

    // Use the original template's antigen order if available, otherwise fall back to extracting from cells
    let antigens = [];
    if (antigram.antigen_order && antigram.antigen_order.length > 0) {
        // Use the original template's antigen order
        antigens = antigram.antigen_order;
    } else if (antigram.cells && antigram.cells.length > 0 && antigram.cells[0].reactions) {
        // Fallback: extract from the first cell's reactions
        antigens = Object.keys(antigram.cells[0].reactions);
    }

    // Create system header row
    let systemHeaderRow = "<tr><th>Cell #</th>";
    let i = 0;
    let systemBorders = []; // Track where system borders should be
    
    while (i < antigens.length) {
        const agName = antigens[i];
        const sys = antigenSystemData[agName] || 'Unknown';
        let span = 1;
        for (let j = i + 1; j < antigens.length; j++) {
            const nextAg = antigens[j];
            const nextSys = antigenSystemData[nextAg] || 'Unknown';
            if (nextSys === sys) span++;
            else break;
        }
        
        // Add border classes for system separation
        let borderClasses = "antigen-system-header";
        if (i > 0) borderClasses += " system-border-left";
        if (i + span < antigens.length) borderClasses += " system-border-right";
        
        systemHeaderRow += `<th colspan="${span}" class="${borderClasses}">${sys}</th>`;
        
        // Track border positions for body cells
        if (i > 0) systemBorders.push(i);
        if (i + span < antigens.length) systemBorders.push(i + span);
        
        i += span;
    }
    systemHeaderRow += "</tr>";
    header.innerHTML = systemHeaderRow;

    // Create antigen name header row
    let antigenHeaderRow = "<tr><th>Cell #</th>";
    antigens.forEach((antigen, index) => {
        let borderClasses = "";
        if (systemBorders.includes(index)) borderClasses = "system-border-left";
        antigenHeaderRow += `<th class="${borderClasses}">${antigen}</th>`;
    });
    antigenHeaderRow += "</tr>";
    header.innerHTML += antigenHeaderRow;

    // Populate body with current values
    let bodyHtml = "";
    antigram.cells.forEach(cell => {
        bodyHtml += `<tr><td>${cell.cell_number}</td>`;
        
        // Ensure we iterate through antigens in the same order as the header
        antigens.forEach((antigen, index) => {
            let reaction = cell.reactions[antigen] || '';
            let borderClasses = "";
            if (systemBorders.includes(index)) borderClasses = "system-border-left";
            
            bodyHtml += `
                <td class="${borderClasses}">
                    <input 
                        type="text" 
                        class="edit-reaction-input" 
                        data-cell="${cell.cell_number}" 
                        data-antigen="${antigen}" 
                        maxlength="1" 
                        value="${reaction}"
                        oninput="validateEditReactionInput(this)"
                        onkeydown="handleKeyNavigation(event, this)"
                        autocomplete="off"
                    />
                </td>`;
        });
        
        bodyHtml += "</tr>";
    });
    
    // Debug logging to verify antigen order and system data
    console.log("Edit Modal - Template Name:", antigram.name);
    console.log("Edit Modal - Antigen Order:", antigens);
    console.log("Edit Modal - Original antigen_order from API:", antigram.antigen_order);
    console.log("Edit Modal - Antigen System Data:", antigenSystemData);
    console.log("Edit Modal - Sample antigen system lookup:", antigens.map(ag => `${ag}: ${antigenSystemData[ag]}`));
    body.innerHTML = bodyHtml;

    // Add input highlight logic for edit modal
    document.querySelectorAll('.edit-reaction-input').forEach(input => {
        input.addEventListener('input', function() {
            highlightAntigenInput(input);
        });
        input.addEventListener('blur', function() {
            highlightAntigenInput(input);
        });
        highlightAntigenInput(input);
    });
}

function validateEditReactionInput(input) {
    const validValues = ["+", "0"];
    if (!validValues.includes(input.value)) {
        input.value = ""; // Clear invalid input
        showAlert("Only + or 0 are allowed.", 'danger', false);
    }
    highlightAntigenInput(input);
}

function saveEditChanges() {
    if (!currentEditingAntigram) return;

    let lotNumber = document.getElementById("editLotNumber").value;
    let expirationDate = document.getElementById("editExpirationDate").value;

    if (!lotNumber || !expirationDate) {
        showAlert("Please complete all fields before saving.", 'danger', false);
        return;
    }

    let cells = [];
    let allFieldsFilled = true;

    document.querySelectorAll(".edit-reaction-input").forEach(input => {
        let cellNumber = input.getAttribute("data-cell");
        let antigen = input.getAttribute("data-antigen");
        let reaction = input.value.trim();

        if (!reaction) {
            allFieldsFilled = false;
        }

        if (!cells[cellNumber - 1]) {
            cells[cellNumber - 1] = { cellNumber: parseInt(cellNumber), reactions: {} };
        }

        cells[cellNumber - 1].reactions[antigen] = reaction;
    });

    if (!allFieldsFilled) {
        showAlert("Please complete all reaction inputs before saving.", 'danger', false);
        return;
    }

    let payload = {
        lotNumber: lotNumber,
        expirationDate: expirationDate,
        cells: cells.filter(Boolean)
    };

    fetch(`/api/antigrams/${currentEditingAntigram.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert("Error updating antigram: " + data.error, 'danger', false);
        } else {
            showAlert("Antigram updated successfully!", 'success', true);
            closeModal();
            loadAntigrams();
        }
    })
    .catch(error => {
        showAlert("Failed to update antigram.", 'danger', false);
    });
}

// Delete functionality
function deleteAntigram(antigramId) {
    if (!confirm("Are you sure you want to delete this antigram?")) {
        return;
    }

    fetch(`/api/antigrams/${antigramId}`, {
        method: "DELETE"
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert("Error deleting antigram: " + data.error);
        } else {
            alert("Antigram deleted successfully!");
            loadAntigrams();
        }
    })
    .catch(error => {
        console.error("Error deleting antigram:", error);
        alert("Failed to delete antigram.");
    });
}

// Modal functionality
function closeModal() {
    const modal = document.getElementById("editModal");
    if (modal) modal.style.display = "none";
    currentEditingAntigram = null;
}

// Ensure modal close buttons work
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupModalCloseListeners);
} else {
    setupModalCloseListeners();
}
function setupModalCloseListeners() {
    const closeBtn = document.querySelector("#editModal .close");
    const cancelBtn = document.getElementById("cancelEditBtn");
    if (closeBtn) closeBtn.onclick = closeModal;
    if (cancelBtn) cancelBtn.onclick = closeModal;
}

// Utility functions
function resetForm() {
    document.getElementById("templateSelect").value = "";
    document.getElementById("lotNumber").value = "";
    document.getElementById("expirationDate").value = "";
    document.getElementById("reactions-section").style.display = "none";
    selectedTemplate = null;
}