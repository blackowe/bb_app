// Define valid antigen pairs
const validAntigenPairs = {
    'E': ['e'],
    'e': ['E'],
    'C': ['c'],
    'c': ['C'],
    'K': ['k'],
    'k': ['K'],
    'Fya': ['Fyb'],
    'Fyb': ['Fya'],
    'Jka': ['Jkb'],
    'Jkb': ['Jka'],
    'M': ['N'],
    'N': ['M'],
    'S': ['s'],
    's': ['S'],
    'Lea': ['Leb'],
    'Leb': ['Lea']
};

// Initialize Select2 for multiple select
$(document).ready(function() {
    $('#ruleAntigens').select2({
        placeholder: 'Select Rule Antigens',
        allowClear: true
    });
    
    // Load initial data
    loadAntigens();
    loadRules();
    
    // Handle antigen system change
    $('#antigenSystem').change(function() {
        if ($(this).val() === 'Other') {
            $('#otherSystemGroup').show();
        } else {
            $('#otherSystemGroup').hide();
        }
    });

    // Handle dependency addition
    $('#addDependency').click(function() {
        addDependencyField();
    });

    // Handle rule type change
    $('#ruleType').change(function() {
        updateRuleFields();
    });
});

// Add new dependency field
function addDependencyField() {
    const template = `
        <div class="dependency-group mb-3">
            <div class="row">
                <div class="col-md-5">
                    <label class="form-label">Required Antigen</label>
                    <select class="form-select dependency-antigen">
                        <option value="">Select Antigen</option>
                    </select>
                </div>
                <div class="col-md-5">
                    <label class="form-label">Required Reaction</label>
                    <select class="form-select dependency-reaction">
                        <option value="+">Positive (+)</option>
                        <option value="0">Negative (0)</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <label class="form-label">&nbsp;</label>
                    <button type="button" class="btn btn-danger w-100 remove-dependency">Remove</button>
                </div>
            </div>
        </div>
    `;
    
    $('#dependenciesContainer').append(template);
    populateAntigenSelect($('#dependenciesContainer .dependency-antigen').last());
    
    // Show remove button for all but the first dependency
    if ($('.dependency-group').length > 1) {
        $('.remove-dependency').show();
    }
}

// Remove dependency field
$(document).on('click', '.remove-dependency', function() {
    $(this).closest('.dependency-group').remove();
    if ($('.dependency-group').length === 1) {
        $('.remove-dependency').hide();
    }
});

// Update rule fields based on rule type
function updateRuleFields() {
    const ruleType = $('#ruleType').val();
    
    // Reset fields
    $('#ruleAntigens').val(null).trigger('change');
    $('#requiredCount').val(1);
    
    // Update based on rule type
    switch(ruleType) {
        case 'homozygous':
            $('#ruleAntigens').attr('multiple', false);
            break;
        case 'heterozygous':
            $('#ruleAntigens').attr('multiple', false);
            break;
        case 'composite':
            $('#ruleAntigens').attr('multiple', true);
            break;
    }
}

