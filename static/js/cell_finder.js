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
      const response = await fetch("/cell_finder", {
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

      // Populate results table
      const resultsBody = document.getElementById("results-body");
      resultsBody.innerHTML = ""; // Clear previous results

      if (results.length > 0) {
          results.forEach(result => {
              const row = document.createElement("tr");

              // Create table cells dynamically
              row.innerHTML = `
                  <td>${result.antigram.lot_number}</td>
                  <td>${result.antigram.expiration_date}</td>
                  <td>${result.cell.cell_number}</td>
                  ${["D", "C", "c", "E", "e", "K", "Fya", "Fyb", "Jka", "Jkb"]
                      .map(antigen => `<td>${result.cell.reactions[antigen] || "-"}</td>`)
                      .join("")}
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
