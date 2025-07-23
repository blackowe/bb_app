// Global variable to store antigen pairs
let antigenPairsData = {};
let ruleModal = null;

$(document).ready(function() {
    // Initialize Select2 for dropdowns inside modal
    $('#ruleAntigens').select2({
        dropdownParent: $('#ruleModal'),
        placeholder: 'Select antigens...',
        allowClear: true
    });

    // Load initial data
    loadAntigens();
    loadAntigenPairs();
    loadRules();

    // Add event listeners
    $('#ruleType').on('change', updateRuleFields);

    // Modal logic
    ruleModal = new bootstrap.Modal(document.getElementById('ruleModal'));

    // Open Create Rule Modal
    $('#openCreateRuleModal').on('click', function() {
        openRuleModal('create');
    });

    // Save Rule from modal
    $('#saveRuleBtn').on('click', function() {
        submitRuleForm();
    });
});

// Store pending antigens to select after loading
window.pendingRuleAntigens = null;
window.isEditingRule = false;

function openRuleModal(mode, rule) {
    resetForm();
    if (mode === 'create') {
        window.isEditingRule = false;
        $('#ruleModalLabel').text('Create New Antibody Rule');
        $('#saveRuleBtn').text('Save Rule');
        $('#ruleId').val('');
        window.pendingRuleAntigens = null;
    } else if (mode === 'edit') {
        window.isEditingRule = true;
        $('#ruleModalLabel').text('Edit Antibody Rule');
        $('#saveRuleBtn').text('Save Rule');
        if (rule) {
            $('#ruleId').val(rule.id);
            $('#targetAntigen').val(rule.target_antigen);
            $('#ruleType').val(rule.rule_type);
            const ruleData = rule.rule_data;
            let antigensToSelect = [];
            if (rule.rule_type === 'abspecific') {
                antigensToSelect = [ruleData.antibody, ruleData.antigen1, ruleData.antigen2];
            } else if (rule.rule_type === 'homo') {
                // Find the pair for the current target antigen and select the paired antigen
                const pair = (ruleData.antigen_pairs || []).find(pair => pair[0] === rule.target_antigen);
                antigensToSelect = pair ? [pair[1]] : [];
            } else if (rule.rule_type === 'hetero') {
                // Only show the paired antigen (not the target antigen)
                if (ruleData.antigen_a === rule.target_antigen) {
                    antigensToSelect = [ruleData.antigen_b];
                } else if (ruleData.antigen_b === rule.target_antigen) {
                    antigensToSelect = [ruleData.antigen_a];
                } else {
                    antigensToSelect = [];
                }
            } else if (rule.rule_type === 'single') {
                antigensToSelect = ruleData.antigens;
            } else if (rule.rule_type === 'lowf') {
                antigensToSelect = ruleData.antigens;
            }
            window.pendingRuleAntigens = antigensToSelect;
            // Fix required count population
            if (typeof ruleData.required_count !== 'undefined') {
                $('#requiredCount').val(ruleData.required_count);
            } else {
                $('#requiredCount').val(1);
            }
            $('#description').val(rule.description || '');
            updateRuleFields();
            // Set the value after updateRuleFields (which resets the dropdown)
            if (window.pendingRuleAntigens && window.pendingRuleAntigens.length > 0) {
                $('#ruleAntigens').val(window.pendingRuleAntigens).trigger('change');
            }
        }
    }
    ruleModal.show();
}

// Update rule fields based on rule type
function updateRuleFields() {
    const ruleType = $('#ruleType').val();
    
    // Only reset if not editing or if no value is set
    if (!window.isEditingRule || !$('#ruleAntigens').val() || $('#ruleAntigens').val().length === 0) {
        $('#ruleAntigens').val(null).trigger('change');
    }
    
    // Reset fields
    $('#requiredCount').val(1);
    
    // Show/hide fields based on rule type
    const ruleAntigensGroup = $('#ruleAntigens').closest('.col-md-6');
    const requiredCountGroup = $('#requiredCount').closest('.col-md-6');
    
    // Update based on rule type
    switch(ruleType) {
        case 'abspecific':
            ruleAntigensGroup.show();
            requiredCountGroup.show();
            $('#ruleAntigens').attr('multiple', false);
            $('#requiredCount').prop('disabled', false);
            break;
        case 'homo':
            ruleAntigensGroup.show();
            requiredCountGroup.hide(); // Hide Required Count for Homo
            $('#ruleAntigens').attr('multiple', true);
            $('#requiredCount').prop('disabled', true);
            break;
        case 'hetero':
            ruleAntigensGroup.show();
            requiredCountGroup.show();
            $('#ruleAntigens').attr('multiple', false);
            $('#requiredCount').prop('disabled', false);
            break;
        case 'single':
            ruleAntigensGroup.hide(); // Hide Rule Antigens for Single
            requiredCountGroup.hide(); // Hide Required Count for Single
            $('#ruleAntigens').attr('multiple', true);
            $('#requiredCount').prop('disabled', true);
            break;
        case 'lowf':
            ruleAntigensGroup.show();
            requiredCountGroup.hide(); // Hide Required Count for LowF
            $('#ruleAntigens').attr('multiple', true);
            $('#requiredCount').prop('disabled', true);
            break;
        default:
            ruleAntigensGroup.show();
            requiredCountGroup.show();
            break;
    }
}

