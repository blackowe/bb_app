document.addEventListener("DOMContentLoaded", async function () {
    await loadAntigenInputTable();
    document.getElementById("reset-btn").addEventListener("click", resetAntigenInputs);
});

async function loadAntigenInputTable() {
    try {
        // Fetch valid antigens
        const validResp = await fetch("/api/antigens/valid");
        const validAntigens = await validResp.json();
        // Fetch default order
        const orderResp = await fetch("/api/antigens/default-order");
        const panocellOrder = await orderResp.json();
        // Group by system
        const systemGroups = {};
        validAntigens.forEach(ag => {
            if (!systemGroups[ag.system]) systemGroups[ag.system] = [];
            systemGroups[ag.system].push(ag.name);
        });
        // Build antigen order: Panocell order first, then any remaining valid antigens grouped by system
        let antigenOrder = [];
        let used = new Set();
        panocellOrder.forEach(ag => {
            const agObj = validAntigens.find(a => a.name === ag);
            if (agObj && !used.has(ag)) {
                antigenOrder.push(ag);
                used.add(ag);
            }
        });
        Object.keys(systemGroups).forEach(sys => {
            systemGroups[sys].forEach(ag => {
                if (!used.has(ag)) {
                    antigenOrder.push(ag);
                    used.add(ag);
                }
            });
        });
        renderAntigenInputTable(validAntigens, antigenOrder, systemGroups);
        window.antigenHeaders = antigenOrder;
        enableSearchButton();
    } catch (error) {
        console.error("❌ Error loading antigens:", error);
        showErrorMessage();
    }
}

function renderAntigenInputTable(validAntigens, antigenOrder, systemGroups) {
    const antigenInputTable = document.getElementById("antigen-input-table");
    const thead = antigenInputTable.querySelector("thead");
    const tbody = antigenInputTable.querySelector("tbody");
    // Remove all rows
    thead.innerHTML = "";
    tbody.innerHTML = "";
    // --- System header row ---
    const systemHeaderRow = document.createElement("tr");
    systemHeaderRow.id = "system-header-row";
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
    thead.appendChild(systemHeaderRow);
    // --- Antigen name row ---
    const antigenHeaderRow = document.createElement("tr");
    antigenHeaderRow.id = "antigen-header-row";
    antigenOrder.forEach((agName, idx) => {
        const th = document.createElement('th');
        th.className = 'antigen-dnd-th';
        th.textContent = agName;
        th.dataset.idx = idx;
        th.dataset.antigen = agName;
        antigenHeaderRow.appendChild(th);
    });
    thead.appendChild(antigenHeaderRow);
    // --- Input row ---
    const inputRow = document.createElement("tr");
    inputRow.id = "antigen-input-row";
    antigenOrder.forEach((agName, idx) => {
        const td = document.createElement('td');
        td.style.textAlign = 'center';
        td.style.padding = '0';
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control antigen-input-box';
        input.name = agName;
        input.maxLength = 1;
        input.autocomplete = 'off';
        input.addEventListener('input', function() {
            validateAntigenInput(input);
        });
        input.addEventListener('blur', function() {
            validateAntigenInput(input);
        });
        td.appendChild(input);
        inputRow.appendChild(td);
    });
    tbody.appendChild(inputRow);
    
    // Add instruction text below the table
    const instructionDiv = document.createElement('div');
    instructionDiv.className = 'mt-2 text-muted';
    instructionDiv.style.fontSize = '1.5em';
    instructionDiv.innerHTML = '<small>💡 <strong>Valid inputs:</strong> Enter "0" for negative reactions or "+" for positive reactions only.</small>';
    antigenInputTable.parentNode.appendChild(instructionDiv);
}

function validateAntigenInput(input) {
    const val = input.value.trim();
    if (val === "0" || val === "+") {
        input.style.borderColor = '#007bff';
        input.style.boxShadow = '0 0 0 0.2rem rgba(0,123,255,.25)';
        input.style.backgroundColor = '#e7f3ff'; // Light blue background
    } else if (val === "") {
        input.style.borderColor = '#ccc';
        input.style.boxShadow = '';
        input.style.backgroundColor = '#fff'; // White background
    } else {
        input.style.borderColor = '#dc3545';
        input.style.boxShadow = '0 0 0 0.2rem rgba(220,53,69,.25)';
        input.style.backgroundColor = '#fff'; // White background for invalid
    }
}

function resetAntigenInputs() {
    document.querySelectorAll('.antigen-input-box').forEach(input => {
        input.value = '';
        validateAntigenInput(input);
    });
}

function enableSearchButton() {
    const searchBtn = document.getElementById("search-btn");
    if (searchBtn) {
        searchBtn.disabled = false;
        searchBtn.innerHTML = "Search";
    }
}

function showNoAntigensMessage() {
    const antigenHeaderRow = document.getElementById("antigen-header-row");
    const antigenInputRow = document.getElementById("antigen-input-row");
    const searchBtn = document.getElementById("search-btn");
    
    antigenHeaderRow.innerHTML = `<th>No Antigens</th>`;
    antigenInputRow.innerHTML = `<td class="text-muted">No antigens found. Please create antigrams first.</td>`;
    
    if (searchBtn) {
        searchBtn.disabled = true;
        searchBtn.innerHTML = "No Antigens Available";
    }
}

