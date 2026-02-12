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

# View Mode Selection
view_mode = st.sidebar.radio("View Mode", ["Single City", "Compare Cities", "Compare Countries"])

if view_mode == "Single City":
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

@st.cache_data
def load_multiple_cities_data(locations_dict, city_selections):
    """Load data for multiple cities and add city/country identifiers."""
    all_data = []
    for country, city in city_selections:
        df = load_data(country, city)
        if df is not None and not df.empty:
            df['city'] = city
            df['country'] = country
            all_data.append(df)
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        return combined_df
    return None

@st.cache_data
def load_country_data(locations_dict, countries_list):
    """Load data for all cities in specified countries."""
    all_data = []
    for country in countries_list:
        if country in locations_dict:
            for city in locations_dict[country]:
                df = load_data(country, city)
                if df is not None and not df.empty:
                    df['city'] = city
                    df['country'] = country
                    all_data.append(df)
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        return combined_df
    return None

# Main Content
if view_mode == "Single City":
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

elif view_mode == "Compare Cities":
    st.subheader("Compare Multiple Cities")
    
    # Multi-select cities across countries
    selected_countries = st.sidebar.multiselect("Select Countries", sorted(locations.keys()))
    
    if selected_countries:
        city_options = []
        for country in selected_countries:
            for city in locations[country]:
                city_options.append((country, city, f"{city}, {country}"))
        
        selected_city_pairs = []
        for country, city, display_name in city_options:
            if st.sidebar.checkbox(display_name):
                selected_city_pairs.append((country, city))
        
        if selected_city_pairs:
            with st.spinner("Loading data for selected cities..."):
                comparison_df = load_multiple_cities_data(locations, selected_city_pairs)
            
            if comparison_df is not None and not comparison_df.empty:
                # Price filter
                st.sidebar.markdown("---")
                st.sidebar.subheader("Price Filter")
                if 'price_numeric' in comparison_df.columns and comparison_df['price_numeric'].notna().any():
                    min_price = int(comparison_df['price_numeric'].min())
                    max_price = int(comparison_df['price_numeric'].max())
                    
                    # Quick preset buttons
                    st.sidebar.write("Quick Presets:")
                    cols = st.sidebar.columns(5)
                    presets = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
                    
                    selected_preset = None
                    for i, preset in enumerate(presets):
                        with cols[i % 5]:
                            if st.button(f"< ${preset}"):
                                selected_preset = preset
                    
                    # Slider
                    if selected_preset:
                        default_value = (min_price, min(selected_preset, max_price))
                    else:
                        default_value = (min_price, max_price)
                    
                    price_range = st.sidebar.slider(
                        "Price Range ($)",
                        min_value=min_price,
                        max_value=max_price,
                        value=default_value
                    )
                    comparison_df = comparison_df[
                        (comparison_df['price_numeric'] >= price_range[0]) & 
                        (comparison_df['price_numeric'] <= price_range[1])
                    ]
                
                # Price statistics by city
                st.markdown("---")
                st.subheader("📊 Price Statistics by City")
                
                city_stats = comparison_df.groupby('city').agg({
                    'price_numeric': ['count', 'mean', 'median', 'min', 'max', 'std']
                }).round(2)
                city_stats.columns = ['Total Listings', 'Avg Price', 'Median Price', 'Min Price', 'Max Price', 'Std Dev']
                st.dataframe(city_stats, use_container_width=True)
                
                # Price distribution box plot
                st.markdown("---")
                st.subheader("📈 Price Distribution Comparison")
                
                fig = px.box(
                    comparison_df,
                    x='city',
                    y='price_numeric',
                    title="Price Distribution by City",
                    labels={'city': 'City', 'price_numeric': 'Price ($)'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Average price bar chart
                avg_prices = comparison_df.groupby('city')['price_numeric'].mean().sort_values(ascending=False)
                fig2 = px.bar(
                    x=avg_prices.index,
                    y=avg_prices.values,
                    title="Average Price by City",
                    labels={'x': 'City', 'y': 'Average Price ($)'},
                    color=avg_prices.values,
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                # Room type comparison
                if 'room_type' in comparison_df.columns:
                    st.markdown("---")
                    st.subheader("🏠 Room Type Distribution")
                    
                    room_city_counts = pd.crosstab(comparison_df['city'], comparison_df['room_type'])
                    fig3 = px.bar(
                        room_city_counts,
                        title="Room Type Distribution by City",
                        barmode='group',
                        labels={'value': 'Count', 'index': 'City'}
                    )
                    st.plotly_chart(fig3, use_container_width=True)
            else:
                st.error("Could not load data for selected cities.")
        else:
            st.info("Select at least one city to compare.")
    else:
        st.info("Select at least one country to see available cities.")

elif view_mode == "Compare Countries":
    st.subheader("Compare Countries")
    
    # Multi-select countries
    selected_countries = st.sidebar.multiselect("Select Countries to Compare", sorted(locations.keys()), default=[sorted(locations.keys())[0]] if locations else [])
    
    if selected_countries:
        with st.spinner("Loading data for selected countries..."):
            country_df = load_country_data(locations, selected_countries)
        
        if country_df is not None and not country_df.empty:
            # Price filter
            st.sidebar.markdown("---")
            st.sidebar.subheader("Price Filter")
            if 'price_numeric' in country_df.columns and country_df['price_numeric'].notna().any():
                min_price = int(country_df['price_numeric'].min())
                max_price = int(country_df['price_numeric'].max())
                
                # Quick preset buttons
                st.sidebar.write("Quick Presets:")
                cols = st.sidebar.columns(5)
                presets = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
                
                selected_preset = None
                for i, preset in enumerate(presets):
                    with cols[i % 5]:
                        if st.button(f"< ${preset}", key=f"country_preset_{preset}"):
                            selected_preset = preset
                
                # Slider
                if selected_preset:
                    default_value = (min_price, min(selected_preset, max_price))
                else:
                    default_value = (min_price, max_price)
                
                price_range = st.sidebar.slider(
                    "Price Range ($)",
                    min_value=min_price,
                    max_value=max_price,
                    value=default_value,
                    key="country_price_range"
                )
                country_df = country_df[
                    (country_df['price_numeric'] >= price_range[0]) & 
                    (country_df['price_numeric'] <= price_range[1])
                ]
            
            # Price statistics by country
            st.markdown("---")
            st.subheader("📊 Price Statistics by Country")
            
            country_stats = country_df.groupby('country').agg({
                'price_numeric': ['count', 'mean', 'median', 'min', 'max', 'std']
            }).round(2)
            country_stats.columns = ['Total Listings', 'Avg Price', 'Median Price', 'Min Price', 'Max Price', 'Std Dev']
            st.dataframe(country_stats, use_container_width=True)
            
            # Price distribution box plot by country
            st.markdown("---")
            st.subheader("📈 Price Distribution Comparison")
            
            fig = px.box(
                country_df,
                x='country',
                y='price_numeric',
                title="Price Distribution by Country",
                labels={'country': 'Country', 'price_numeric': 'Price ($)'}
            )
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Average price bar chart
            avg_prices = country_df.groupby('country')['price_numeric'].mean().sort_values(ascending=False)
            fig2 = px.bar(
                x=avg_prices.index,
                y=avg_prices.values,
                title="Average Price by Country",
                labels={'x': 'Country', 'y': 'Average Price ($)'},
                color=avg_prices.values,
                color_continuous_scale='Viridis'
            )
            fig2.update_xaxes(tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)
            
            # Listings count by country
            st.markdown("---")
            st.subheader("🏠 Total Listings by Country")
            
            listings_count = country_df.groupby('country').size().sort_values(ascending=False)
            fig3 = px.bar(
                x=listings_count.index,
                y=listings_count.values,
                title="Total Listings by Country",
                labels={'x': 'Country', 'y': 'Number of Listings'},
                color=listings_count.values,
                color_continuous_scale='Blues'
            )
            fig3.update_xaxes(tickangle=-45)
            st.plotly_chart(fig3, use_container_width=True)
            
            # Room type distribution by country
            if 'room_type' in country_df.columns:
                st.markdown("---")
                st.subheader("🏠 Room Type Distribution by Country")
                
                room_country_pct = pd.crosstab(country_df['country'], country_df['room_type'], normalize='index') * 100
                fig4 = px.bar(
                    room_country_pct,
                    title="Room Type Distribution by Country (%)",
                    barmode='stack',
                    labels={'value': 'Percentage', 'index': 'Country'}
                )
                fig4.update_xaxes(tickangle=-45)
                st.plotly_chart(fig4, use_container_width=True)
        else:
            st.error("Could not load data for selected countries.")
