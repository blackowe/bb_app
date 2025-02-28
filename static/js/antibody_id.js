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
    const fetchAndRenderPatientReactions = async () => {
        try {
            const response = await fetch("/api/patient-reactions");
            if (!response.ok) throw new Error("Failed to fetch patient reactions.");
    
            const data = await response.json();
            const reactions = data.patient_reactions || [];
    
            summaryTable.innerHTML = ""; // Clear existing rows
    
            if (reactions.length === 0) {
                summaryTable.innerHTML = `<tr><td colspan="4">No patient reactions recorded.</td></tr>`;
                return;
            }
    
            reactions.forEach(({ lot_number, cell_number, patient_reaction }) => {
                const row = document.createElement("tr");
                row.dataset.cellNumber = cell_number;
                row.dataset.lotNumber = lot_number;
    
                row.innerHTML = `
                    <td>${lot_number}</td>
                    <td>${cell_number}</td>
                    <td>${patient_reaction}</td>
                    <td><button class="delete-btn">❌</button></td>
                `;
    
                summaryTable.appendChild(row);
            });
    
        } catch (error) {
            console.error("❌ Error fetching patient reactions:", error);
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
            
            console.log("Selected Antigram ID:", selectedAntigramId);
    
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
    

    // Save all reactions for the selected antigram
    saveAllReactionsBtn.addEventListener("click", async () => {
        try {
            if (!selectedAntigramId) {
                alert("Error: No antigram selected.");
                return;
            }
    
            const reactions = Array.from(
                reactionFormContainer.querySelectorAll("input[data-cell-number]")
            )
                .map(input => ({
                    cell_number: parseInt(input.dataset.cellNumber),
                    patient_rxn: input.value.trim(),
                }))
                .filter(r => r.patient_rxn === "+" || r.patient_rxn === "0");
    
            if (reactions.length === 0) {
                alert("No valid reactions to save.");
                return;
            }
    
            const response = await fetch("/api/patient-reactions", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ antigram_id: selectedAntigramId, reactions }),
            });
    
            // ✅ **Fix: Check response status before throwing an error**
            if (!response.ok) {
                const errorMessage = await response.text();
                throw new Error(`Failed to save reactions: ${errorMessage}`);
            }
    
            console.log("✅ Reactions saved successfully!");
    
            // ✅ **Fix: Ensure ABID results are re-fetched after saving reactions**
            await fetchAndRenderPatientReactions();
            await fetchAndRenderAbidResults();
    
        } catch (error) {
            console.error("❌ Error saving reactions:", error);
            alert("Error saving reactions: " + error.message);
        }
    });
    
    
    

    summaryTable.addEventListener("click", async (e) => {
        if (e.target.classList.contains("delete-btn")) {
            const row = e.target.closest("tr");
            const cellNumber = row.dataset.cellNumber;
            const lotNumber = row.dataset.lotNumber;
    
            try {
                const response = await fetch(`/api/patient-reactions/${selectedAntigramId}/${cellNumber}`, {
                    method: "DELETE",
                });
    
                if (response.ok) {
                    row.remove();
                    fetchAndRenderPatientReactions();  // Update summary table
                    fetchAndRenderAbidResults(); // Update ABID results
                } else {
                    throw new Error("Failed to delete the reaction.");
                }
            } catch (error) {
                console.error("❌ Error deleting reaction:", error);
                alert("Failed to delete reaction.");
            }
        }
    });
    

    // Render ABID results
    const renderAbidResults = (results) => {
        const createRowDisplay = (data, label) => {
            if (!data || data.length === 0) {
                return `<div><strong>${label}:</strong> None</div>`;
            }
    
            let row = `<div><strong>${label}:</strong> `;
            row += data.map(item => `<span class="antigen">${item}</span>`).join(", ");
            row += `</div>`;
            return row;
        };
    
        // Properly format ruled-out details (Lot Number & Cell Number)
        const ruledOutDetailsDisplay = Object.entries(results.ruled_out_details || {})
            .map(([antigen, cells]) => 
                `<div><strong>${antigen}:</strong> ruled out by cells: ${cells.map(cell => `Lot ${cell.lot_number}, Cell ${cell.cell_number}`).join(", ")}</div>`
            ).join("");
    
        abidResultsContainer.innerHTML = `
            ${createRowDisplay(results.ruled_out, "Ruled Out (RO)")}
            ${createRowDisplay(results.still_to_rule_out, "Still to Rule Out (STRO)")}
            ${createRowDisplay(results.match, "100% Match")}
            <div><strong>Ruled Out Details:</strong></div>
            <div id="ruled-out-details">${ruledOutDetailsDisplay || "None"}</div>
        `;
    };

    const fetchAndRenderAbidResults = async () => {
        try {
            console.log("✅ Fetching ABID results...");
            const response = await fetch("/api/abid");
            if (!response.ok) throw new Error("Failed to fetch ABID results.");
    
            const abidResults = await response.json();
            console.log("✅ ABID Results:", abidResults);
            
            renderAbidResults(abidResults);  // ✅ **Ensure fresh results are rendered**
        } catch (error) {
            console.error("❌ Error fetching ABID results:", error);
            alert("Error fetching ABID results: " + error.message);
        }
    };
    
    
});
