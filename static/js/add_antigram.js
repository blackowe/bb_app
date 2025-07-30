// Global variables
let selectedTemplate = null;
let currentEditingAntigram = null;
let allAntigrams = [];

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

function onTemplateSelect() {
    let templateId = document.getElementById("templateSelect").value;
    if (!templateId) {
        document.getElementById("reactions-section").style.display = "none";
        return;
    }

    fetch(`/api/templates/${templateId}`)
        .then(response => response.json())
        .then(template => {
            selectedTemplate = template;
            generateAntigramTable(template);
            document.getElementById("reactions-section").style.display = "block";
        })
        .catch(error => {
            console.error("Error fetching template details:", error);
            alert("Failed to fetch template details.");
        });
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

    // Create header row with antigen names
    let headerRow = "<tr><th>Cell #</th>";
    template.antigen_order.forEach(antigen => {
        headerRow += `<th>${antigen}</th>`;
    });
    headerRow += "</tr>";
    header.innerHTML = headerRow;

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

        template.antigen_order.forEach(antigen => {
            bodyHtml += `  
                <td>
                    <input 
                        type="text" 
                        class="reaction-input" 
                        data-cell="${cellNumber}" 
                        data-antigen="${antigen}" 
                        maxlength="1" 
                        oninput="validateReactionInput(this)"
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
        instructionDiv.innerHTML = '<span>💡 <strong>Valid inputs:</strong> Enter "0" for negative reactions or "+" for positive reactions only.</span>';
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
    if (val === "0" || val === "+") {
        input.style.borderColor = '#007bff';
        input.style.boxShadow = '0 0 0 0.2rem rgba(0,123,255,.25)';
        input.style.backgroundColor = '#e7f3ff';
    } else if (val === "") {
        input.style.borderColor = '#ccc';
        input.style.boxShadow = '';
        input.style.backgroundColor = '#fff';
    } else {
        input.style.borderColor = '#dc3545';
        input.style.boxShadow = '0 0 0 0.2rem rgba(220,53,69,.25)';
        input.style.backgroundColor = '#fff';
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
function editAntigram(antigramId) {
    fetch(`/api/antigrams/${antigramId}`)
        .then(response => response.json())
        .then(antigram => {
            currentEditingAntigram = antigram;
            populateEditModal(antigram);
            document.getElementById("editModal").style.display = "block";
        })
        .catch(error => {
            console.error("Error fetching antigram:", error);
            alert("Failed to fetch antigram details.");
        });
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

    // Get all unique antigens from the first cell
    let antigens = [];
    if (antigram.cells && antigram.cells.length > 0 && antigram.cells[0].reactions) {
        antigens = Object.keys(antigram.cells[0].reactions);
    }

    // Create header row
    let headerRow = "<tr><th>Cell #</th>";
    antigens.forEach(antigen => {
        headerRow += `<th>${antigen}</th>`;
    });
    headerRow += "</tr>";
    header.innerHTML = headerRow;

    // Populate body with current values
    let bodyHtml = "";
    antigram.cells.forEach(cell => {
        bodyHtml += `<tr><td>${cell.cell_number}</td>`;
        
        // Ensure we iterate through antigens in the same order as the header
        antigens.forEach(antigen => {
            let reaction = cell.reactions[antigen] || '';
            bodyHtml += `
                <td>
                    <input 
                        type="text" 
                        class="edit-reaction-input" 
                        data-cell="${cell.cell_number}" 
                        data-antigen="${antigen}" 
                        maxlength="1" 
                        value="${reaction}"
                        oninput="validateEditReactionInput(this)"
                        autocomplete="off"
                    />
                </td>`;
        });
        
        bodyHtml += "</tr>";
    });
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