const categoryIcons = {
  "Hospital": "local_hospital",
  "School": "school",
  "Metro": "train",
  "Railway": "directions_railway",
  "Mall": "shopping_cart",
  "Bank": "account_balance"
};

const cityAreas = {
  "Mumbai": ["Kandivali", "Powai", "Andheri", "Malad", "Chembur", "Goregaon", "Borivali", "Mulund", "Ghatkopar", "Wadala", "Santacruz", "Bhandup", "Parel", "Worli", "Vikhroli", "Kanjurmarg", "Bandra", "Vile Parle", "Dahisar", "Byculla", "Jogeshwari", "Kurla", "Juhu", "Dadar", "Khar", "Matunga", "Mankhurd", "Girgaon-Malabar", "Mahim", "Sion", "Vidyavihar", "Colaba", "Mazgaon-Chinchpokli", "Girgaon", "Cumbala Hill", "Agripada", "Mandvi-Bhuleshwar", "Mazgaon", "Grant Road", "Sandhurst", "Byculla-Mazgaon", "Churchgate"],

  "Thane": ["Thane", "Kalyan-Dombivli", "Bhiwandi", "Mumbra", "Diva"],

  "Navi Mumbai": ["Navi Mumbai", "Kharghar", "Panvel", "Ulwe", "Nerul", "Kamothe", "Vashi", "Airoli", "Taloja", "Ghansoli", "Roadpali", "Seawoods", "Belapur", "Khanda Colony", "Kalamboli", "Sanpada", "Turbhe"]
};

/* ---------------------------
   Existing logic (preserved + slight UI hooks)
   --------------------------- */

function toggleAmenity(btn) {
  btn.classList.toggle("active");
}

function safeInt(value) {
  const num = parseInt(value, 10);
  return isNaN(num) ? null : num;
}

function getSelectedAmenities() {
  const amenities = [];
  document.querySelectorAll('.amenity-container .amenity-btn').forEach(btn => {
    if (btn.classList.contains("active")) {
      amenities.push(btn.querySelector("span").textContent.trim());
    }
  });
  return amenities;
}

function getFormData() {
  const carpetAreaValue = document.getElementById("carpetarea").value;
  const facingValue = document.getElementById("facing").value;
  const bedroomValue = document.getElementById("bedroom").value;
  const bathroomValue = document.getElementById("bathroom").value;
  const balconyValue = document.getElementById("balcony").value;
  const furnishValue = document.getElementById("furnish_type").value;
  const propValue = document.getElementById("prop_type").value;
  const cityValue = document.getElementById("city").value;
  const ageingValue = document.getElementById("ageing").value;
  const locationValue = document.getElementById("area").value;
  const floorLevelValue = document.getElementById("floor_level").value;

  const selectedAmenities = getSelectedAmenities();

  // Store room checkbox
  const storeRoomValue = document.getElementById("store_room").checked;

  return {
    carpet_area: safeInt(carpetAreaValue),
    facing: facingValue,
    bedrooms: safeInt(bedroomValue),
    bathrooms: safeInt(bathroomValue),
    balcony: safeInt(balconyValue),
    store_room: storeRoomValue,
    furnish_type: furnishValue,
    prop_type: propValue,
    city: cityValue,
    ageing: ageingValue,
    location_area: locationValue,
    floor_category: floorLevelValue,
    amenities: selectedAmenities
  };
}

function getSelectedAmenitiesJSON() {
  const jsonObject = getFormData();
  document.getElementById('jsonOutput').textContent = JSON.stringify(jsonObject, null, 2);
  return jsonObject;
}

