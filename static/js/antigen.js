// Initialize Select2 for better dropdown experience
$(document).ready(function() {
    // Load initial data
    loadAntigens();
});

// Load antigens from the server
function loadAntigens() {
    fetch('/api/antigens')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('antigensTableBody');
            tbody.innerHTML = '';
            
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
            });
        })
        .catch(error => console.error('Error loading antigens:', error));
}

// Handle antigen form submission
document.getElementById('antigenForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('antigenName').value,
        system: document.getElementById('antigenSystem').value
    };
    
    // Handle "Other" system
    if (formData.system === 'Other') {
        formData.system = document.getElementById('otherSystem').value;
    }
    
    fetch('/api/antigens', {
        method: 'POST',
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
        loadAntigens();
        document.getElementById('antigenForm').reset();
        alert('Antigen added successfully!');
    })
    .catch(error => {
        console.error('Error adding antigen:', error);
        alert('Error adding antigen. Please try again.');
    });
});

// Handle system selection change
document.getElementById('antigenSystem').addEventListener('change', function() {
    const otherSystemGroup = document.getElementById('otherSystemGroup');
    if (this.value === 'Other') {
        otherSystemGroup.style.display = 'block';
            } else {
        otherSystemGroup.style.display = 'none';
    }
});

// Delete antigen
function deleteAntigen(name) {
    if (confirm(`Are you sure you want to delete antigen '${name}'?`)) {
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
            alert('Antigen deleted successfully!');
    })
        .catch(error => {
            console.error('Error deleting antigen:', error);
            alert('Error deleting antigen');
        });
    }
}

// Initialize base antigens
function initializeBaseAntigens() {
    if (confirm('This will replace all existing antigens with the base antigens. Continue?')) {
        fetch('/api/antigens/initialize', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
            loadAntigens();
            alert('Base antigens initialized successfully!');
    })
        .catch(error => {
            console.error('Error initializing base antigens:', error);
            alert('Error initializing base antigens');
        });
    }
} 