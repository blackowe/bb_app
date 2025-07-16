// Global variables
let selectedTemplate = null;
let currentEditingAntigram = null;
let allAntigrams = [];

document.addEventListener("DOMContentLoaded", function () {
    loadTemplates();
    loadAntigrams();

    // Create antigram functionality
    document.getElementById("templateSelect").addEventListener("change", onTemplateSelect);
    document.getElementById("create-antigram-btn").addEventListener("click", createAntigram);
    document.getElementById("save-antigram-btn").addEventListener("click", saveAntigram);

    // Search functionality
    document.getElementById("searchBtn").addEventListener("click", searchAntigrams);
    document.getElementById("clearSearchBtn").addEventListener("click", clearSearch);
    document.getElementById("searchAntigrams").addEventListener("keypress", function(e) {
        if (e.key === "Enter") searchAntigrams();
    });

    // Modal functionality
    document.querySelector(".close").addEventListener("click", closeModal);
    document.getElementById("cancelEditBtn").addEventListener("click", closeModal);
    document.getElementById("saveEditBtn").addEventListener("click", saveEditChanges);

    // Close modal when clicking outside
    window.addEventListener("click", function(event) {
        const modal = document.getElementById("editModal");
        if (event.target === modal) {
            closeModal();
        }
    });
});

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
                        placeholder="+" 
                        oninput="validateReactionInput(this)"
                    />
                </td>`;
        });

        bodyHtml += "</tr>";
    });
    body.innerHTML = bodyHtml;

    // Show the save button
    document.getElementById("save-antigram-btn").style.display = "block";
}

// Validation
function validateReactionInput(input) {
    const validValues = ["+", "0"];
    if (!validValues.includes(input.value)) {
        input.value = ""; // Clear invalid input
        alert("Only + or 0 are allowed.");
    }
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

// Save Antigram
function saveAntigram() {
    let templateId = document.getElementById("templateSelect").value;
    let lotNumber = document.getElementById("lotNumber").value;
    let expirationDate = document.getElementById("expirationDate").value;

    if (!templateId || !lotNumber || !expirationDate) {
        alert("Please complete all fields before saving.");
        return;
    }

    if (!selectedTemplate) {
        alert("Please select a template first.");
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
        alert("Please complete all reaction inputs before saving.");
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
            alert("Error saving antigram: " + data.error);
        } else {
            alert("Antigram saved successfully!");
            // Reset form and reload antigrams
            resetForm();
            loadAntigrams();
        }
    })
    .catch(error => {
        console.error("Error creating antigram:", error);
        alert("Failed to save antigram.");
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
        tbody.innerHTML = "<tr><td colspan='5' class='no-data'>No antigrams found</td></tr>";
        return;
    }

    antigrams.forEach(antigram => {
        let row = document.createElement("tr");
        row.innerHTML = `
            <td>${antigram.id}</td>
            <td>${antigram.template_name || antigram.name}</td>
            <td>${antigram.lot_number}</td>
            <td>${antigram.expiration_date}</td>
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
                    />
                </td>`;
        });
        
        bodyHtml += "</tr>";
    });
    body.innerHTML = bodyHtml;
}

function validateEditReactionInput(input) {
    const validValues = ["+", "0"];
    if (!validValues.includes(input.value)) {
        input.value = ""; // Clear invalid input
        alert("Only + or 0 are allowed.");
    }
}

function saveEditChanges() {
    if (!currentEditingAntigram) return;

    let lotNumber = document.getElementById("editLotNumber").value;
    let expirationDate = document.getElementById("editExpirationDate").value;

    if (!lotNumber || !expirationDate) {
        alert("Please complete all fields before saving.");
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
        alert("Please complete all reaction inputs before saving.");
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
            alert("Error updating antigram: " + data.error);
        } else {
            alert("Antigram updated successfully!");
            closeModal();
            loadAntigrams();
        }
    })
    .catch(error => {
        console.error("Error updating antigram:", error);
        alert("Failed to update antigram.");
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
    document.getElementById("editModal").style.display = "none";
    currentEditingAntigram = null;
}

// Utility functions
function resetForm() {
    document.getElementById("templateSelect").value = "";
    document.getElementById("lotNumber").value = "";
    document.getElementById("expirationDate").value = "";
    document.getElementById("reactions-section").style.display = "none";
    selectedTemplate = null;
}