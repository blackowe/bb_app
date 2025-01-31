document.addEventListener("DOMContentLoaded", async function () {
    try {
        // Fetch antigen names from the API
        const response = await fetch("/api/antigens");
        if (!response.ok) {
            throw new Error("Failed to fetch antigen list.");
        }

        const data = await response.json();
        const antigens = data.antigens;

        // ✅ Populate the antigen input form dynamically
        const antigenHeaderRow = document.getElementById("antigen-header-row");
        const antigenInputRow = document.getElementById("antigen-input-row");

        antigenHeaderRow.innerHTML = "";  // Clear existing headers
        antigenInputRow.innerHTML = "";   // Clear existing inputs

        antigens.forEach(antigen => {
            antigenHeaderRow.innerHTML += `<th>${antigen}</th>`;
            antigenInputRow.innerHTML += `<td><input type="text" name="${antigen}" maxlength="1" placeholder="0 or +"></td>`;
        });

        // ✅ Populate the results table dynamically
        const resultsHeaderRow = document.getElementById("results-header-row");
        resultsHeaderRow.innerHTML = `
            <th>Lot Number</th>
            <th>Expiration Date</th>
            <th>Cell Number</th>
        `; // Keep fixed columns

        antigens.forEach(antigen => {
            resultsHeaderRow.innerHTML += `<th>${antigen}</th>`;
        });

        // ✅ Store antigen order in global variable for consistent reference
        window.antigenHeaders = antigens;

    } catch (error) {
        console.error("Error loading antigens:", error);
    }
});

// ✅ Handle form submission and search for matching cells
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
        const response = await fetch("/cell_finder", {  // ✅ Matches Flask route
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ antigenProfile }),
        });

        if (!response.ok) {
            console.error("Failed to fetch matching cells:", response.statusText);
            return;
        }

        const results = await response.json();
        console.log("API Response:", results);

        // ✅ Ensure antigen headers are correctly mapped (avoid inconsistencies)
        const antigenHeaders = window.antigenHeaders || [];
        
        // ✅ Populate results table
        const resultsBody = document.getElementById("results-body");
        resultsBody.innerHTML = ""; // Clear previous results

        if (results.length > 0) {
            results.forEach(result => {
                const row = document.createElement("tr");

                row.innerHTML = `
                    <td>${result.antigram.lot_number}</td>
                    <td>${result.antigram.expiration_date}</td>
                    <td>${result.cell.cell_number}</td>
                    ${antigenHeaders.map(antigen => {
                        let reaction = result.cell.reactions[antigen]; // Fetch reaction
                        return `<td>${reaction !== undefined ? reaction : "-"}</td>`; // Ensure it shows correct values
                    }).join("")}
                `;
                resultsBody.appendChild(row);
            });
        } else {
            resultsBody.innerHTML = "<tr><td colspan='13'>No matching cells found.</td></tr>";
        }
    } catch (error) {
        console.error("Error in Cell Finder:", error);
    }
});
