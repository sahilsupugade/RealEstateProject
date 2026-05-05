import streamlit as st
import requests

st.set_page_config(page_title="Real Estate Price Prediction", layout="wide")

# ---------------------------
# CUSTOM CSS (from your design)
# ---------------------------
st.markdown("""
<style>
body {
    background-color: #f7f9fc;
}

.hero {
    position: relative;
    text-align: center;
    color: white;
}

.hero img {
    width: 100%;
    height: 220px;
    object-fit: cover;
    filter: brightness(0.6);
}

.hero-text {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}

.card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}

.result-box {
    background: #ecfdf5;
    padding: 25px;
    border-radius: 12px;
    text-align: center;
}

.price {
    font-size: 40px;
    font-weight: bold;
    color: #067a4f;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# HERO BANNER
# ---------------------------
st.markdown("""
<div class="hero">
    <img src="https://images.wallpaperscraft.com/image/single/buildings_night_city_road_168957_1920x1080.jpg">
    <div class="hero-text">
        <h1>Real Estate Property Price Prediction</h1>
        <p>Enter property details and get ML-based price estimate</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# TABS
# ---------------------------
tab1, tab2 = st.tabs(["Price Prediction", "Insights Dashboard"])

# ===========================
# TAB 1
# ===========================
with tab1:

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Property Details")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        carpet_area = st.number_input("Carpet Area", min_value=0)

    with col2:
        bedrooms = st.number_input("Bedrooms", min_value=0)

    with col3:
        bathrooms = st.number_input("Bathrooms", min_value=0)

    with col4:
        balcony = st.number_input("Balcony", min_value=0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        facing = st.selectbox("Facing", [
            "East","West","North-East","North","North-West","South","South-West","South-East"
        ])

    with col2:
        furnish = st.selectbox("Furnish Type", [
            "Semifurnished","Unfurnished","Furnished"
        ])

    with col3:
        prop_type = st.selectbox("Property Type", ["House","Flat"])

    with col4:
        city = st.selectbox("City", ["Mumbai","Thane","Navi Mumbai"])

    col1, col2, col3 = st.columns(3)

    with col1:
        ageing = st.selectbox("Property Age", [
            "Relatively New","Old","New","Relatively Old","Under Construction"
        ])

    with col2:
        floor = st.selectbox("Floor Level", [
            "Low Floor","Mid Floor","High Floor"
        ])

    with col3:
        store_room = st.checkbox("Store Room")

    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- LOCATION
    st.markdown('<div class="card">', unsafe_allow_html=True)
    location = st.selectbox("Select Location", [
        "Kandivali","Thane","Powai","Andheri","Malad","Chembur","Borivali","Bandra","Dadar"
    ])
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- AMENITIES
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Amenities")

    amenities = st.multiselect("Select Amenities", [
        "24/7 Water Supply","Security Personnel","Car Parking","Gymnasium",
        "Swimming Pool","Club House","Park","Lift(s)","Rain Water Harvesting"
    ])
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- PREDICT BUTTON
    if st.button("Predict Price"):

        payload = {
            "carpet_area": carpet_area,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "balcony": balcony,
            "facing": facing,
            "furnish_type": furnish,
            "prop_type": prop_type,
            "city": city,
            "ageing": ageing,
            "floor_category": floor,
            "location_area": location,
            "store_room": store_room,
            "amenities": amenities
        }

        try:
            res = requests.post("http://127.0.0.1:8000/predict", json=payload)
            result = res.json()

            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.markdown("### Predicted Price")
            st.markdown(f'<div class="price">₹ {result["prediction"]:.2f} Cr</div>', unsafe_allow_html=True)

            # WEATHER
            if "weather" in result:
                st.write("### Weather Info")
                st.write(result["weather"])

            st.markdown('</div>', unsafe_allow_html=True)

            # ---------------- NEARBY INSIGHTS ----------------
            if location:

                st.markdown("## 📍 Nearby Infrastructure")

                try:
                    nearby_res = requests.get(f"http://127.0.0.1:8000/nearby/{location}")
                    nearby_data = nearby_res.json()

                    if not nearby_data:
                        st.info("No nearby data found")

                    for direction, categories in nearby_data.items():

                        st.markdown(f"### {direction}")

                        cols = st.columns(3)

                        i = 0
                        for category, info in categories.items():

                            with cols[i % 3]:

                                with st.expander(f"{category} ({info['count']})"):

                                    for place in info["top_places"]:
                                        st.write("•", place)

                            i += 1

                except Exception as e:
                    st.error("Error loading nearby insights")

        except Exception as e:
            st.error("Error connecting to backend")

# ===========================
# TAB 2
# ===========================
with tab2:

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Insights Dashboard")

    st.write("### Location-wise Price Map")
    st.components.v1.iframe("http://127.0.0.1:8000/map", height=450)

    st.write("### Charts")
    st.image("assets/bedrooms.png")
    st.image("assets/wordcloud.png")

    st.markdown('</div>', unsafe_allow_html=True)