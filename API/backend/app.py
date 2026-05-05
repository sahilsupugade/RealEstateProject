from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, computed_field
from typing import List, Optional, Literal
import pandas as pd
import numpy as np
import pickle
import ast
import requests
import plotly.express as px
import os
from dotenv import load_dotenv
import joblib


load_dotenv()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------
# LOAD FILES

coords_df = pd.read_csv(os.path.join(BASE_DIR, "OpenStreet.csv"))
direction_df = pd.read_csv(os.path.join(BASE_DIR, "nearby_area_direction_level.csv"))

coords_df["geo_place"] = coords_df["geo_place"].str.strip().str.lower()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_coordinates(location_area: str):
    row = coords_df[coords_df["geo_place"] == location_area.strip().lower()]
    if row.empty:
        return None, None
    return float(row.iloc[0]["latitude"]), float(row.iloc[0]["longitude"])

def get_aqi(lat: float, lon: float):
    url = "http://api.openweathermap.org/data/2.5/air_pollution"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY
    }

    r = requests.get(url, params=params, timeout=5)
    r.raise_for_status()
    data = r.json()

    aqi_index = data["list"][0]["main"]["aqi"]

    aqi_map = {
        1: "Good",
        2: "Fair",
        3: "Moderate",
        4: "Poor",
        5: "Very Poor"
    }

    return {
        "aqi_index": aqi_index,
        "aqi_label": aqi_map.get(aqi_index, "Unknown")
    }

def get_weather(lat: float, lon: float):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    r = requests.get(url, params=params, timeout=5)
    r.raise_for_status()
    data = r.json()

    return {
        "temp": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "description": data["weather"][0]["description"],
        "wind_speed": data["wind"]["speed"],
    }

# INPUT 

class Input(BaseModel):
    bedrooms: int = Field(..., gt=0)
    bathrooms: int = Field(..., gt=0)
    carpet_area: int = Field(..., gt=0)
    balcony: int = Field(..., ge=0)
    store_room: bool

    facing: Optional[
        Literal["East","West","North-East","North","North-West","South","South-West","South-East"]
    ] = "Missing"

    furnish_type: Literal["Semifurnished","Unfurnished","Furnished"]
    prop_type: Literal["Flat","House"]
    city: Literal["Mumbai","Thane","Navi Mumbai"]
    ageing: Literal[
        "Relatively New","Old","New","Relatively Old","Undefined","Under Construction"
    ]
    location_area: str
    floor_category: Literal["Low Floor","Mid Floor","High Floor"]
    amenities: List[str]

    @computed_field(return_type=str)
    def luxury_category(self) -> str:
        feature_points = {
            '24/7 Power Backup': 10,
            'Power Back-up': 10,
            '24/7 Water Supply': 10,
            'Security Personnel': 9,
            'Car Parking': 9,
            'Visitor Parking': 8,
            'Fire Fighting Systems': 8,
            'Security / Fire Alarm': 8,
            'Centrally Air Conditioned': 9,
            'Gymnasium': 8,
            'Fitness Centre / GYM': 8,
            'Swimming Pool': 8,
            'Club House': 7,
            'Club house / Community Center': 7,
            'Park': 7,
            "Children's Play Area": 7,
            'Private Garden / Terrace': 8,
            'Low Density Society': 8,
            'Recently Renovated': 7,
            'Internet/wi-fi connectivity': 7,
            'Lift(s)': 8,
            'Rain Water Harvesting': 6,
            'Piped-gas': 6,
            'Water purifier': 6,
            'Maintenance Staff': 6,
            'Waste Disposal': 6,
            'Water Storage': 6,
            'Water softening plant': 6,
            'Spacious Interiors': 7,
            'Natural Light': 6,
            'Airy Rooms': 6,
            'High Ceiling Height': 6,
            'False Ceiling Lighting': 4,
            'Separate entry for servant room': 4,
            'Intercom Facility': 5,
            'InterCom': 5,
            'Bank Attached Property': 4,
            'Shopping Centre': 5,
            'Feng Shui / Vaastu Compliant': 4,
            'No open drainage around': 5
        }

        score = sum(feature_points.get(a, 0) for a in self.amenities)

        if score < 100:
            return "Low"
        elif score < 300:
            return "Medium"
        return "High"

# PREDICTION

MODEL_PATH = os.path.join(BASE_DIR, "rfpipeline.pkl")

try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"Model loading failed: {e}")


