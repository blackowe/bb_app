function highlightAntigenInput(input) {
    const val = input.value.trim();
    
    // Remove any existing validation classes
    input.classList.remove('valid-input', 'invalid-input', 'empty-input');
    
    if (val === "0" || val === "+") {
        input.classList.add('valid-input');
        input.style.borderColor = '#007bff';
        input.style.backgroundColor = '#e7f3ff'; // Light blue background
        // Different text colors for 0 and +
        if (val === "0") {
            input.style.color = '#000000'; // Black text for 0
        } else {
            input.style.color = '#6c757d'; // Light grey text for +
        }
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