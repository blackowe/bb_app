document.addEventListener("DOMContentLoaded", function () {
  loadTemplates();

  document.getElementById("confirm-template-btn").addEventListener("click", loadTemplateDetails);
  document.getElementById("save-antigram-btn").addEventListener("click", saveAntigram);
});

function loadTemplates() {
  fetch("/api/antigram-templates")
      .then(response => response.json())
      .then(data => {
          let dropdown = document.getElementById("templateSelect");
          dropdown.innerHTML = "<option value=''>-- Select a Template --</option>";
          data.forEach(template => {
              let option = document.createElement("option");
              option.value = template.id;
              option.textContent = template.name;
              dropdown.appendChild(option);
          });
      })
      .catch(error => console.error("Error loading templates:", error));
}

function loadTemplateDetails() {
  let templateId = document.getElementById("templateSelect").value;
  if (!templateId) {
      alert("Please select a template.");
      return;
  }

  fetch(`/api/antigram-templates/${templateId}`)
      .then(response => response.json())
      .then(template => {
          document.getElementById("lotNumber").value = template.lot_number || "";
          document.getElementById("expirationDate").value = template.expiration_date || "";
          generateAntigramTable(template);
      })
      .catch(error => {
          console.error("Error fetching template details:", error);
          alert("Failed to fetch template details.");
      });
}

function generateAntigramTable(template) {
  let table = document.getElementById("antigram-table");
  let header = document.getElementById("antigram-header");
  let body = document.getElementById("antigram-body");

  // ✅ Clear previous data
  header.innerHTML = "";
  body.innerHTML = "";

  // ✅ Create header row with antigen names
  let headerRow = "<tr><th>Cell #</th>";
  template.antigen_order.forEach(antigen => {
      headerRow += `<th>${antigen}</th>`;
  });
  headerRow += "</tr>";
  header.innerHTML = headerRow;

  // ✅ Populate body with input fields
  let bodyHtml = "";
  for (let i = 1; i <= template.cell_count; i++) {
      bodyHtml += `<tr><td>${i}</td>`; // Cell number column

      template.antigen_order.forEach(antigen => {
          bodyHtml += `
              <td>
                  <input 
                      type="text" 
                      class="reaction-input" 
                      data-cell="${i}" 
                      data-antigen="${antigen}" 
                      maxlength="1" 
                      placeholder="+" 
                  />
              </td>`;
      });

      bodyHtml += "</tr>";
  }
  body.innerHTML = bodyHtml;

  // ✅ Debugging: Log the generated HTML
  console.log("Generated Table Body:", body.innerHTML);

  // ✅ Ensure the "Save Antigram" button is visible
  document.getElementById("save-antigram-btn").style.display = "block";
}



function saveAntigram() {
  let templateId = document.getElementById("templateSelect").value;
  let lotNumber = document.getElementById("lotNumber").value;
  let expirationDate = document.getElementById("expirationDate").value;

  if (!templateId || !lotNumber || !expirationDate) {
      alert("Please complete all fields before saving.");
      return;
  }

  let cells = [];
  let allFieldsFilled = true; // ✅ Flag to check if all reaction inputs are filled

  document.querySelectorAll(".reaction-input").forEach(input => {
      let cellNumber = input.getAttribute("data-cell");
      let antigen = input.getAttribute("data-antigen");
      let reaction = input.value.trim();

      if (!cells[cellNumber - 1]) {
          cells[cellNumber - 1] = { cellNumber: parseInt(cellNumber), reactions: {} };
      }

      // ✅ Fill in missing reactions with "0" instead of skipping them
      cells[cellNumber - 1].reactions[antigen] = reaction || "0";

      // ✅ If any field is empty, set the flag to false
      if (reaction === "") {
          allFieldsFilled = false;
      }
  });

  // ✅ Ensure the reaction matrix is correctly filled
  if (!allFieldsFilled) {
      alert("Please complete all reaction inputs before saving.");
      return;
  }

  let payload = {
      templateId: templateId,
      lotNumber: lotNumber,
      expirationDate: expirationDate,
      cells: cells.filter(Boolean) // ✅ Remove empty indices
  };

  fetch("/api/antigrams", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
  })
  .then(response => response.json())
  .then(data => {
      if (data.error) {
          alert("Error saving antigram: " + data.error);
      } else {
          alert("Antigram saved successfully!");
      }
  })
  .catch(error => {
      console.error("Error creating antigram:", error);
      alert("Failed to save antigram.");
  });
}
