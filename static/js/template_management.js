document.addEventListener("DOMContentLoaded", function () {
    loadTemplates();
    setupFormValidation();
});

function setupFormValidation() {
    // Add event listeners for real-time validation
    document.getElementById('cellCount').addEventListener('input', validateCellRange);
    document.getElementById('cellRangeStart').addEventListener('input', validateCellRange);
    document.getElementById('cellRangeEnd').addEventListener('input', validateCellRange);
    
    // Form submission
    document.getElementById('templateForm').addEventListener('submit', createTemplate);
}

function validateCellRange() {
    const cellCount = parseInt(document.getElementById('cellCount').value) || 0;
    const rangeStart = parseInt(document.getElementById('cellRangeStart').value) || 0;
    const rangeEnd = parseInt(document.getElementById('cellRangeEnd').value) || 0;
    
    const rangeValidation = document.getElementById('rangeValidation');
    const rangeError = document.getElementById('rangeError');
    const rangeValidationText = document.getElementById('rangeValidationText');
    const rangeErrorText = document.getElementById('rangeErrorText');
    
    // Hide both alerts initially
    rangeValidation.style.display = 'none';
    rangeError.style.display = 'none';
    
    // If no range is specified, that's valid
    if (rangeStart === 0 && rangeEnd === 0) {
        return true;
    }
    
    // If only one range value is provided, show error
    if ((rangeStart > 0 && rangeEnd === 0) || (rangeStart === 0 && rangeEnd > 0)) {
        rangeErrorText.textContent = 'Both start and end values must be provided for cell range.';
        rangeError.style.display = 'block';
        return false;
    }
    
    // If range is provided, validate it
    if (rangeStart > 0 && rangeEnd > 0) {
        // Check if start is less than end
        if (rangeStart >= rangeEnd) {
            rangeErrorText.textContent = 'Cell range start must be less than end.';
            rangeError.style.display = 'block';
            return false;
        }
        
        // Calculate expected count from range
        const expectedCount = rangeEnd - rangeStart + 1;
        
        // Check if count matches range
        if (cellCount !== expectedCount) {
            rangeErrorText.textContent = `Cell count (${cellCount}) must match the range (${expectedCount} cells from ${rangeStart} to ${rangeEnd}).`;
            rangeError.style.display = 'block';
            return false;
        }
        
        // Show validation success
        rangeValidationText.textContent = `Valid range: ${expectedCount} cells from ${rangeStart} to ${rangeEnd}`;
        rangeValidation.style.display = 'block';
        return true;
    }
    
    return true;
}

function createTemplate(e) {
    e.preventDefault();
    
    // Validate cell range before submission
    if (!validateCellRange()) {
        return;
    }
    
    const name = document.getElementById('templateName').value.trim();
    const cellCount = parseInt(document.getElementById('cellCount').value);
    const antigenOrderText = document.getElementById('antigenOrder').value.trim();
    const rangeStart = parseInt(document.getElementById('cellRangeStart').value) || 0;
    const rangeEnd = parseInt(document.getElementById('cellRangeEnd').value) || 0;
    
    // Validate required fields
    if (!name || !cellCount || !antigenOrderText) {
        alert('Please fill in all required fields.');
        return;
    }
    
    // Parse antigen order
    const antigenOrder = antigenOrderText.split(',').map(antigen => antigen.trim()).filter(antigen => antigen.length > 0);
    
    if (antigenOrder.length === 0) {
        alert('Please enter at least one antigen.');
        return;
    }
    
    // Prepare cell range
    let cellRange = null;
    if (rangeStart > 0 && rangeEnd > 0) {
        cellRange = [rangeStart, rangeEnd];
    }
    
    // Create payload
    const payload = {
        name: name,
        antigen_order: antigenOrder,
        cell_count: cellCount,
        cell_range: cellRange
    };
    
    // Send request
    fetch('/api/templates', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error creating template: ' + data.error);
        } else {
            alert('Template created successfully!');
            resetTemplateForm();
            loadTemplates(); // Refresh the template list
        }
    })
    .catch(error => {
        console.error('Error creating template:', error);
        alert('Failed to create template.');
    });
}

function loadTemplates() {
    fetch('/api/templates')
        .then(response => response.json())
        .then(templates => {
            const tableBody = document.getElementById('templateTableBody');
            tableBody.innerHTML = '';
            
            if (templates.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" class="text-center">No templates found</td></tr>';
                return;
            }
            
            templates.forEach(template => {
                const row = document.createElement('tr');
                
                // Format cell range display
                let cellRangeDisplay = 'N/A';
                if (template.cell_range && template.cell_range.length === 2) {
                    cellRangeDisplay = `${template.cell_range[0]} - ${template.cell_range[1]}`;
                }
                
                // Format antigens display (show first few + count)
                let antigensDisplay = template.antigen_order.join(', ');
                if (template.antigen_order.length > 5) {
                    antigensDisplay = template.antigen_order.slice(0, 5).join(', ') + ` (+${template.antigen_order.length - 5} more)`;
                }
                
                row.innerHTML = `
                    <td>${template.name}</td>
                    <td>${template.cell_count}</td>
                    <td>${cellRangeDisplay}</td>
                    <td title="${template.antigen_order.join(', ')}">${antigensDisplay}</td>
                    <td>
                        <button class="btn btn-sm btn-danger" onclick="deleteTemplate(${template.id})">Delete</button>
                    </td>
                `;
                
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error loading templates:', error);
            document.getElementById('templateTableBody').innerHTML = '<tr><td colspan="5" class="text-center text-danger">Error loading templates</td></tr>';
        });
}

function deleteTemplate(templateId) {
    if (!confirm('Are you sure you want to delete this template? This action cannot be undone.')) {
        return;
    }
    
    fetch(`/api/templates/${templateId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error deleting template: ' + data.error);
        } else {
            alert('Template deleted successfully!');
            loadTemplates(); // Refresh the template list
        }
    })
    .catch(error => {
        console.error('Error deleting template:', error);
        alert('Failed to delete template.');
    });
}

function resetTemplateForm() {
    document.getElementById('templateForm').reset();
    document.getElementById('rangeValidation').style.display = 'none';
    document.getElementById('rangeError').style.display = 'none';
} 