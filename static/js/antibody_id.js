document.addEventListener("DOMContentLoaded", () => {
    const searchBar = document.getElementById("search-bar");
    const searchBtn = document.getElementById("search-btn");
    const antigramTable = document.getElementById("antigram-table").querySelector("tbody");
    const reactionFormContainer = document.getElementById("reaction-form-container");
    const saveAllReactionsBtn = document.getElementById("save-all-reactions-btn");
    const summaryTable = document.getElementById("summary-table").querySelector("tbody");
    const abidResultsContainer = document.getElementById("abid-results");

    let selectedAntigramId = null;
    let selectedLotNumber = null;

    // Function to fetch and render ABID results
    const fetchAndRenderAbidResults = async () => {
        try {
            const abidResponse = await fetch("/api/abid");
            if (!abidResponse.ok) throw new Error("Failed to fetch ABID results.");
            const abidResults = await abidResponse.json();
            renderAbidResults(abidResults);
        } catch (error) {
            console.error("Error fetching ABID results:", error);
        }
    };

    // Search for antigrams (no reset of summary table)
    searchBtn.addEventListener("click", async () => {
        const searchQuery = searchBar.value.trim();
        if (!searchQuery) {
            alert("Please enter a lot number to search.");
            return;
        }

        try {
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
        } catch (error) {
            console.error("Error fetching antigrams:", error);
        }
    });

    // Handle antigram selection
    antigramTable.addEventListener("click", async (e) => {
        if (e.target.classList.contains("select-btn")) {
            selectedAntigramId = e.target.dataset.antigramId;
            selectedLotNumber = e.target.dataset.lotNumber;

            try {
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
            } catch (error) {
                console.error("Error fetching antigram details:", error);
            }
        }
    });

    // Save patient reactions and update the summary (append or update rows)
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
                // Append new reactions to the summary
                reactions.forEach(({ cell_number, patient_rxn }) => {
                    if (patient_rxn !== "") {
                        const existingRow = summaryTable.querySelector(
                            `tr[data-cell-number="${cell_number}"][data-lot-number="${selectedLotNumber}"]`
                        );

                        if (existingRow) {
                            existingRow.querySelector(".reaction-cell").textContent = patient_rxn;
                        } else {
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
                    }
                });

                // Re-fetch and update ABID results
                fetchAndRenderAbidResults();
            } else {
                throw new Error("Failed to save reactions.");
            }
        } catch (error) {
            console.error("Error saving reactions:", error);
            alert(error.message);
        }
    });

    // Delete reactions from the summary
    summaryTable.addEventListener("click", async (e) => {
        if (e.target.classList.contains("delete-btn")) {
            const row = e.target.closest("tr");
            const cellNumber = row.dataset.cellNumber;

            try {
                const response = await fetch(`/api/patient-reactions/${selectedAntigramId}/${cellNumber}`, {
                    method: "DELETE",
                });

                if (response.ok) {
                    row.remove();

                    // Re-fetch and update ABID results
                    fetchAndRenderAbidResults();
                } else {
                    throw new Error("Failed to delete the reaction.");
                }
            } catch (error) {
                console.error("Error deleting reaction or updating ABID results:", error);
                alert(error.message);
            }
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
});
