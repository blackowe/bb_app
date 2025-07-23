document.addEventListener("DOMContentLoaded", async function () {
    try {
        // First try to get antigens from the database (Antigen entities)
        let response = await fetch("/api/antigens");
        let antigens = [];
        
        if (response.ok) {
            const data = await response.json();
            // The API returns an array of antigen objects, extract the names
            if (Array.isArray(data)) {
                antigens = data.map(antigen => antigen.name);
                console.log("✅ Loaded antigens from database:", antigens);
            }
        }
        
        // If no antigens from database, try to get them from antigram matrices
        if (!antigens || antigens.length === 0) {
            console.log("No antigens in database, trying antigram matrices...");
            response = await fetch("/api/antigens");
            if (response.ok) {
                const data = await response.json();
                antigens = data.antigens || [];
                console.log("✅ Loaded antigens from antigram matrices:", antigens);
            }
        }

        if (!antigens || antigens.length === 0) {
            console.warn("No antigens found in the system");
            showNoAntigensMessage();
            return;
        }

        // Populate the antigen input form dynamically
        populateAntigenTable(antigens);

        // Store antigen order globally for use in results table
        window.antigenHeaders = antigens;

        // Enable the search button
        enableSearchButton();

        console.log("✅ Antigens loaded successfully:", antigens);

    } catch (error) {
        console.error("❌ Error loading antigens:", error);
        showErrorMessage();
    }
});

function populateAntigenTable(antigens) {
    const antigenHeaderRow = document.getElementById("antigen-header-row");
    const antigenInputRow = document.getElementById("antigen-input-row");
    // Remove any previous system row
    if (antigenHeaderRow.previousElementSibling && antigenHeaderRow.previousElementSibling.id === 'system-header-row') {
        antigenHeaderRow.previousElementSibling.remove();
    }
    // Clear existing content
    antigenHeaderRow.innerHTML = "";
    antigenInputRow.innerHTML = "";

    // Group antigens by system
    const systemGroups = {};
    antigens.forEach(ag => {
        if (!systemGroups[ag.system]) systemGroups[ag.system] = [];
        systemGroups[ag.system].push(ag.name);
    });
    // Build system row
    const systemRow = document.createElement('tr');
    systemRow.id = 'system-header-row';
    for (const [system, ags] of Object.entries(systemGroups)) {
        const th = document.createElement('th');
        th.colSpan = ags.length;
        th.textContent = system;
        systemRow.appendChild(th);
    }
    // Insert system row above antigenHeaderRow
    antigenHeaderRow.parentNode.insertBefore(systemRow, antigenHeaderRow);

    // Add header row with all antigens
    antigens.forEach(ag => {
        antigenHeaderRow.innerHTML += `<th>${ag.name}</th>`;
        antigenInputRow.innerHTML += `<td><input type="text" class="form-control" name="${ag.name}" maxlength="1" placeholder="0 or +"></td>`;
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

    // Collect all non-empty antigen reactions
    for (const [key, value] of formData.entries()) {
        if (value && value.trim()) {
            antigenProfile[key] = value.trim();
        }
    }

    // Validate that at least one antigen reaction is provided
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
        const antigenHeaders = data.antigens || window.antigenHeaders || [];

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

    // Show results container
    resultsContainer.style.display = "block";

    // Build header with all antigens
    resultsHeaderRow.innerHTML = `
        <th>Lot Number</th>
        <th>Expiration Date</th>
        <th>Cell Number</th>
        ${antigenHeaders.map(antigen => `<th>${antigen}</th>`).join("")}
    `;

    // Populate the result rows
    results.forEach(result => {
        const row = document.createElement("tr");
        
        // Get reactions for all antigens in the correct order
        const reactions = antigenHeaders.map(antigen => {
            const reaction = result.cell.reactions[antigen];
            return reaction !== undefined && reaction !== null ? reaction : '-';
        });

        row.innerHTML = `
            <td>${result.antigram.lot_number}</td>
            <td>${result.antigram.expiration_date}</td>
            <td>${result.cell.cell_number}</td>
            ${reactions.map(reaction => `<td>${reaction}</td>`).join("")}
        `;
        
        resultsBody.appendChild(row);
    });

    console.log(`✅ Displayed ${results.length} matching cells`);
}