async function submitData(event) {
  if (event) event.preventDefault();

  const jsonObject = getFormData();

  // For UX: disable predict button while waiting (if exists)
  const btn = document.getElementById("predictBtn");
  if (btn) { btn.disabled = true; btn.style.opacity = 0.7; }

  try {
    // Keep same endpoint as original
    const response = await fetch("https://my-api-production-0c7b.up.railway.app/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(jsonObject)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log(result);

    // Format and show result in the same UI (green result box)
    const rv = document.getElementById("resultPrice");
    const resultCard = document.getElementById("predictionResult");

    const mean = result.prediction;
    const lower = result.lower;
    const upper = result.upper;

    rv.innerText = `${lower.toFixed(2)} Cr - ${upper.toFixed(2)} Cr`;

    resultCard.classList.remove("hidden");

    // --------------------
    // PROPERTY RECOMMENDATIONS
    // --------------------
    const recContainer = document.getElementById("recommendationContainer");

    if (result.recommendations && result.recommendations.length > 0) {

      recContainer.classList.remove("hidden");

      recContainer.innerHTML = `
      <br><br>
    <h2>Recommended Properties</h2>
    <div id="recGrid"></div>
  `;

      const grid = document.getElementById("recGrid");

      if (!grid) {
        console.error("Grid not found!");
        return;
      }

      result.recommendations.forEach(item => {
        const card = `
      <div class="property-card">
        <div class="card-title">${item.property_name || "Property"}</div>
        <div class="card-price">₹ ${item.price} Cr</div>
        <a href="${item.link}" target="_blank" class="view-btn">
          View Property
        </a>
      </div>
    `;
        grid.innerHTML += card;
      });

    } else {
      recContainer.classList.remove("hidden");
      recContainer.innerHTML = "<p>No recommendations found.</p>";
    }

    document.getElementById("nearbyContainer").innerHTML =
      "<h2 style='color:red'>TEST NEARBY DISPLAY</h2>";
    console.log("AQI RAW:", result.weather.aqi);
    console.log("WEATHER:", result.weather);
    console.log("AQI:", result.aqi);

    // Display Weather Info
    // Gate ONLY on weather (mandatory)
    // Remove old title if already exists
    const oldWeatherTitle = document.getElementById("weatherTitle");
    if (oldWeatherTitle) oldWeatherTitle.remove();

    // Create wrapper (for spacing)
    const weatherTitleWrapper = document.createElement("div");
    weatherTitleWrapper.id = "weatherTitle";

    // Add 2 <br> + title
    weatherTitleWrapper.innerHTML = `
  <br><br><br><br>
  <h2>Weather & Air Quality</h2>
`;

    // Insert ABOVE weather container
    const weatherDiv = document.getElementById("weatherContainer");
    if (weatherDiv) {
      weatherDiv.parentNode.insertBefore(weatherTitleWrapper, weatherDiv);
    }

    if (result.weather) {

      const weatherDiv = document.getElementById("weatherContainer");

      if (!weatherDiv) return;

      // AQI is OPTIONAL
      let aqiHTML = "<br><br>";

      if (result.aqi && result.aqi.aqi_index !== undefined) {
        aqiHTML = `
    <div class="stat">
      <span>AQI</span>
      <strong>
        ${result.aqi.aqi_index}
      </strong>
      <small>${result.aqi.aqi_label}</small>
    </div>
  `;
      }

      weatherDiv.innerHTML = `
    <div class="weather-card">

      <div class="weather-header">
        <span class="material-icons weather-icon">wb_sunny</span>
        <h4>Weather & Air Quality</h4>
      </div>

      <div class="weather-main">
        <div class="weather-temp">
          ${result.weather.temp}°C
        </div>
        <div class="weather-desc">
          ${result.weather.description.toUpperCase()}
        </div>
      </div>

      <div class="weather-stats">
        <div class="stat">
          <span>Feels Like</span>
          <strong>${result.weather.feels_like}°C</strong>
        </div>

        <div class="stat">
          <span>Humidity</span>
          <strong>${result.weather.humidity}%</strong>
        </div>

        <div class="stat">
          <span>Wind</span>
          <strong>${result.weather.wind_speed} m/s</strong>
        </div>

        ${aqiHTML}
      </div>

    </div>
  `;
    }



    if (jsonObject.location_area) {
      loadNearby(jsonObject.location_area);
    } ////////////////////////////////////////////////////////////////////////////////////////////

    // Also update JSON preview
    const jsonBox = document.getElementById('jsonOutput');
    if (jsonBox) {
      jsonBox.textContent = JSON.stringify({
        request: jsonObject,
        response: result
      }, null, 2);
    }

    // Scroll to result smoothly
    resultCard.scrollIntoView({ behavior: "smooth", block: "center" });

  } catch (error) {
    console.error("Error:", error);
  } finally {
    if (btn) { btn.disabled = false; btn.style.opacity = 1; }
  }
}

async function loadNearby(area) {

  const container = document.getElementById("nearbyContainer");
  if (!container || !area) return;

  // Remove old title if exists (avoid duplicates)
  const oldNearbyTitle = document.getElementById("nearbyTitle");
  if (oldNearbyTitle) oldNearbyTitle.remove();

  // Create title wrapper
  const nearbyTitleWrapper = document.createElement("div");
  nearbyTitleWrapper.id = "nearbyTitle";

  nearbyTitleWrapper.innerHTML = `
  <br><br><br><br>
  <h2>Nearby Infrastructure Summary</h2>
`;

  // Insert ABOVE container
  container.parentNode.insertBefore(nearbyTitleWrapper, container);

  container.classList.remove("hidden");

  container.innerHTML = "<p>Loading nearby insights...</p>";

  try {
    const res = await fetch(
      `https://my-api-production-0c7b.up.railway.app/nearby/${encodeURIComponent(area.trim())}`
    );

    const data = await res.json();

    if (!data || Object.keys(data).length === 0) {
      container.innerHTML = "<p>No curated nearby data found.</p>";
      return;
    }

    let html = `
      <div class="section-head">
        <p class="muted">Curated categories only</p>
      </div>
      <div class="direction-container">
    `;

    for (const direction in data) {

      html += `<div class="grid-box">
                <h4>${direction}</h4>`;

      for (const category in data[direction]) {

        const info = data[direction][category];

        html += `
          <div class="category-summary" onclick="toggleCategory(this)">
            <div class="category-header">
              <strong>
  <span class="material-icons cat-icon">
    ${categoryIcons[category] || "place"}
  </span>
  ${category}
</strong>
              <span>${info.count}</span>
            </div>
            <ul class="hidden">
              ${info.top_places.map(p => `<li>${p}</li>`).join("")}
              <li class="view-more">View all</li>
            </ul>
          </div>
        `;
      }

      html += `</div>`;
    }

    html += `</div>`;
    container.innerHTML = html;

  } catch (err) {
    console.error(err);
    container.innerHTML = "<p>Error loading nearby insights.</p>";
  }
}

function toggleCategory(card) {
  const list = card.querySelector("ul");
  list.classList.toggle("hidden");
}

function updateAreas() {
  const city = document.getElementById("city").value;
  const areaSelect = document.getElementById("area");

  // Clear options
  areaSelect.innerHTML = '<option value="">-- Select a location --</option>';

  const areas = cityAreas[city] || [];

  areas.forEach(a => {
    const opt = document.createElement("option");
    opt.value = a;
    opt.textContent = a;
    areaSelect.appendChild(opt);
  });

  // Add Others
  const other = document.createElement("option");
  other.value = "Others";
  other.textContent = "Others";
  areaSelect.appendChild(other);

  // 🔥 IMPORTANT (because you're using Select2)
  if (window.jQuery && $.fn.select2) {
    $('#area').trigger('change'); // refresh UI
  }
}

/* ---------------------------
   UI Glue: Tabs + Select2 + JSON collapse
   --------------------------- */
document.addEventListener("DOMContentLoaded", function () {

  /* ---------------------------
     Select2 init
  --------------------------- */
  if (window.jQuery && $.fn.select2) {
    $('#area').select2({
      placeholder: "Search a location",
      allowClear: true,
      width: 'resolve'
    });
  }

  /* ---------------------------
     Tab switching (SINGLE source)
  --------------------------- */
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", function () {

      document.querySelectorAll(".tab-btn")
        .forEach(b => b.classList.remove("active-tab"));
      this.classList.add("active-tab");

      document.querySelectorAll(".tab-content")
        .forEach(t => t.classList.remove("active-tab-content"));

      const target = this.dataset.target;
      const activeTab = document.getElementById(target);
      if (activeTab) activeTab.classList.add("active-tab-content");
    });
  });
  // City → Area filtering
  const citySelect = document.getElementById("city");

  if (citySelect) {
    citySelect.addEventListener("change", updateAreas);
  }

  // Run once on load (default Mumbai)
  updateAreas();
});