@app.post("/predict")
def predict(data: Input):

    input_df = pd.DataFrame([{
        "carpet_area": data.carpet_area,
        "facing": data.facing,
        "bedrooms": data.bedrooms,
        "bathrooms": data.bathrooms,
        "balcony": data.balcony,
        "furnish_type": data.furnish_type,
        "prop_type": data.prop_type,
        "city": data.city,
        "Store Room": data.store_room,
        "ageing": data.ageing,
        "location_area": data.location_area,
        "luxury_category": data.luxury_category,
        "floor_category": data.floor_category,
    }])

    prediction = model.predict(input_df)
    final_price = float(np.expm1(prediction[0]))
    lower = final_price * 0.9
    upper = final_price * 1.1

    lat, lon = get_coordinates(data.location_area)
    weather = None
    aqi = None

    if lat and lon and OPENWEATHER_API_KEY:
        try:
            weather = get_weather(lat, lon)
        except Exception as e:
            print("Weather fetch failed:", e)

        try:
            aqi = get_aqi(lat, lon)
        except Exception as e:
            print("AQI fetch failed:", e)

    return {
    "prediction": final_price,
    "lower": lower,
    "upper": upper,
    "weather": weather,
    "aqi": aqi
    }

@app.get("/nearby/{area}")
def get_nearby(area: str):

    filtered = direction_df[
        direction_df["location_area"].str.strip().str.lower()
        == area.strip().lower()
    ].copy()

    if filtered.empty:
        return {}

    filtered["places"] = filtered["places"].apply(ast.literal_eval)

    IMPORTANT_CATEGORIES = [
        "Hospital",
        "School",
        "Metro",
        "Railway",
        "Mall",
        "Bank",
        "Clinic",
        "Market"
    ]

    result = {}

    for _, row in filtered.iterrows():

        direction = row["direction"]
        category = row["category"]

        if category not in IMPORTANT_CATEGORIES:
            continue

        result.setdefault(direction, {})
        result[direction].setdefault(category, [])

        # extend all places into one list
        result[direction][category].extend(row["places"])

    # Now clean + summarize
    final_output = {}

    for direction, categories in result.items():

        final_output[direction] = {}

        for category, places in categories.items():

            unique_places = list(set([p.strip() for p in places]))

            final_output[direction][category] = {
                "count": len(unique_places),
                "top_places": unique_places[:5],
                "all_places": unique_places
            }

    return final_output


# MAP

@app.get("/map", response_class=HTMLResponse)
def show_map():
    df = pd.read_csv(os.path.join(BASE_DIR, "imputed_data.csv"))
    geo_df = pd.read_csv(os.path.join(BASE_DIR, "OpenStreet.csv"))

    df["geo_place"] = (
        df["location_area"].str.strip() + " " +
        df["direction"].str.strip()
    )

    df["geo_place"] = df["geo_place"].fillna(df["location_area"])

    def normalize_place(col):
        return (
            col.str.lower()
               .str.replace(r"\s+", " ", regex=True)
               .str.strip()
        )

    df["geo_place_norm"] = normalize_place(df["geo_place"])
    geo_df["geo_place_norm"] = normalize_place(geo_df["geo_place"])

    merged_df = df.merge(
        geo_df.drop(columns=["geo_place"]),
        on="geo_place_norm",
        how="left"
    )

    merged_df["location_direction"] = np.where(
        merged_df["direction"].notna(),
        merged_df["location_area"] + " - " + merged_df["direction"],
        merged_df["location_area"]
    )

    grouped_df = (
        merged_df
        .dropna(subset=["latitude", "longitude"])
        .groupby("location_direction", as_index=False)
        .agg(
            latitude=("latitude", "mean"),
            longitude=("longitude", "mean"),
            avg_price_per_sqft=("price_per_sqft", "mean"),
            avg_carpet_area=("carpet_area", "mean"),
            avg_price=("price", "median"),
            property_count=("price", "count")
        )
    )

    plot_grouped_df = grouped_df.dropna(
        subset=["latitude", "longitude", "avg_carpet_area"]
    )

    fig = px.scatter_map(
        plot_grouped_df,
        lat="latitude",
        lon="longitude",
        color="avg_price_per_sqft",
        size="avg_carpet_area",
        color_continuous_scale=px.colors.cyclical.IceFire,
        size_max=15,
        zoom=10,
        hover_name="location_direction",
        hover_data={
            "avg_price_per_sqft": ":,.0f",
            "avg_carpet_area": ":,.0f"
        },
        center={"lat": 19.09, "lon": 72.92}
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0)
    )

    return fig.to_html(full_html=False)