// Load antigens and their pairs from the server
function loadAntigens() {
    fetch('/api/antigens')
        .then(response => response.json())
        .then(data => {
            // Update select dropdowns
            const targetAntigenSelect = document.getElementById('targetAntigen');
            const ruleAntigensSelect = document.getElementById('ruleAntigens');
            
            // Clear existing options
            targetAntigenSelect.innerHTML = '<option value="">Select Target Antigen</option>';
            ruleAntigensSelect.innerHTML = '';
            
            data.forEach(antigen => {
                // Add to select dropdowns
                const option = new Option(antigen.name, antigen.name);
                targetAntigenSelect.add(option.cloneNode(true));
                ruleAntigensSelect.add(option);
            });
            
            // Refresh Select2
            $('#ruleAntigens').trigger('change');
            // Always check for pending antigens to select (edit mode)
            if (window.pendingRuleAntigens && window.pendingRuleAntigens.length > 0) {
                $('#ruleAntigens').val(window.pendingRuleAntigens).trigger('change');
            }
        })
        .catch(error => console.error('Error loading antigens:', error));
}

// Load antigen pairs from the server
function loadAntigenPairs() {
    fetch('/api/antigens/pairs')
        .then(response => response.json())
        .then(data => {
            antigenPairsData = data.antigen_pairs || {};
            console.log('Loaded antigen pairs:', antigenPairsData);
        })
        .catch(error => console.error('Error loading antigen pairs:', error));
}

// Get paired antigen (dynamic lookup from database)
function getPairedAntigen(antigen) {
    if (antigenPairsData[antigen] && antigenPairsData[antigen].length > 0) {
        return antigenPairsData[antigen][0]; // Return first available pair
    }
    return '';
}

// Get all paired antigens for a given antigen
function getAllPairedAntigens(antigen) {
    return antigenPairsData[antigen] || [];
}

// Handle rule form submission
document.getElementById('antibodyRuleForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Validate form
    if (!validateRuleForm()) {
        return;
    }
    
    const formData = {
        target_antigen: document.getElementById('targetAntigen').value,
        rule_type: document.getElementById('ruleType').value,
        rule_data: getRuleData(),
        description: document.getElementById('description').value,
        enabled: true
    };
    
    const ruleId = document.getElementById('ruleId').value;
    const url = ruleId ? `/api/antibody-rules/${ruleId}` : '/api/antibody-rules';
    const method = ruleId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        loadRules();
        resetForm();
        alert(ruleId ? 'Rule updated successfully!' : 'Rule created successfully!');
    })
    .catch(error => {
        console.error('Error saving rule:', error);
        alert('Error saving rule. Please try again.');
    });
});

// Get rule data based on rule type
function getRuleData() {
    const ruleType = document.getElementById('ruleType').value;
    const ruleAntigens = $('#ruleAntigens').val();
    const requiredCount = parseInt(document.getElementById('requiredCount').value);
    const targetAntigen = document.getElementById('targetAntigen').value;
    
    switch(ruleType) {
        case 'abspecific':
            return {
                antibody: ruleAntigens[0],
                antigen1: ruleAntigens[1] || '',
                antigen2: ruleAntigens[2] || '',
                required_count: requiredCount
            };
        case 'homo':
            // For Homo rules, use dynamic antigen pairs from the database
            const antigenPairs = [];
            if (ruleAntigens && ruleAntigens.length > 0) {
                // Create pairs using the selected antigens and their known pairs
                ruleAntigens.forEach(antigen => {
                    const pairedAntigens = getAllPairedAntigens(antigen);
                    pairedAntigens.forEach(pairedAntigen => {
                        antigenPairs.push([antigen, pairedAntigen]);
                    });
                });
            }
            
            // If no specific pairs found, create a default pair with the target antigen
            // This ensures the rule can still be created and evaluated
            if (antigenPairs.length === 0) {
                const targetPairedAntigens = getAllPairedAntigens(targetAntigen);
                if (targetPairedAntigens.length > 0) {
                    targetPairedAntigens.forEach(pairedAntigen => {
                        antigenPairs.push([targetAntigen, pairedAntigen]);
                    });
                } else {
                    // Fallback: create a self-pair if no pairs are defined
                    antigenPairs.push([targetAntigen, targetAntigen]);
                }
            }
            
            return {
                antigen_pairs: antigenPairs
            };
        case 'hetero':
            return {
                antigen_a: ruleAntigens[0],
                antigen_b: ruleAntigens[1] || '',
                required_count: requiredCount
            };
        case 'single':
            // For Single Antigen rules, use the target antigen as the rule antigen
            return {
                antigens: [targetAntigen]
            };
        case 'lowf':
            return {
                antigens: ruleAntigens
            };
        default:
            return {};
    }
}