function showErrorMessage() {
    const antigenHeaderRow = document.getElementById("antigen-header-row");
    const antigenInputRow = document.getElementById("antigen-input-row");
    const searchBtn = document.getElementById("search-btn");
    
    antigenHeaderRow.innerHTML = `<th>Error</th>`;
    antigenInputRow.innerHTML = `<td class="text-danger">Failed to load antigens. Please refresh the page.</td>`;
    
    if (searchBtn) {
        searchBtn.disabled = true;
        searchBtn.innerHTML = "Error Loading Antigens";
    }
}

// Handle form submission and search for matching cells
document.getElementById("cell-finder-form").addEventListener("submit", async function (event) {
    event.preventDefault();
    const antigenProfile = {};
    const formData = new FormData(event.target);
    let hasInvalid = false;
    // Collect all non-empty antigen reactions, validate
    for (const [key, value] of formData.entries()) {
        const val = value.trim();
        if (val) {
            if (val !== "0" && val !== "+") {
                hasInvalid = true;
                const input = document.querySelector(`input[name='${key}']`);
                if (input) validateAntigenInput(input);
            } else {
                antigenProfile[key] = val;
            }
        }
    }
    if (hasInvalid) {
        alert("Please enter only '0', '+', or leave blank for antigen reactions.");
        return;
    }
    if (Object.keys(antigenProfile).length === 0) {
        alert("Please enter at least one antigen reaction to search for.");
        return;
    }

    console.log("🔍 Searching for antigen profile:", antigenProfile);

    // Show loading state
    const searchBtn = document.getElementById("search-btn");
    const originalText = searchBtn.innerHTML;
    searchBtn.disabled = true;
    searchBtn.innerHTML = '<span class="loading-spinner"></span> Searching...';

    try {
        const response = await fetch("/cell_finder", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ antigenProfile }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log("✅ API Response:", data);

        const results = data.results;
        // Use the same antigen order as the input table (Panocell order)
        const antigenHeaders = window.antigenHeaders || [];

        displayResults(results, antigenHeaders);

    } catch (error) {
        console.error("❌ Error in Cell Finder:", error);
        alert(`Error searching for cells: ${error.message}`);
    } finally {
        // Restore button state
        searchBtn.disabled = false;
        searchBtn.innerHTML = originalText;
    }
});

function displayResults(results, antigenHeaders) {
    const resultsContainer = document.getElementById("results");
    const resultsHeaderRow = document.getElementById("results-header-row");
    const resultsBody = document.getElementById("results-body");

    // Clear previous results
    resultsBody.innerHTML = "";

    if (results.length === 0) {
        resultsContainer.style.display = "block";
        resultsBody.innerHTML = "<tr><td colspan='" + (3 + antigenHeaders.length) + "' class='text-center text-muted'>No matching cells found.</td></tr>";
        return;
    }

    // Sort results: by expiration date (latest first), then by cell number
    results.sort((a, b) => {
        const dateA = new Date(a.antigram.expiration_date);
        const dateB = new Date(b.antigram.expiration_date);
        
        // Sort by expiration date (descending - latest first)
        if (dateA > dateB) return -1;
        if (dateA < dateB) return 1;
        
        // If same expiration date, sort by cell number (ascending)
        const cellA = parseInt(a.cell.cell_number);
        const cellB = parseInt(b.cell.cell_number);
        return cellA - cellB;
    });

    // Limit to 15 results
    const limitedResults = results.slice(0, 15);

    // Show results container
    resultsContainer.style.display = "block";

    // Build header with correct column order
    resultsHeaderRow.innerHTML = `
        <th>Lot Number</th>
        <th>Cell Number</th>
        <th>Expiration Date</th>
        ${antigenHeaders.map(antigen => `<th>${antigen}</th>`).join("")}
    `;

    // Get today's date for expiration comparison
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Set to start of day for accurate comparison
    
    console.log("Today's date for comparison:", today.toISOString().split('T')[0]);

    // Populate the result rows
    limitedResults.forEach(result => {
        const row = document.createElement("tr");
        
        // Format expiration date as MM/DD/YYYY
        const expirationDate = new Date(result.antigram.expiration_date);
        const formattedDate = expirationDate.toLocaleDateString('en-US', {
            month: '2-digit',
            day: '2-digit',
            year: 'numeric'
        });
        
        // Determine if date is expired (compare dates only, not time)
        const expirationDateOnly = new Date(expirationDate.getFullYear(), expirationDate.getMonth(), expirationDate.getDate());
        const isExpired = expirationDateOnly < today;
        
        // Use inline styles to ensure color coding works
        const dateStyle = isExpired ? 'style="color: #dc3545 !important; font-weight: bold !important;"' : 'style="color: black !important;"';
        
        // Debug logging
        console.log(`Date: ${formattedDate}, Original: ${result.antigram.expiration_date}, Is Expired: ${isExpired}, Style: ${dateStyle}`);
        
        // Get reactions for all antigens in the correct order
        const reactions = antigenHeaders.map(antigen => {
            const reaction = result.cell.reactions[antigen];
            return reaction !== undefined && reaction !== null ? reaction : '-';
        });

        row.innerHTML = `
            <td>${result.antigram.lot_number}</td>
            <td>${result.cell.cell_number}</td>
            <td ${dateStyle}>${formattedDate}</td>
            ${reactions.map(reaction => `<td>${reaction}</td>`).join("")}
        `;
        
        resultsBody.appendChild(row);
    });

    console.log(`✅ Displayed ${limitedResults.length} matching cells (limited to 15)`);
}
