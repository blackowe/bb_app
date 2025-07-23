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
    
            reactions.forEach(({ lot_number, cell_number, patient_reaction, antigram_id }) => {
                const row = document.createElement("tr");
                row.dataset.cellNumber = cell_number;
                row.dataset.lotNumber = lot_number;
                row.dataset.antigramId = antigram_id;  // Store antigram_id in the row
    
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
            console.log("Selected Lot Number:", selectedLotNumber);
    
            try {
                const response = await fetch(`/api/antigrams/${selectedAntigramId}`);
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error("API Error Response:", errorText);
                    alert("Failed to fetch antigram details.");
                    return;
                }
    
                const antigram = await response.json();
                console.log("Antigram Details:", antigram);
                
                // Clear previous form and show the container
                reactionFormContainer.style.display = "block";
                const cardBody = reactionFormContainer.querySelector(".card-body");
                cardBody.innerHTML = "";
                
                // Add header
                const header = document.createElement("h5");
                header.textContent = `Enter Patient Reactions for Lot ${selectedLotNumber}`;
                header.style.marginBottom = "15px";
                cardBody.appendChild(header);
                
                // Check if cells data exists
                if (!antigram.cells || !Array.isArray(antigram.cells) || antigram.cells.length === 0) {
                    console.error("No cells data found in antigram:", antigram);
                    const errorMsg = document.createElement("p");
                    errorMsg.className = "text-danger";
                    errorMsg.textContent = "No cell data found for this antigram.";
                    cardBody.appendChild(errorMsg);
                    return;
                }
                
                console.log("Number of cells found:", antigram.cells.length);
                
                // Create form for each cell
                antigram.cells.forEach((cell, index) => {
                    console.log(`Processing cell ${index}:`, cell);
                    
                    const formRow = document.createElement("div");
                    formRow.classList.add("form-row");
                    formRow.style.cssText = "display: flex; align-items: center; gap: 10px; margin-bottom: 10px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; background-color: #f8f9fa;";
                    
                    const cellLabel = document.createElement("span");
                    cellLabel.textContent = `Cell ${cell.cell_number}:`;
                    cellLabel.style.fontWeight = "bold";
                    cellLabel.style.minWidth = "80px";
                    
                    const input = document.createElement("input");
                    input.type = "text";
                    input.id = `patient-rxn-${cell.cell_number}`;
                    input.dataset.cellNumber = cell.cell_number;
                    input.placeholder = "+ or 0 (optional)";
                    input.style.cssText = "width: 120px; padding: 5px; border: 1px solid #ccc; border-radius: 3px; text-align: center;";
                    input.maxLength = "1";
                    
                    formRow.appendChild(cellLabel);
                    formRow.appendChild(input);
                    cardBody.appendChild(formRow);
                });
    
                saveAllReactionsBtn.style.display = "block";
                console.log("✅ Cell form created successfully");
                
            } catch (error) {
                console.error("❌ Error fetching antigram details:", error);
                alert("Error fetching antigram details: " + error.message);
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
                    cell_number: input.dataset.cellNumber,  // Keep as string, don't parse as integer
                    reaction: input.value.trim(),
                }))
                .filter(r => r.reaction === "+" || r.reaction === "0");
    
            if (reactions.length === 0) {
                alert("No valid reactions to save.");
                return;
            }
    
            console.log("Saving reactions:", reactions);
    
            // Send each reaction individually
            for (const reactionData of reactions) {
                const response = await fetch("/api/patient-reactions", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ 
                        antigram_id: selectedAntigramId, 
                        cell_number: reactionData.cell_number,
                        reaction: reactionData.reaction
                    }),
                });
    
                if (!response.ok) {
                    const errorMessage = await response.text();
                    throw new Error(`Failed to save reaction for cell ${reactionData.cell_number}: ${errorMessage}`);
                }
            }
    
            console.log("✅ All reactions saved successfully!");
    
            //  Ensure ABID results are re-fetched after saving reactions**
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
            const antigramId = row.dataset.antigramId;  // Get antigram_id from the row
    
            if (!antigramId) {
                console.error("No antigram ID found for this reaction");
                return;
            }
    
            try {
                const response = await fetch(`/api/patient-reactions/${antigramId}/${cellNumber}`, {
                    method: "DELETE",
                });
    
                if (!response.ok) {
                    throw new Error("Failed to delete the reaction.");
                }

                const abidResponse = await response.json();
                
                // Remove the row from the table
                row.remove();
                
                // Update the ABID results display
                renderAbidResults(abidResponse);
                
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
                return `<div class="result-row"><strong>${label}:</strong> None</div>`;
            }
    
            let row = `<div class="result-row"><strong>${label}:</strong> `;
            row += data.map(item => `<span class="antigen">${item}</span>`).join(", ");
            row += `</div>`;
            return row;
        };
    
        // Group antigens by rule-out type
        const groupedRuleOuts = {
            single: [],
            homozygous: [],
            heterozygous: []
        };

        Object.entries(results.ruled_out_details || {}).forEach(([antigen, cells]) => {
            // First check for homozygous rule-outs
            const homozygousCells = cells.filter(cell => cell.rule_type === 'homozygous');
            if (homozygousCells.length > 0) {
                // If we have a homozygous rule-out, use that
                groupedRuleOuts.homozygous.push({
                    antigen,
                    cell: homozygousCells[0].cell_number,
                    lot: homozygousCells[0].lot_number
                });
                return; // Skip to next antigen
            }

            // Then check for single rule-outs
            const singleCells = cells.filter(cell => cell.rule_type === 'single');
            if (singleCells.length > 0) {
                groupedRuleOuts.single.push({
                    antigen,
                    cell: singleCells[0].cell_number,
                    lot: singleCells[0].lot_number
                });
                return; // Skip to next antigen
            }

            // Finally check for heterozygous rule-outs
            const heterozygousCells = cells.filter(cell => cell.rule_type === 'heterozygous');
            if (heterozygousCells.length >= 3) {
                groupedRuleOuts.heterozygous.push({
                    antigen,
                    cells: heterozygousCells.slice(0, 3).map(cell => ({
                        number: cell.cell_number,
                        lot: cell.lot_number
                    }))
                });
            }
        });

        // Create the HTML for each rule-out type section
        const createRuleOutSection = (title, antigens, template) => {
            if (antigens.length === 0) return '';
            
            const antigenList = antigens.map(template).join('');
            return `
                <div class="rule-out-section">
                    <h4>${title}</h4>
                    ${antigenList}
                </div>
            `;
        };

        const singleRuleOuts = createRuleOutSection(
            'Single Antigen Rule-Outs',
            groupedRuleOuts.single,
            item => `<div class="rule-out-item">
                <strong>${item.antigen}:</strong> 
                <span class="cell-info">
                    <span class="lot-number">${item.lot}</span>
                    Cell ${item.cell}
                </span>
            </div>`
        );

        const homoRuleOuts = createRuleOutSection(
            'Homozygous Rule-Outs',
            groupedRuleOuts.homozygous,
            item => `<div class="rule-out-item">
                <strong>${item.antigen}:</strong> 
                <span class="cell-info">
                    <span class="lot-number">${item.lot}</span>
                    Cell ${item.cell}
                </span>
            </div>`
        );

        const heteroRuleOuts = createRuleOutSection(
            'Heterozygous Rule-Outs',
            groupedRuleOuts.heterozygous,
            item => `<div class="rule-out-item">
                <strong>${item.antigen}:</strong> 
                <span class="cell-info">
                    ${item.cells.map(cell => `
                        <span class="lot-number">${cell.lot}</span>
                        Cell ${cell.number}
                    `).join(", ")}
                </span>
            </div>`
        );

        // Add some CSS styles
        const styles = `
            <style>
                .result-row {
                    margin-bottom: 15px;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                }
                .rule-out-section {
                    margin: 15px 0;
                    padding: 15px;
                    background-color: #fff;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                }
                .rule-out-section h4 {
                    margin-top: 0;
                    color: #495057;
                    border-bottom: 2px solid #e9ecef;
                    padding-bottom: 5px;
                }
                .rule-out-item {
                    margin: 8px 0;
                    padding: 5px 0;
                    display: flex;
                    align-items: baseline;
                }
                .rule-out-item strong {
                    min-width: 45px;
                    margin-right: 10px;
                }
                .cell-info {
                    color: #666;
                }
                .lot-number {
                    color: #0066cc;
                    margin-right: 8px;
                    font-family: monospace;
                }
                .antigen {
                    background-color: #e9ecef;
                    padding: 2px 6px;
                    border-radius: 3px;
                    margin: 0 2px;
                }
            </style>
        `;
    
        abidResultsContainer.innerHTML = `
            ${styles}
            ${createRowDisplay(results.ruled_out, "Ruled Out (RO)")}
            ${createRowDisplay(results.stro, "Still to Rule Out (STRO)")}
            ${createRowDisplay(results.matches, "100% Match")}
            <div class="rule-out-details">
                <h3>Ruled Out Details</h3>
                ${singleRuleOuts}
                ${homoRuleOuts}
                ${heteroRuleOuts}
            </div>
        `;
    };

    const fetchAndRenderAbidResults = async () => {
        try {
            console.log("✅ Fetching ABID results...");
            const response = await fetch("/api/abid");
            if (!response.ok) throw new Error("Failed to fetch ABID results.");
    
            const abidResults = await response.json();
            console.log("✅ ABID Results:", abidResults);
            
            renderAbidResults(abidResults);  // *Ensure fresh results are rendered**
        } catch (error) {
            console.error("❌ Error fetching ABID results:", error);
            alert("Error fetching ABID results: " + error.message);
        }
    };
    
    
});