// Validate rule form
function validateRuleForm() {
    const ruleType = document.getElementById('ruleType').value;
    const ruleAntigens = $('#ruleAntigens').val();
    const targetAntigen = document.getElementById('targetAntigen').value;
    
    if (!ruleType) {
        alert('Please select a rule type');
        return false;
    }
    
    if (!targetAntigen) {
        alert('Please select a target antigen');
        return false;
    }
    
    // For Single Antigen rules, don't require rule antigens (target antigen is the rule antigen)
    if (ruleType !== 'single') {
        if (!ruleAntigens || ruleAntigens.length === 0) {
            alert('Please select at least one rule antigen');
            return false;
        }
    }
    
    // Validate rule-specific requirements
    switch(ruleType) {
        case 'abspecific':
            if (ruleAntigens.length < 3) {
                alert('ABSpecificRO rules require 3 antigens (antibody, antigen1, antigen2)');
                return false;
            }
            break;
        case 'hetero':
            if (ruleAntigens.length < 2) {
                alert('Heterozygous rules require 2 antigens');
                return false;
            }
            break;
    }
    
    return true;
}

// Reset form
function resetForm() {
    document.getElementById('antibodyRuleForm').reset();
    document.getElementById('ruleId').value = '';
    $('#ruleAntigens').val(null).trigger('change');
    $('#requiredCount').prop('disabled', false);
    $('#ruleType').val('').trigger('change');
    $('#targetAntigen').val('');
    $('#description').val('');
}

// Load rules from the server
function loadRules() {
    fetch('/api/antibody-rules')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('rulesTableBody');
            tbody.innerHTML = '';
            
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No rules found. Create your first rule above.</td></tr>';
                return;
            }
            
            data.forEach(rule => {
                const row = document.createElement('tr');
                const ruleData = rule.rule_data;
                let ruleInfo = '';
                
                switch(rule.rule_type) {
                    case 'abspecific':
                        ruleInfo = `ABSpecificRO(${ruleData.antibody},${ruleData.antigen1},${ruleData.antigen2},${ruleData.required_count})`;
                        break;
                    case 'homo':
                        ruleInfo = `Homo[${ruleData.antigen_pairs.map(pair => `(${pair[0]},${pair[1]})`).join(',')}]`;
                        break;
                    case 'hetero':
                        ruleInfo = `Hetero(${ruleData.antigen_a},${ruleData.antigen_b},${ruleData.required_count})`;
                        break;
                    case 'single':
                        ruleInfo = `SingleAG([${ruleData.antigens.join(',')}])`;
                        break;
                    case 'lowf':
                        ruleInfo = `LowF([${ruleData.antigens.join(',')}])`;
                        break;
                    default:
                        ruleInfo = 'Unknown rule type';
                }
                
                const ruleTypeBadge = `<span class="rule-type-badge rule-type-${rule.rule_type}">${rule.rule_type.toUpperCase()}</span>`;
                
                row.innerHTML = `
                    <td><strong>${rule.target_antigen}</strong></td>
                    <td>${ruleTypeBadge}</td>
                    <td><code>${ruleInfo}</code></td>
                    <td>${ruleData.required_count || 'N/A'}</td>
                    <td>${rule.description || '<em>No description</em>'}</td>
                    <td>
                        <button class="btn btn-sm btn-primary me-1" onclick="editRule(${rule.id})">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteRule(${rule.id})">Delete</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error loading rules:', error);
            document.getElementById('rulesTableBody').innerHTML = '<tr><td colspan="6" class="text-center text-danger">Error loading rules</td></tr>';
        });
}

// Edit rule
function editRule(id) {
    fetch(`/api/antibody-rules/${id}`)
        .then(response => response.json())
        .then(rule => {
            openRuleModal('edit', rule);
        })
        .catch(error => {
            console.error('Error loading rule:', error);
            alert('Error loading rule for editing');
        });
}

// Delete rule
function deleteRule(id) {
    if (confirm('Are you sure you want to delete this rule?')) {
        fetch(`/api/antibody-rules/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            loadRules();
            alert('Rule deleted successfully!');
        })
        .catch(error => {
            console.error('Error deleting rule:', error);
            alert('Error deleting rule');
        });
    }
}

// Delete all rules
function deleteAllRules() {
    if (confirm('Are you sure you want to delete all rules? This action cannot be undone.')) {
        fetch('/api/antibody-rules/delete-all', {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            loadRules();
            alert('All rules deleted successfully!');
        })
        .catch(error => {
            console.error('Error deleting all rules:', error);
            alert('Error deleting all rules');
        });
    }
}

// Initialize default rules
function initializeDefaultRules() {
    if (confirm('This will replace all existing rules with the default rules. Continue?')) {
        fetch('/api/antibody-rules/initialize', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            loadRules();
            alert('Default rules initialized successfully!');
        })
        .catch(error => {
            console.error('Error initializing default rules:', error);
            alert('Error initializing default rules');
        });
    }
} 

// Expose modal and form functions to global scope for button handlers
window.openRuleModal = openRuleModal;
window.resetForm = resetForm;
window.submitRuleForm = submitRuleForm;
window.editRule = editRule; 