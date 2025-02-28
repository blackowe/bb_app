document.addEventListener("DOMContentLoaded", async function () {
    try {
        // Fetch antigen names from the API
        const response = await fetch("/api/antigens");
        if (!response.ok) {
            throw new Error("Failed to fetch antigen list.");
        }

        const data = await response.json();
        const antigens = data.antigens;

        // Populate the antigen input form dynamically
        const antigenHeaderRow = document.getElementById("antigen-header-row");
        const antigenInputRow = document.getElementById("antigen-input-row");

        antigenHeaderRow.innerHTML = `<th>Antigen</th>`; // Label first column
        antigenInputRow.innerHTML = `<td>Reaction</td>`; // Align first column

        antigens.forEach(antigen => {
            antigenHeaderRow.innerHTML += `<th>${antigen}</th>`;
            antigenInputRow.innerHTML += `<td><input type="text" class="reaction-input" name="${antigen}" maxlength="1" placeholder="0 or +"></td>`;
        });

        // Store antigen order globally for use in results table
        window.antigenHeaders = antigens;

    } catch (error) {
        console.error("❌ Error loading antigens:", error);
    }
});

// Handle form submission and search for matching cells
document.getElementById("cell-finder-form").addEventListener("submit", async function (event) {
    event.preventDefault();

    const antigenProfile = {};
    const formData = new FormData(event.target);

    for (const [key, value] of formData.entries()) {
        if (value) {
            antigenProfile[key] = value.trim();
        }
    }

    try {
        const response = await fetch("/cell_finder", {  // Matches Flask route
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ antigenProfile }),
        });

        if (!response.ok) {
            console.error("❌ Failed to fetch matching cells:", response.statusText);
            return;
        }

        const data = await response.json();
        console.log("✅ API Response:", data);

        const results = data.results;
        const antigenHeaders = data.antigens || [];  // Use the order returned by the backend

        const resultsHeaderRow = document.getElementById("results-header-row");
        const resultsBody = document.getElementById("results-body");

        resultsBody.innerHTML = ""; // Clear previous results

        if (results.length === 0) {
            resultsBody.innerHTML = "<tr><td colspan='13'>No matching cells found.</td></tr>";
            return;
        }

        // Ensure antigen headers appear in the correct order in the results table
        resultsHeaderRow.innerHTML = `
            <th>Lot Number</th>
            <th>Expiration Date</th>
            <th>Cell Number</th>
            ${antigenHeaders.map(antigen => `<th>${antigen}</th>`).join("")}
        `;

        // Populate the result rows correctly (remove input fields)
        results.forEach(result => {
            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${result.antigram.lot_number}</td>
                <td>${result.antigram.expiration_date}</td>
                <td>${result.cell.cell_number}</td>
                ${result.cell.reactions.map(reaction => `<td>${reaction !== undefined ? reaction : '-'}</td>`).join("")}
            `;
            resultsBody.appendChild(row);
        });

    } catch (error) {
        console.error("❌ Error in Cell Finder:", error);
    }
});