// Load antigens from the server
function loadAntigens() {
    fetch('/api/antigens')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('antigensTableBody');
            tbody.innerHTML = '';
            
            // Update select dropdowns
            const targetAntigenSelect = document.getElementById('targetAntigen');
            const ruleAntigensSelect = document.getElementById('ruleAntigens');
            
            // Clear existing options
            targetAntigenSelect.innerHTML = '<option value="">Select Target Antigen</option>';
            ruleAntigensSelect.innerHTML = '';
            
            data.forEach(antigen => {
                // Add to table
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${antigen.name}</td>
                    <td>${antigen.system}</td>
                    <td>
                        <button class="btn btn-sm btn-danger" onclick="deleteAntigen('${antigen.name}')">Delete</button>
                    </td>
                `;
                tbody.appendChild(row);
                
                // Add to select dropdowns
                const option = new Option(antigen.name, antigen.name);
                targetAntigenSelect.add(option.cloneNode(true));
                ruleAntigensSelect.add(option);
            });
            
            // Refresh Select2
            $('#ruleAntigens').trigger('change');
            populateAntigenSelect($('.dependency-antigen'));
        })
        .catch(error => console.error('Error loading antigens:', error));
}

// Populate antigen select dropdowns
function populateAntigenSelect(selects) {
    fetch('/api/antigens')
        .then(response => response.json())
        .then(data => {
            selects.each(function() {
                const select = $(this);
                select.html('<option value="">Select Antigen</option>');
                data.forEach(antigen => {
                    select.append(new Option(antigen.name, antigen.name));
                });
            });
        })
        .catch(error => console.error('Error loading antigens:', error));
}

// Handle rule form submission
document.getElementById('antigenRuleForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Validate form
    if (!validateRuleForm()) {
        return;
    }
    
    const formData = {
        target_antigen: document.getElementById('targetAntigen').value,
        rule_type: document.getElementById('ruleType').value,
        rule_conditions: getRuleConditions(),
        required_count: parseInt(document.getElementById('requiredCount').value),
        description: document.getElementById('description').value,
        dependencies: getDependencies()
    };
    
    const ruleId = document.getElementById('ruleId').value;
    const url = ruleId ? `/api/antigen-rules/${ruleId}` : '/api/antigen-rules';
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
    })
    .catch(error => console.error('Error saving rule:', error));
});

// Get rule conditions based on rule type
function getRuleConditions() {
    const ruleType = document.getElementById('ruleType').value;
    const ruleAntigens = $('#ruleAntigens').val();
    
    switch(ruleType) {
        case 'homozygous':
        case 'heterozygous':
            return JSON.stringify({
                antigen: ruleAntigens[0],
                cell_reaction: "+",
                paired_antigen: getPairedAntigen(ruleAntigens[0]),
                paired_reaction: ruleType === 'homozygous' ? "0" : "+"
            });
        case 'composite':
            return JSON.stringify({
                conditions: ruleAntigens.map(antigen => ({
                    antigen: antigen,
                    cell_reaction: "+",
                    paired_antigen: getPairedAntigen(antigen),
                    paired_reaction: "0"
                })),
                operator: "AND"
            });
    }
}

// Get dependencies from form
function getDependencies() {
    const dependencies = [];
    $('.dependency-group').each(function() {
        const antigen = $(this).find('.dependency-antigen').val();
        const reaction = $(this).find('.dependency-reaction').val();
        if (antigen) {
            dependencies.push({
                antigen: antigen,
                reaction: reaction
            });
        }
    });
    
    if (dependencies.length === 0) {
        return null;
    }
    
    return JSON.stringify({
        required_antigens: dependencies.map(d => d.antigen),
        required_reactions: dependencies.map(d => d.reaction),
        description: "Rule dependencies"
    });
}

// Validate rule form
function validateRuleForm() {
    const ruleType = document.getElementById('ruleType').value;
    const ruleAntigens = $('#ruleAntigens').val();
    
    if (!ruleType) {
        alert('Please select a rule type');
        return false;
    }
    
    if (!ruleAntigens || ruleAntigens.length === 0) {
        alert('Please select at least one rule antigen');
        return false;
    }
    
    // Validate dependencies
    const dependencies = getDependencies();
    if (dependencies) {
        try {
            const deps = JSON.parse(dependencies);
            if (deps.required_antigens.length !== deps.required_reactions.length) {
                alert('Invalid dependency configuration');
                return false;
            }
        } catch (e) {
            alert('Invalid dependency format');
            return false;
        }
    }
    
    return true;
}

// Get paired antigen (simplified version)
function getPairedAntigen(antigen) {
    const pairs = {
        'E': 'e',
        'e': 'E',
        'C': 'c',
        'c': 'C',
        'K': 'k',
        'k': 'K',
        'Fya': 'Fyb',
        'Fyb': 'Fya',
        'Jka': 'Jkb',
        'Jkb': 'Jka',
        'M': 'N',
        'N': 'M',
        'S': 's',
        's': 'S',
        'Lea': 'Leb',
        'Leb': 'Lea'
    };
    return pairs[antigen] || '';
}

// Reset form
function resetForm() {
    document.getElementById('antigenRuleForm').reset();
    document.getElementById('ruleId').value = '';
    $('#ruleAntigens').val(null).trigger('change');
    $('#dependenciesContainer').html(`
        <div class="dependency-group mb-3">
            <div class="row">
                <div class="col-md-5">
                    <label class="form-label">Required Antigen</label>
                    <select class="form-select dependency-antigen">
                        <option value="">Select Antigen</option>
                    </select>
                </div>
                <div class="col-md-5">
                    <label class="form-label">Required Reaction</label>
                    <select class="form-select dependency-reaction">
                        <option value="+">Positive (+)</option>
                        <option value="0">Negative (0)</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <label class="form-label">&nbsp;</label>
                    <button type="button" class="btn btn-danger w-100 remove-dependency" style="display: none;">Remove</button>
                </div>
            </div>
        </div>
    `);
    populateAntigenSelect($('.dependency-antigen'));
}

// Load rules from the server
function loadRules() {
    fetch('/api/antigen-rules')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('rulesTableBody');
            tbody.innerHTML = '';
            
            data.forEach(rule => {
        const row = document.createElement('tr');
                const dependencies = rule.dependencies ? 
                    JSON.parse(rule.dependencies).required_antigens.join(', ') : 
                    'None';
                
        row.innerHTML = `
                    <td>${rule.target_antigen}</td>
                    <td>${rule.rule_type}</td>
                    <td>${JSON.parse(rule.rule_conditions).antigen || 'Multiple'}</td>
            <td>${rule.required_count}</td>
                    <td>${dependencies}</td>
                    <td>${rule.description || ''}</td>
            <td>
                        <button class="btn btn-sm btn-primary me-2" onclick="editRule(${rule.id})">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteRule(${rule.id})">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
        })
        .catch(error => console.error('Error loading rules:', error));
}

