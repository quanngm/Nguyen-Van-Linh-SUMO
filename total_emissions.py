import xml.etree.ElementTree as ET
import pandas as pd
import os

def sum_total_emissions(xml_file, csv_output="total_emissions.csv"):
    # Check if file exists
    if not os.path.exists(xml_file):
        print(f"Error: {xml_file} not found. Ensure SUMO has generated emission data.")
        return None

    # Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Initialize total sums
    total_emissions = {
        "Total CO2 (g)": 0,
        "Total CO (g)": 0,
        "Total HC (g)": 0,
        "Total NOx (g)": 0,
        "Total PMx (g)": 0,
        "Total Fuel (L)": 0
    }

    # Extract and sum emissions
    for timestep in root.findall("timestep"):
        for vehicle in timestep.findall("vehicle"):
            total_emissions["Total CO2 (g)"] += float(vehicle.get("CO2", 0))
            total_emissions["Total CO (g)"] += float(vehicle.get("CO", 0))
            total_emissions["Total HC (g)"] += float(vehicle.get("HC", 0))
            total_emissions["Total NOx (g)"] += float(vehicle.get("NOx", 0))
            total_emissions["Total PMx (g)"] += float(vehicle.get("PMx", 0))
            total_emissions["Total Fuel (L)"] += float(vehicle.get("fuel", 0))

    # Convert to DataFrame
    df = pd.DataFrame([total_emissions])

    # Save as CSV
    df.to_csv(csv_output, index=False)
    print(f"Total emissions saved to {csv_output}")

    return df

# Specify the SUMO emissions file
xml_filename = "emissions_data.xml"

# Process and sum total emissions
df_total_emissions = sum_total_emissions(xml_filename)

# # Display CSV data if processing was successful
# if df_total_emissions is not None:
#     import ace_tools as tools
#     tools.display_dataframe_to_user(name="Total SUMO Emissions", dataframe=df_total_emissions)
