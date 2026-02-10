import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Set page configuration
st.set_page_config(page_title="Airbnb Data Viewer", layout="wide")

# Title
st.title("🌍 European Airbnb Data Viewer")

# Sidebar for navigation
st.sidebar.header("Select Location")

# Data Directory
DATA_DIR = "data"

@st.cache_data
def get_locations(base_dir):
    """
    Returns a dictionary of {Country: [Cities]} found in the base_dir.
    """
    locations = {}
    if not os.path.exists(base_dir):
        return locations
        
    countries = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    for country in sorted(countries):
        country_path = os.path.join(base_dir, country)
        cities = [d for d in os.listdir(country_path) if os.path.isdir(os.path.join(country_path, d))]
        if cities:
            locations[country] = sorted(cities)
    return locations

locations = get_locations(DATA_DIR)

if not locations:
    st.error("No data found in 'data/' directory. Please ensure the data download step was completed.")
    st.stop()

# Country Selection
selected_country = st.sidebar.selectbox("Choose a Country", list(locations.keys()))

# City Selection
cities = locations[selected_country]
selected_city = st.sidebar.selectbox("Choose a City", cities)

# Load Data function
@st.cache_data
def load_data(country, city):
    file_path = os.path.join(DATA_DIR, country, city, "listings.csv.gz")
    if not os.path.exists(file_path):
        return None
    
    try:
        df = pd.read_csv(file_path, compression='gzip')
        # Basic preprocessing
        if 'price' in df.columns:
            # Force conversion to numeric, coercing errors to NaN
            # First clean any potential string symbols just in case, though file seems to have raw numbers sometimes
            # Actually, standard lists.csv.gz usually has $ and , but the listings.csv (visualisations) has raw numbers?
            # Let's handle both cases.
            df['price_cleaned'] = df['price'].astype(str).str.replace(r'[$,]', '', regex=True)
            df['price_numeric'] = pd.to_numeric(df['price_cleaned'], errors='coerce')
        
        # Drop rows with critical missing map data
        df = df.dropna(subset=['latitude', 'longitude'])
        
        # Fill missing prices with median for visualization purposes (size param fails on NaN)
        if 'price_numeric' in df.columns:
            median_price = df['price_numeric'].median()
            if pd.isna(median_price):
                 median_price = 0
            df['price_numeric'] = df['price_numeric'].fillna(median_price)

        return df
    except Exception as e:
        st.error(f"Error loading data for {city}: {e}")
        return None

# Main Content
if selected_country and selected_city:
    with st.spinner(f"Loading data for {selected_city}, {selected_country}..."):
        df = load_data(selected_country, selected_city)

    if df is not None and not df.empty:
        # --- Filters ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("Filters")
        
        # Price Filter
        if 'price_numeric' in df.columns:
            # Handle potential empty or all-NaN price column
            if df['price_numeric'].notna().any():
                min_price = int(df['price_numeric'].min())
                max_price = int(df['price_numeric'].max())
                
                if min_price < max_price:
                    price_range = st.sidebar.slider(
                        "Price Range ($)",
                        min_value=min_price,
                        max_value=max_price,
                        value=(min_price, max_price)
                    )
                    df = df[
                        (df['price_numeric'] >= price_range[0]) & 
                        (df['price_numeric'] <= price_range[1])
                    ]
        
        # Room Type Filter
        if 'room_type' in df.columns:
            all_room_types = sorted(df['room_type'].dropna().unique().tolist())
            selected_room_types = st.sidebar.multiselect(
                "Room Type",
                all_room_types,
                default=all_room_types
            )
            if selected_room_types:
                df = df[df['room_type'].isin(selected_room_types)]

        # --- Metrics Row ---
        col1, col2, col3, col4 = st.columns(4)
        
        total_listings = len(df)
        avg_price = df['price_numeric'].mean() if 'price_numeric' in df.columns else 0
        avg_rating = df['review_scores_rating'].mean() if 'review_scores_rating' in df.columns else 0

        
        col1.metric("Total Listings", f"{total_listings:,}")
        col2.metric("Avg. Price (Night)", f"${avg_price:,.2f}")
        col3.metric("Avg. Rating", f"{avg_rating:.2f} ⭐")
        
        # Room Type Distribution (Mini chart)
        if 'room_type' in df.columns:
            room_counts = df['room_type'].value_counts()
            top_room_type = room_counts.idxmax()
            col4.metric("Top Room Type", top_room_type)

        st.markdown("---")

        # --- Interactive Map ---
        st.subheader(f"📍 Listings Map: {selected_city}")
        
        # Ensure we have lat/lon
        if 'latitude' in df.columns and 'longitude' in df.columns:
            # To keep the map fast, maybe limit points if it's huge, or use specific mapbox style
            # For now, let's plot all points but keep hover data minimal
            
            # Allow user to color by specific columns
            color_options = ['room_type', 'price_numeric', 'review_scores_rating']
            # Filter options that exist in columns
            valid_color_options = [c for c in color_options if c in df.columns]
            
            color_by = st.selectbox("Color Map By", valid_color_options, index=0 if valid_color_options else None)
            
            fig = px.scatter_mapbox(
                df,
                lat="latitude",
                lon="longitude",
                color=color_by,
                size="price_numeric" if "price_numeric" in df.columns else None,
                hover_name="name",
                hover_data=["room_type", "price", "review_scores_rating"],
                zoom=10,
                height=600,
                color_continuous_scale=px.colors.sequential.Viridis
            )
            fig.update_layout(mapbox_style="open-street-map")
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Latitude/Longitude data missing. Cannot render map.")

        # --- Optional Data View ---
        with st.expander("🔍 View Raw Data"):
            st.dataframe(df.head(100))

    else:
        st.error(f"Could not load data for {selected_city}. File might be missing.")