// Edit rule
function editRule(id) {
    fetch(`/api/antigen-rules/${id}`)
        .then(response => response.json())
        .then(rule => {
            document.getElementById('ruleId').value = rule.id;
            document.getElementById('targetAntigen').value = rule.target_antigen;
            document.getElementById('ruleType').value = rule.rule_type;
            
            const conditions = JSON.parse(rule.rule_conditions);
            if (rule.rule_type === 'composite') {
                $('#ruleAntigens').val(conditions.conditions.map(c => c.antigen)).trigger('change');
            } else {
                $('#ruleAntigens').val([conditions.antigen]).trigger('change');
            }
            
            document.getElementById('requiredCount').value = rule.required_count;
            document.getElementById('description').value = rule.description || '';
            
            // Set dependencies
            $('#dependenciesContainer').empty();
            if (rule.dependencies) {
                const deps = JSON.parse(rule.dependencies);
                deps.required_antigens.forEach((antigen, index) => {
                    addDependencyField();
                    const lastGroup = $('.dependency-group').last();
                    lastGroup.find('.dependency-antigen').val(antigen);
                    lastGroup.find('.dependency-reaction').val(deps.required_reactions[index]);
                });
            } else {
                addDependencyField();
            }
        })
        .catch(error => console.error('Error loading rule:', error));
}

// Delete antigen
function deleteAntigen(name) {
    if (!confirm(`Are you sure you want to delete antigen ${name}?`)) {
        return;
    }
    
    fetch(`/api/antigens/${name}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        loadAntigens();
    })
    .catch(error => console.error('Error deleting antigen:', error));
}

// Delete rule
function deleteRule(id) {
    if (!confirm('Are you sure you want to delete this rule?')) {
        return;
    }
    
    fetch(`/api/antigen-rules/${id}`, {
            method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        loadRules();
    })
    .catch(error => console.error('Error deleting rule:', error));
}

// Delete all rules
function deleteAllRules() {
    if (!confirm('Are you sure you want to delete all rules? This cannot be undone.')) {
        return;
    }
    
    fetch('/api/antigen-rules/delete-all', {
            method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        loadRules();
    })
    .catch(error => console.error('Error deleting all rules:', error));
}

// Initialize default rules
function initializeDefaultRules() {
    if (!confirm('Are you sure you want to initialize default rules? This will delete all existing rules.')) {
        return;
    }
    
    fetch('/api/antigen-rules/initialize', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        loadRules();
    })
    .catch(error => console.error('Error initializing default rules:', error));
} 