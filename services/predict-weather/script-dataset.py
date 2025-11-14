import pandas as pd
import numpy as np

# ==================== CONFIGURATION ====================
# Define date range for filtering data: 2022-01-01 to 2025-12-31 (UTC timezone)
DATE_START = pd.to_datetime('2022-01-01', utc=True)
DATE_END = pd.to_datetime('2025-12-31', utc=True)

# Columns to exclude from hourly weather data (geographic metadata and derived metrics)
EXCLUDE_COLS_HOURLY = ["numero_poste","nom_usuel","latitude","longitude","altitude","duree_precipitations", "vent_moyen", "code_etat_neige", "charge_neige",
                       "neige_au_sol", "code_etat_sol_sans_neige", "code_etat_sol_avec_neige"]

# Columns to exclude from alert data (redundant classification column)
EXCLUDE_COLS_ALERT = ["type_vigilance"]

def load_and_filter_data(filepath, date_col_pattern='date', date_start=DATE_START, date_end=DATE_END, exclude_cols=None, dept_number=92):
    """
    Load CSV file and apply standard data cleaning filters.
    
    Workflow:
    1. Read CSV file into DataFrame
    2. Auto-detect datetime column (searches for 'date' or 'time' keywords)
    3. Convert all date-related columns to datetime objects
    4. Normalize all datetimes to UTC timezone
    5. Filter rows to specified date range (DATE_START to DATE_END)
    6. Filter to specific department (default: 92 = Hauts-de-Seine)
    7. Remove unwanted columns from the dataset
    
    Args:
        filepath (str): Path to CSV file
        date_col_pattern (str): Keyword to identify datetime column
        date_start (pd.Timestamp): Start of date filter range
        date_end (pd.Timestamp): End of date filter range
        exclude_cols (list): Column names to remove
        dept_number (int): Department ID to filter on (92 = Île-de-France)
    
    Returns:
        tuple: (filtered_dataframe, datetime_column_name)
    """
    # Read CSV file into memory
    df = pd.read_csv(filepath)
    
    # Auto-detect datetime column by searching for 'date' or 'time' patterns
    dt_col = next((col for col in df.columns if date_col_pattern in col.lower() or 'time' in col.lower()), df.columns[0])
    
    # Convert all columns containing 'date' in name to datetime type for proper comparison
    for col in df.columns:
        if 'date' in col.lower():
            df[col] = pd.to_datetime(df[col])
    
    # Normalize timezone handling: ensure all datetimes use UTC for consistent comparisons
    if df[dt_col].dt.tz is not None:
        # If already timezone-aware, convert to UTC
        df[dt_col] = df[dt_col].dt.tz_convert('UTC')
    else:
        # If timezone-naive, localize to UTC
        df[dt_col] = df[dt_col].dt.tz_localize('UTC')
    
    # Filter to specified date range (reduces data to relevant time period)
    df = df[(df[dt_col] >= date_start) & (df[dt_col] <= date_end)]
    
    # Filter to specific department (Île-de-France region: dept 92)
    # Search for department column by various naming conventions
    dept_cols = [col for col in df.columns if 'department' in col.lower() or 'num_departement' in col.lower() or 'departement' in col.lower()]
    if dept_cols:
        dept_col = dept_cols[0]
        df = df[df[dept_col] == dept_number]
    
    # Remove unwanted columns to reduce memory footprint and improve processing
    if exclude_cols:
        df = df[[col for col in df.columns if col not in exclude_cols]]
    
    return df, dt_col

# ==================== LOAD & FILTER DATA ====================
# Load hourly meteorological observations from Météo-France
print("Loading hourly weather data...")
df_hourly_filtered, datetime_col = load_and_filter_data(
    r"chemin\vers\meteo_france_horaire_2020-2025.csv",
    exclude_cols=EXCLUDE_COLS_HOURLY
)
print(f"  ✓ Hourly weather: {len(df_hourly_filtered)} rows, {len(df_hourly_filtered.columns)} cols")

# Load weather alert/vigilance data with warning levels and time ranges
print("Loading alert data...")
df_alerts_filtered, datetime_col_alert = load_and_filter_data(
    r"chemin\vers\meteo_france_alertes_2020-2025.csv",
    exclude_cols=EXCLUDE_COLS_ALERT
)
print(f"  ✓ Alerts: {len(df_alerts_filtered)} rows, {len(df_alerts_filtered.columns)} cols")

