// Event listener for the "Load Antigram" button
document.getElementById("load-antigram-button").addEventListener("click", async function () {
  const lotNumber = document.getElementById("lot-number-dropdown").value;

  if (!lotNumber) {
      console.log("No lot number selected.");
      alert("Please select a lot number.");
      return;
  }

  try {
      console.log("Fetching antigram for lot number:", lotNumber);

      // Fetch antigram data from the backend
      const response = await fetch(`/api/antigrams/${lotNumber}`);

      if (!response.ok) {
          console.error("Failed to fetch antigram:", response.statusText);
          alert("Failed to load antigram. Please try again.");
          return;
      }

      const data = await response.json();
      console.log("Fetched antigram data:", data);

      if (!data.cells || data.cells.length === 0) {
          console.error("No cells found for the selected antigram.");
          alert("No cells found for the selected antigram.");
          return;
      }

      // Populate the table with antigram data
      const tbody = document.getElementById("antigen-input-body");
      tbody.innerHTML = ""; // Clear previous data

      data.cells.forEach(cell => {
          const row = document.createElement("tr");
          row.innerHTML = `
              <td>${cell.cell_number}</td>
              ${Object.keys(cell.reactions).map(antigen => `<td>${cell.reactions[antigen] || "-"}</td>`).join("")}
              <td><input type="text" name="patient_reaction_${cell.cell_number}" placeholder="0 or +"></td>
          `;
          tbody.appendChild(row);
      });

  } catch (error) {
      console.error("Error fetching antigram:", error);
      alert("An error occurred while loading the antigram. Please check the console for more details.");
  }
});

// Event listener for the "ABID" button
document.getElementById("abid-button").addEventListener("click", async function () {
  const lotNumber = document.getElementById("lot-number-dropdown").value;
  const patientReactions = {};

  if (!lotNumber) {
      alert("Please select a lot number before performing ABID.");
      return;
  }

  // Collect patient reactions
  document.querySelectorAll("[name^='patient_reaction_']").forEach(input => {
      const cellNumber = input.name.split("_")[2];
      patientReactions[cellNumber] = input.value.trim(); // Ensure no extra spaces
  });

  console.log("Patient Reactions Submitted:", patientReactions);

  try {
      // Send patient reactions and lot number to the backend
      const response = await fetch("/antibody_id", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ lot_number: lotNumber, patient_reactions: patientReactions })
      });

      if (!response.ok) {
          console.error("Failed to perform ABID:", response.statusText);
          alert("Failed to perform ABID. Please try again.");
          return;
      }

      const results = await response.json();
      console.log("ABID Results:", results);

      // Display results
      document.getElementById("ruled-out-antigens").innerText = results.ruled_out_antigens.join(", ");
      document.getElementById("possible-antibodies").innerText = results.possible_antibodies.join(", ");

  } catch (error) {
      console.error("Error during ABID:", error);
      alert("An error occurred while performing ABID. Please check the console for more details.");
  }
});

