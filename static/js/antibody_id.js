document.addEventListener("DOMContentLoaded", () => {
    const searchBar = document.getElementById("search-bar");
    const searchBtn = document.getElementById("search-btn");
    const antigramTable = document.getElementById("antigram-table").querySelector("tbody");
    const reactionFormContainer = document.getElementById("reaction-form-container");
    const saveAllReactionsBtn = document.getElementById("save-all-reactions-btn");
    const summaryTable = document.getElementById("summary-table").querySelector("tbody");

    let selectedAntigramId = null;
    let selectedLotNumber = null; // Store the actual selected lot number

    // Search for antigrams
    searchBtn.addEventListener("click", async () => {
        const searchQuery = searchBar.value.trim();
        if (!searchQuery) {
            alert("Please enter a lot number to search.");
            return;
        }
    
        // Fetch filtered antigrams
        const response = await fetch(`/api/antigrams?search=${encodeURIComponent(searchQuery)}`);
        if (!response.ok) {
            alert("Failed to fetch antigrams.");
            return;
        }
    
        const antigrams = await response.json();
    
        // Clear the table before populating new results
        antigramTable.innerHTML = "";
    
        if (antigrams.length === 0) {
            antigramTable.innerHTML = `
                <tr>
                    <td colspan="2">No matching antigrams found.</td>
                </tr>
            `;
            return;
        }
    
        // Populate the antigram table with filtered results
        antigrams.forEach(antigram => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${antigram.lot_number}</td>
                <td>
                    <button 
                        class="select-btn" 
                        data-antigram-id="${antigram.id}" 
                        data-lot-number="${antigram.lot_number}">
                        Select
                    </button>
                </td>
            `;
            antigramTable.appendChild(row);
        });
    });

    // Handle Select button click
    antigramTable.addEventListener("click", async (e) => {
        if (e.target.classList.contains("select-btn")) {
            selectedAntigramId = e.target.dataset.antigramId;
            selectedLotNumber = e.target.dataset.lotNumber; // Capture the correct lot number

            const response = await fetch(`/api/antigrams/${selectedAntigramId}`);
            if (!response.ok) {
                alert("Failed to fetch antigram details.");
                return;
            }

            const antigram = await response.json();

            // Clear and populate the reaction form container
            reactionFormContainer.innerHTML = `
                <h3>Enter Patient Reactions for Lot ${selectedLotNumber}</h3>
            `;

            antigram.cells.forEach(cell => {
                const formRow = document.createElement("div");
                formRow.classList.add("form-row");
                formRow.innerHTML = `
                    <span>Cell Number: ${cell.cell_number}</span>
                    <input 
                        type="text" 
                        id="patient-rxn-${cell.cell_number}" 
                        data-cell-number="${cell.cell_number}" 
                        placeholder="+ or 0 (optional)">
                `;
                reactionFormContainer.appendChild(formRow);
            });

            // Show the Save All Reactions button
            saveAllReactionsBtn.style.display = "block";
        }
    });

    // Save all entered reactions
    saveAllReactionsBtn.addEventListener("click", async () => {
        if (!selectedAntigramId || !selectedLotNumber) {
            alert("No antigram selected.");
            return;
        }
    
        const inputs = reactionFormContainer.querySelectorAll("input[data-cell-number]");
        const reactions = Array.from(inputs)
            .filter(input => input.value.trim() !== "")
            .map(input => ({
                cell_number: input.dataset.cellNumber,
                patient_rxn: input.value.trim(),
            }));
    
        if (reactions.length === 0) {
            alert("No reactions entered to save.");
            return;
        }
    
        const response = await fetch("/api/patient-reaction", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                antigram_id: selectedAntigramId,
                reactions: reactions,
            }),
        });
    
        if (response.ok) {
            alert("All reactions saved successfully!");
    
            // Update the summary table
            reactions.forEach(reaction => {
                const existingRow = summaryTable.querySelector(
                    `tr[data-lot-number="${selectedLotNumber}"][data-cell-number="${reaction.cell_number}"]`
                );
    
                if (existingRow) {
                    // Update the existing row
                    existingRow.innerHTML = `
                        <td>${selectedLotNumber}</td>
                        <td>${reaction.cell_number}</td>
                        <td>${reaction.patient_rxn}</td>
                    `;
                } else {
                    // Add a new row
                    const row = document.createElement("tr");
                    row.setAttribute("data-lot-number", selectedLotNumber);
                    row.setAttribute("data-cell-number", reaction.cell_number);
                    row.innerHTML = `
                        <td>${selectedLotNumber}</td>
                        <td>${reaction.cell_number}</td>
                        <td>${reaction.patient_rxn}</td>
                    `;
                    summaryTable.appendChild(row);
                }
            });
        } else {
            alert("Failed to save reactions.");
        }
    });


});
