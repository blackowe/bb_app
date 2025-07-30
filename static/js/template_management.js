document.addEventListener("DOMContentLoaded", function () {
    loadTemplates();
    setupFormValidation();
    loadValidAntigensAndRenderDnd();
});

function setupFormValidation() {
    // Add event listeners for real-time validation
    document.getElementById('cellCount').addEventListener('input', validateCellRange);
    document.getElementById('cellRangeStart').addEventListener('input', validateCellRange);
    document.getElementById('cellRangeEnd').addEventListener('input', validateCellRange);
    
    // Add validation for required fields
    const templateName = document.getElementById('templateName');
    const cellCount = document.getElementById('cellCount');
    const antigenOrder = document.getElementById('antigenOrder');
    
    if (templateName) {
        templateName.addEventListener('input', validateField);
        templateName.addEventListener('blur', validateField);
    }
    
    if (cellCount) {
        cellCount.addEventListener('input', validateField);
        cellCount.addEventListener('blur', validateField);
    }
    
    if (antigenOrder) {
        antigenOrder.addEventListener('input', validateField);
        antigenOrder.addEventListener('blur', validateField);
    }
    
    // Form submission
    document.getElementById('templateForm').addEventListener('submit', createTemplate);
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
    
    // Get form element
    const form = document.getElementById('templateForm');
    
    // Use HTML5 form validation
    if (!form.checkValidity()) {
        // Trigger browser validation UI
        form.reportValidity();
        return;
    }
    
    // Validate cell range before submission
    if (!validateCellRange()) {
        return;
    }
    
    const name = document.getElementById('templateName').value.trim();
    const cellCount = parseInt(document.getElementById('cellCount').value);
    const antigenOrderText = document.getElementById('antigenOrder').value.trim();
    const rangeStart = parseInt(document.getElementById('cellRangeStart').value) || 0;
    const rangeEnd = parseInt(document.getElementById('cellRangeEnd').value) || 0;
    
    // Parse antigen order
    const antigenOrder = antigenOrderText.split(',').map(antigen => antigen.trim()).filter(antigen => antigen.length > 0);
    
    if (antigenOrder.length === 0) {
        // Set custom validation message for antigen order
        const antigenOrderField = document.getElementById('antigenOrder');
        antigenOrderField.setCustomValidity('Please select at least one antigen');
        antigenOrderField.reportValidity();
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
    // Reset antigen order to default (Panocell) order
    if (Array.isArray(panocellOrder) && panocellOrder.length > 0) {
        let used = new Set();
        antigenOrder = [];
        panocellOrder.forEach(ag => {
            const agObj = validAntigens.find(a => a.name === ag);
            if (agObj && !used.has(ag)) {
                antigenOrder.push(ag);
                used.add(ag);
            }
        });
        // Add any remaining valid antigens not in Panocell order, grouped by system
        Object.keys(systemGroups).forEach(sys => {
            systemGroups[sys].forEach(ag => {
                if (!used.has(ag)) {
                    antigenOrder.push(ag);
                    used.add(ag);
                }
            });
        });
        renderAntigenOrderTable();
        setupSortableAntigenOrder();
    }
} 

let validAntigens = [];
let antigenOrder = [];
let systemGroups = {};
let bypassSystemSplit = false;
let panocellOrder = [];

function loadValidAntigensAndRenderDnd() {
    fetch('/api/antigens/valid')
        .then(response => response.json())
        .then(data => {
            validAntigens = data;
            // Group by system
            systemGroups = {};
            data.forEach(ag => {
                if (!systemGroups[ag.system]) systemGroups[ag.system] = [];
                systemGroups[ag.system].push(ag.name);
            });
            // Fetch the default antigen order from the backend
            fetch('/api/antigens/default-order')
                .then(resp => resp.json())
                .then(defaultOrder => {
                    panocellOrder = Array.isArray(defaultOrder) ? defaultOrder : [];
                    // Build default antigen order: group by system, keep Panocell order, only valid antigens
                    antigenOrder = [];
                    let used = new Set();
                    panocellOrder.forEach(ag => {
                        const agObj = data.find(a => a.name === ag);
                        if (agObj && !used.has(ag)) {
                            antigenOrder.push(ag);
                            used.add(ag);
                        }
                    });
                    // Add any remaining valid antigens not in Panocell order, grouped by system
                    Object.keys(systemGroups).forEach(sys => {
                        systemGroups[sys].forEach(ag => {
                            if (!used.has(ag)) {
                                antigenOrder.push(ag);
                                used.add(ag);
                            }
                        });
                    });
                    renderAntigenOrderTable();
                    setupSortableAntigenOrder();
                })
                .catch(() => {
                    // Fallback: just use valid antigens in original order
                    antigenOrder = data.map(a => a.name);
                    renderAntigenOrderTable();
                    setupSortableAntigenOrder();
                });
        });
}

function renderAntigenOrderTable() {
    const systemHeaderRow = document.getElementById('system-header-row');
    const antigenHeaderRow = document.getElementById('antigen-header-row');
    let antigenDeleteRow = document.getElementById('antigen-delete-row');
    if (!antigenDeleteRow) {
        antigenDeleteRow = document.createElement('tr');
        antigenDeleteRow.id = 'antigen-delete-row';
        antigenHeaderRow.parentNode.appendChild(antigenDeleteRow);
    }
    systemHeaderRow.innerHTML = '';
    antigenHeaderRow.innerHTML = '';
    antigenDeleteRow.innerHTML = '';
    // Build system row with correct colspan
    let i = 0;
    while (i < antigenOrder.length) {
        const agName = antigenOrder[i];
        const ag = validAntigens.find(a => a.name === agName);
        if (!ag) { i++; continue; }
        const sys = ag.system;
        let span = 1;
        for (let j = i + 1; j < antigenOrder.length; j++) {
            const nextAg = validAntigens.find(a => a.name === antigenOrder[j]);
            if (nextAg && nextAg.system === sys) span++;
            else break;
        }
        const th = document.createElement('th');
        th.colSpan = span;
        th.className = 'antigen-system-header';
        th.textContent = sys;
        systemHeaderRow.appendChild(th);
        i += span;
    }
    // Build antigen row (draggable columns)
    antigenOrder.forEach((agName, idx) => {
        const th = document.createElement('th');
        th.className = 'antigen-dnd-th';
        th.textContent = agName;
        th.dataset.idx = idx;
        th.dataset.antigen = agName;
        th.style.cursor = 'grab';
        antigenHeaderRow.appendChild(th);
        // Delete button row
        const td = document.createElement('td');
        td.style.textAlign = 'center';
        td.style.padding = '0';
        const btn = document.createElement('button');
        btn.className = 'btn btn-sm btn-outline-danger antigen-delete-btn';
        btn.style.margin = '2px 0 2px 0';
        btn.title = 'Remove antigen';
        btn.innerHTML = '&times;';
        btn.onclick = function() {
            antigenOrder.splice(idx, 1);
            renderAntigenOrderTable();
            setupSortableAntigenOrder();
            
            // Trigger validation after removing antigen
            const antigenOrderField = document.getElementById('antigenOrder');
            if (antigenOrderField) {
                validateField({ target: antigenOrderField });
            }
        };
        td.appendChild(btn);
        antigenDeleteRow.appendChild(td);
    });
    updateAntigenOrderInput();
}

function setupSortableAntigenOrder() {
    const antigenHeaderRow = document.getElementById('antigen-header-row');
    if (!antigenHeaderRow) return;
    if (antigenHeaderRow._sortable) return; // Prevent double init
    antigenHeaderRow._sortable = true;
    Sortable.create(antigenHeaderRow, {
        animation: 150,
        direction: 'horizontal',
        ghostClass: 'antigen-dnd-ghost',
        chosenClass: 'antigen-dnd-chosen',
        dragClass: 'antigen-dnd-drag',
        onStart: function (evt) {
            evt.item.classList.add('antigen-dnd-grabbed');
        },
        onEnd: function (evt) {
            // Update antigenOrder based on new th order
            const newOrder = [];
            antigenHeaderRow.querySelectorAll('th').forEach(th => {
                newOrder.push(th.textContent);
            });
            // Check for system split
            const prevOrder = [...antigenOrder];
            antigenOrder = newOrder;
            if (!bypassSystemSplit && isSystemSplit()) {
                showSystemSplitModal(() => {
                    bypassSystemSplit = true;
                    renderAntigenOrderTable();
                    setupSortableAntigenOrder();
                }, () => {
                    // Undo move
                    antigenOrder = prevOrder;
                    renderAntigenOrderTable();
                    setupSortableAntigenOrder();
                });
                return;
            }
            renderAntigenOrderTable();
            setupSortableAntigenOrder();
        }
    });
}

document.getElementById('confirmSystemSplit').addEventListener('click', function() {
    bypassSystemSplit = true;
    const modal = bootstrap.Modal.getInstance(document.getElementById('systemSplitModal'));
    modal.hide();
    renderAntigenOrderTable();
    setupSortableAntigenOrder();
});

function showSystemSplitModal(onConfirm, onCancel) {
    const modalEl = document.getElementById('systemSplitModal');
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
    // Confirm button
    const confirmBtn = document.getElementById('confirmSystemSplit');
    const cancelBtn = modalEl.querySelector('.btn-secondary');
    function cleanup() {
        confirmBtn.removeEventListener('click', confirmHandler);
        cancelBtn.removeEventListener('click', cancelHandler);
    }
    function confirmHandler() { cleanup(); onConfirm(); }
    function cancelHandler() { cleanup(); onCancel(); }
    confirmBtn.addEventListener('click', confirmHandler);
    cancelBtn.addEventListener('click', cancelHandler);
}

function isSystemSplit() {
    // For each system, check if its antigens are contiguous in antigenOrder
    for (const sys in systemGroups) {
        const ags = systemGroups[sys];
        const idxs = ags.map(ag => antigenOrder.indexOf(ag)).filter(i => i !== -1).sort((a, b) => a - b);
        if (idxs.length > 1) {
            for (let i = 1; i < idxs.length; i++) {
                if (idxs[i] !== idxs[i - 1] + 1) return true;
            }
        }
    }
    return false;
}

function updateAntigenOrderInput() {
    const antigenOrderField = document.getElementById('antigenOrder');
    antigenOrderField.value = antigenOrder.join(',');
    
    // Trigger validation
    if (antigenOrderField) {
        validateField({ target: antigenOrderField });
    }
} 

// Add styles for highlighting and hand cursor
(function() {
    const style = document.createElement('style');
    style.innerHTML = `
    .antigen-dnd-th { cursor: grab; user-select: none; transition: border 0.2s; }
    .antigen-dnd-th.antigen-dnd-grabbed, .antigen-dnd-th.antigen-dnd-chosen {
        border: 2px solid #007bff !important;
        background: #eaf4ff;
    }
    .antigen-delete-btn { font-size: 0.9em; line-height: 1; padding: 0 6px; }
    `;
    document.head.appendChild(style);
})(); 