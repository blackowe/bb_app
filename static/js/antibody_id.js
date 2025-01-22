document.addEventListener("DOMContentLoaded", () => {
    const searchBar = document.getElementById("search-bar");
    const searchBtn = document.getElementById("search-btn");
    const antigramTable = document.getElementById("antigram-table").querySelector("tbody");
    const reactionFormContainer = document.getElementById("reaction-form-container");
    const saveAllReactionsBtn = document.getElementById("save-all-reactions-btn");
    const summaryTable = document.getElementById("summary-table").querySelector("tbody");
    const abidResultsContainer = document.getElementById("abid-results"); // Reference the ABID results container

    let selectedAntigramId = null;
    let selectedLotNumber = null;

    // Clear state on page load
    window.addEventListener("load", () => {
        summaryTable.innerHTML = "";
        abidResultsContainer.innerHTML = "";
    });

    // Search for antigrams
    searchBtn.addEventListener("click", async () => {
        try {
            // Clear patient reactions
            const clearResponse = await fetch("/api/clear-patient-reactions", { method: "DELETE" });
            if (!clearResponse.ok) throw new Error("Failed to clear patient reactions.");

            console.log("Patient reactions cleared successfully.");
        } catch (error) {
            console.error("Error clearing patient reactions:", error);
        }

        const searchQuery = searchBar.value.trim();
        if (!searchQuery) {
            alert("Please enter a lot number to search.");
            return;
        }

        const response = await fetch(`/api/antigrams?search=${encodeURIComponent(searchQuery)}`);
        if (!response.ok) {
            alert("Failed to fetch antigrams.");
            return;
        }

        const antigrams = await response.json();
        antigramTable.innerHTML = "";

        if (antigrams.length === 0) {
            antigramTable.innerHTML = `<tr><td colspan="2">No matching antigrams found.</td></tr>`;
            return;
        }

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

        // Clear the reaction form, summary table, and ABID results
        reactionFormContainer.innerHTML = "";
        summaryTable.innerHTML = "";
        abidResultsContainer.innerHTML = "";
    });

    // Handle antigram selection
    antigramTable.addEventListener("click", async (e) => {
        if (e.target.classList.contains("select-btn")) {
            selectedAntigramId = e.target.dataset.antigramId;
            selectedLotNumber = e.target.dataset.lotNumber;

            const response = await fetch(`/api/antigrams/${selectedAntigramId}`);
            if (!response.ok) {
                alert("Failed to fetch antigram details.");
                return;
            }

            const antigram = await response.json();
            reactionFormContainer.innerHTML = `<h3>Enter Patient Reactions for Lot ${selectedLotNumber}</h3>`;

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

            saveAllReactionsBtn.style.display = "block";

            // Clear summary and ABID results when a new antigram is selected
            summaryTable.innerHTML = "";
            abidResultsContainer.innerHTML = "";
        }
    });

    // Save patient reactions and fetch ABID results
    saveAllReactionsBtn.addEventListener("click", async () => {
        try {
            const inputs = reactionFormContainer.querySelectorAll("input[data-cell-number]");
            const reactions = Array.from(inputs)
                .map(input => ({
                    cell_number: input.dataset.cellNumber,
                    patient_rxn: input.value.trim(),
                }));

            const response = await fetch("/api/patient-reaction", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ antigram_id: selectedAntigramId, reactions }),
            });

            if (response.ok) {
                alert("Reactions saved successfully!");

                // Reset summary and results
                summaryTable.innerHTML = "";
                abidResultsContainer.innerHTML = "";

                // Update summary with new reactions
                reactions.forEach(({ cell_number, patient_rxn }) => {
                    if (patient_rxn !== "") {
                        const newRow = document.createElement("tr");
                        newRow.dataset.lotNumber = selectedLotNumber;
                        newRow.dataset.cellNumber = cell_number;
                        newRow.innerHTML = `
                            <td>${selectedLotNumber}</td>
                            <td>${cell_number}</td>
                            <td class="reaction-cell">${patient_rxn}</td>
                            <td><button class="delete-btn">Delete</button></td>
                        `;
                        summaryTable.appendChild(newRow);
                    }
                });

                // Fetch and display ABID results dynamically
                const abidResponse = await fetch("/api/abid");
                if (!abidResponse.ok) throw new Error("Failed to fetch ABID results.");

                const abidResults = await abidResponse.json();
                renderAbidResults(abidResults);
            } else {
                throw new Error("Failed to save reactions.");
            }
        } catch (error) {
            console.error("Error saving reactions or fetching ABID results:", error);
            alert(error.message);
        }
    });

    // Render ABID results
    const renderAbidResults = (results) => {
        const createRowDisplay = (data, label) => {
            if (data.length === 0) {
                return `<div><strong>${label}:</strong> None</div>`;
            }
    
            let row = `<div><strong>${label}:</strong> `;
            row += data.map(item => `<span class="antigen">${item}</span>`).join(", ");
            row += `</div>`;
            return row;
        };
    
        abidResultsContainer.innerHTML = `
            ${createRowDisplay(results.ruled_out, "Ruled Out (RO)")}
            ${createRowDisplay(results.still_to_rule_out, "Still to Rule Out (STRO)")}
            ${createRowDisplay(results.match, "100% Match")}
        `;
    };
    

    summaryTable.addEventListener("click", async (e) => {
        if (e.target.classList.contains("delete-btn")) {
            const row = e.target.closest("tr");
            const lotNumber = row.dataset.lotNumber;
            const cellNumber = row.dataset.cellNumber;
    
            try {
                const response = await fetch(`/api/patient-reactions/${selectedAntigramId}/${cellNumber}`, {
                    method: "DELETE",
                });
    
                if (response.ok) {
                    // Remove the row from the summary table
                    row.remove();
    
                    // Re-fetch and update ABID results
                    const abidResponse = await fetch("/api/abid");
                    if (!abidResponse.ok) throw new Error("Failed to fetch updated ABID results.");
    
                    const abidResults = await abidResponse.json();
                    renderAbidResults(abidResults); // Re-render ABID results
                } else {
                    throw new Error("Failed to delete the reaction.");
                }
            } catch (error) {
                console.error("Error deleting reaction or updating ABID results:", error);
                alert(error.message);
            }
        }
    });
    

});