# ==================== CREATE PHENOMENA-VIGILANCE PIVOT ====================
def create_weather_phenomena_dataset(
    df_hourly, 
    df_alerts, 
    datetime_col_hourly='datetime',
    datetime_col_alert='date_debut_vigilance',
    date_end_col='date_fin_vigilance',
    phenomene_col='phenomene_id',
    vigilance_col='niveau_vigilance',
    quantite_precipitations='quantite_precipitations',
    temperature_instant='temperature_instant',
    num_phenomena=7
):
    """
    Create a combined dataset merging hourly weather with active weather phenomenon alerts.
    
    Algorithm:
    1. Extract weather metrics (datetime, precipitation, temperature) from hourly data
    2. For each weather phenomenon (1-7):
       - Filter alerts matching this phenomenon ID
       - For each hourly timestamp, find overlapping alert periods
       - Assign vigilance level from matching alert, or default to 1 (no alert)
    3. Convert datetimes to standardized string format for export
    
    Key Feature: Missing alerts default to vigilance level 1 (lowest alert severity)
    This ensures no NULL values in the final dataset.
    
    Args:
        df_hourly: DataFrame with hourly weather observations
        df_alerts: DataFrame with weather alerts and vigilance levels
        datetime_col_hourly: Name of datetime column in hourly data
        datetime_col_alert: Name of alert start datetime column
        date_end_col: Name of alert end datetime column
        phenomene_col: Name of phenomenon ID column
        vigilance_col: Name of vigilance level column
        quantite_precipitations: Name of precipitation column
        temperature_instant: Name of temperature column
        num_phenomena: Number of weather phenomena to include (default: 7)
    
    Returns:
        DataFrame with columns: datetime, precipitation, temperature, phenomene_1...phenomene_7
    """
    
    # Initialize result with hourly weather data (datetime, precipitation, temperature)
    result = df_hourly[[datetime_col_hourly, quantite_precipitations, temperature_instant]].copy()
    result = result.rename(columns={datetime_col_hourly: 'datetime'})
    
    # Iterate through each phenomenon (1 to num_phenomena) and add vigilance level column
    for phenom_id in range(1, num_phenomena + 1):
        phenom_col_name = f'phenomene_{phenom_id}'
        
        # Filter alerts to only those matching current phenomenon ID
        phenom_alerts = df_alerts[df_alerts[phenomene_col] == phenom_id].copy()
        
        # If no alerts exist for this phenomenon, assign default level 1 to all rows
        if len(phenom_alerts) == 0:
            result[phenom_col_name] = 1
            continue
        
        # Define function to find vigilance level for a given timestamp
        # This function checks if timestamp falls within any alert period for this phenomenon
        def get_vigilance(row_dt):
            """
            Find vigilance level for a specific datetime.
            Searches for alert where: alert_start <= row_dt <= alert_end
            Returns vigilance level if found, otherwise returns 1 (default/no alert)
            """
            # Filter alerts that cover this timestamp (date_debut <= row_dt <= date_fin)
            matching = phenom_alerts[
                (phenom_alerts[datetime_col_alert] <= row_dt) &
                (phenom_alerts[date_end_col] >= row_dt)
            ]
            # Return vigilance level from first matching alert, or 1 if none found
            if len(matching) > 0:
                return matching.iloc[0][vigilance_col]
            return 1  # Default to 1 when no alert matches (no weather threat)
        
        # Apply get_vigilance function to each hourly timestamp
        result[phenom_col_name] = result['datetime'].apply(get_vigilance)
    
    # Ensure no NaN values remain in phenomenon columns (fill with default level 1)
    phenomenon_cols = [f'phenomene_{i}' for i in range(1, num_phenomena + 1)]
    result[phenomenon_cols] = result[phenomenon_cols].fillna(1)
    
    # Convert datetime objects to standardized string format (project convention: YYYY-MM-DD HH:MM:SS)
    result['datetime'] = result['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return result


# ==================== EXECUTE PIPELINE ====================
# Create combined weather-phenomena dataset by merging hourly observations with alert vigilance levels
print("Creating weather-phenomena dataset...")
df_pivot = create_weather_phenomena_dataset(
    df_hourly=df_hourly_filtered,
    df_alerts=df_alerts_filtered,
    datetime_col_hourly=datetime_col,
    datetime_col_alert='date_debut_vigilance',
    date_end_col='date_fin_vigilance',
    phenomene_col='phenomene_id',
    vigilance_col='niveau_vigilance',
    quantite_precipitations='quantite_precipitations',
    temperature_instant='temperature_instant',
    num_phenomena=7
)

# Export final dataset to CSV file for downstream analysis
df_pivot.to_csv(r"chemin\vers\output-dataset.csv", index=False)

# ==================== OUTPUT STATISTICS ====================
print(f"\n✓ Dataset created!")
print(f"  Shape: {df_pivot.shape}")
print(f"  Columns: {list(df_pivot.columns)}")

# Display sample of data
print(f"\nFirst 5 rows:")
print(df_pivot.head())

# Show data types for each column
print(f"\nData types:")
print(df_pivot.dtypes)

# Verify data quality: check for missing/null values (should be none due to fillna(1))
print(f"\nMissing values per column:")
print(df_pivot.isnull().sum())