import xml.etree.ElementTree as ET  # For parsing and editing XML files (like .rou.xml and .sumocfg)
import os  # For handling file system operations
import shutil  # For copying files and directories
import subprocess  # For running external commands (like starting SUMO)
import pandas as pd  # For processing and saving tabular data (CSV)

# Define paths to base input files
NETWORK_FILE = "simpleT.net.xml"  # The road network file
ROUTE_FILE = "simpleT.rou.xml"    # The vehicle routes file
TEMPLATE_CONFIG = "template.sumocfg"  # A base SUMO config file to clone

# Create output directory if not exist
OUTPUT_FOLDER = "output/"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ✅ Check if all required input files exist
def check_input_files(): # Function to check if all input files exist
    missing = [] # List to store missing files
    for f in [NETWORK_FILE, ROUTE_FILE, TEMPLATE_CONFIG]: # Loop through all required files
        if not os.path.exists(f):   # If file does not exist
            missing.append(f)      # Add it to the missing list
    if missing: # If there are missing files
        print("❌ Missing files:", ", ".join(missing)) # Print the missing files
        return False # Return False to indicate missing files
    return True

# ✅ Count current number of vehicles of each type
def get_total_vehicles(root, types):
    total = 0 
    counts = {v: 0 for v in types} 
    for flow in root.findall("flow"):  # Loop through all flow elements
        vtype = flow.get("type") # Get the vehicle type
        if vtype in counts:
            num = int(flow.get("number")) # Get the number of vehicles
            counts[vtype] += num # Add to the count
            total += num # Add to the total
    return total, counts

# ✅ Adjust vehicle counts by percentage
def adjust_vehicle_numbers(input_file, output_file, new_percent): 
    tree = ET.parse(input_file) 
    root = tree.getroot() 

    types = new_percent.keys()  # Get all vehicle types
    total, current_counts = get_total_vehicles(root, types) # Get current vehicle counts
    new_counts = {v: int((new_percent[v] / 100) * total) for v in types} # Calculate new counts

    for flow in root.findall("flow"): # Loop through all flow elements
        vtype = flow.get("type") # Get the vehicle type
        if vtype in new_counts:
            original = int(flow.get("number")) # Get the original number of vehicles
            ratio = original / current_counts[vtype] if current_counts[vtype] > 0 else 1 # Calculate ratio
            flow.set("number", str(max(1, int(new_counts[vtype] * ratio)))) # Set new number of vehicles
    tree.write(output_file, encoding="utf-8", xml_declaration=True) # Write the updated XML to a new file

# ✅ Create a custom SUMO config for the scenario
def create_sumo_config(config_file, route_file, emission_file):
    tree = ET.parse(TEMPLATE_CONFIG)
    root = tree.getroot()

    # Update route file
    for elem in root.findall(".//route-files"):  # Find all route-files elements
        elem.set("value", route_file) # Update the route file path
    
    # Update network file path
    for elem in root.findall(".//net-file"): # Find all net-file elements
        elem.set("value", NETWORK_FILE) # Update the network file path

    # Add or update emission output file
    processing = root.find(".//processing") # Find the processing element
    if processing is None: # If processing element does not exist
        processing = ET.SubElement(root, "processing") # Create a new processing element

    emission_elem = processing.find(".//emission-output") # Find the emission-output element
    if emission_elem is None: # If emission-output element does not exist
        emission_elem = ET.SubElement(processing, "emission-output")    # Create a new emission-output element
    emission_elem.set("value", emission_file)

    tree.write(config_file, encoding="utf-8", xml_declaration=True)

# ✅ Run SUMO simulation
def run_sumo(config_file, cwd):
    subprocess.run(["sumo", "-c", config_file], cwd=cwd)

# ✅ Parse emissions data
def parse_emissions(emission_path):
    if not os.path.exists(emission_path):
        print(f"⚠️ File not found: {emission_path}")
        return None
    tree = ET.parse(emission_path)
    root = tree.getroot()
    totals = {
        "CO2 (g)": 0, "CO (g)": 0,
        "NOx (g)": 0, "PMx (g)": 0,
        "Fuel (L)": 0
    }
    for timestep in root.findall("timestep"):
        for vehicle in timestep.findall("vehicle"):
            totals["CO2 (g)"] += float(vehicle.get("CO2", 0))
            totals["CO (g)"] += float(vehicle.get("CO", 0))
            totals["NOx (g)"] += float(vehicle.get("NOx", 0))
            totals["PMx (g)"] += float(vehicle.get("PMx", 0))
            totals["Fuel (L)"] += float(vehicle.get("fuel", 0))
    return pd.DataFrame([totals])

# ✅ Save DataFrame to CSV
def save_csv(df, path):
    df.to_csv(path, index=False)

# ✅ Main execution function
def main():
    if not check_input_files():
        return

    scenario = 1    # Scenario counter
    all_data = []  # List to store all dataframes

    while True:
        print(f"\n🟢 Enter vehicle percentages for Scenario {scenario}") 
        types = ["pkw", "bus", "bike", "scooter"] # Vehicle types
        distribution = {} # Dictionary to store percentage distribution
        total = 0 # Total percentage
        for t in types: # Loop through all vehicle types
            percent = float(input(f"  {t}: ")) # Get percentage from user
            distribution[t] = percent # Store in distribution dictionary
            total += percent # Add to total
        if total != 100: # If total is not 100%
            print("❌ Total must be 100%. Please try again.") # Print error message
            continue

        # Create scenario output folder
        folder = os.path.join(OUTPUT_FOLDER, f"scenario_{scenario}") # Folder path  
        os.makedirs(folder, exist_ok=True)

        # Define file names per scenario
        route_file = os.path.join(folder, "modified.rou.xml") 
        config_file = os.path.join(folder, "modified.sumocfg")
        emission_file = os.path.join(folder, "emissions.xml")
        csv_file = os.path.join(folder, f"emissions_scenario_{scenario}.csv")

        # Copy network file to scenario folder 
        shutil.copy(NETWORK_FILE, os.path.join(folder, NETWORK_FILE))

        # Adjust vehicle distribution, create config, and run simulation
        adjust_vehicle_numbers(ROUTE_FILE, route_file, distribution)  # Adjust vehicle numbers
        create_sumo_config(config_file, os.path.basename(route_file), os.path.basename(emission_file))  # Create SUMO config
        run_sumo(config_file=os.path.basename(config_file), cwd=folder) # Run SUMO simulation

        # Parse and store emission results
        df = parse_emissions(emission_file) 
        if df is not None:  # If data is available
            df["Scenario"] = scenario  # Add scenario number
            for k, v in distribution.items(): # Add vehicle distribution
                df[k + " %"] = v 
            save_csv(df, csv_file) # Save data to CSV
            all_data.append(df)     # Append to all data list

        again = input("\n➕ Add another scenario? (y/n): ")
        if again.lower() != 'y': # If not 'y',
            break # Exit loop
        scenario += 1 # Increment scenario number

    # Merge and save all scenarios into one file
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True) # Merge all dataframes
        final_csv = os.path.join(OUTPUT_FOLDER, "all_scenarios.csv")    # Output file path
        save_csv(final_df, final_csv) # Save to CSV
        print(f"\n✅ All data saved to: {final_csv}") # Print final message

# Run main program
if __name__ == "__main__":
    main()
#---------------------------------------------------------#
# import xml.etree.ElementTree as ET
# import os
# import shutil
# import subprocess
# import pandas as pd

# # Đường dẫn gốc
# NETWORK_FILE = "simpleT.net.xml"
# ROUTE_FILE = "simpleT.rou.xml"
# TEMPLATE_CONFIG = "template.sumocfg"

# OUTPUT_FOLDER = "output/"
# os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# def check_input_files():
#     missing = []
#     for f in [NETWORK_FILE, ROUTE_FILE, TEMPLATE_CONFIG]:
#         if not os.path.exists(f):
#             missing.append(f)
#     if missing:
#         print("❌ Thiếu file:", ", ".join(missing))
#         return False
#     return True

# def get_total_vehicles(root, types):
#     total = 0
#     counts = {v: 0 for v in types}
#     for flow in root.findall("flow"):
#         vtype = flow.get("type")
#         if vtype in counts:
#             num = int(flow.get("number"))
#             counts[vtype] += num
#             total += num
#     return total, counts

# def adjust_vehicle_numbers(input_file, output_file, new_percent):
#     tree = ET.parse(input_file)
#     root = tree.getroot()

#     types = new_percent.keys()
#     total, current_counts = get_total_vehicles(root, types)
#     new_counts = {v: int((new_percent[v] / 100) * total) for v in types}

#     for flow in root.findall("flow"):
#         vtype = flow.get("type")
#         if vtype in new_counts:
#             original = int(flow.get("number"))
#             ratio = original / current_counts[vtype] if current_counts[vtype] > 0 else 1
#             flow.set("number", str(max(1, int(new_counts[vtype] * ratio))))
#     tree.write(output_file, encoding="utf-8", xml_declaration=True)

# def create_sumo_config(config_file, route_file, emission_file):
#     tree = ET.parse(TEMPLATE_CONFIG)
#     root = tree.getroot()

#     for elem in root.findall(".//route-files"):
#         elem.set("value", route_file)
#     for elem in root.findall(".//net-file"):
#         elem.set("value", NETWORK_FILE)

#     processing = root.find(".//processing")
#     if processing is None:
#         processing = ET.SubElement(root, "processing")

#     emission_elem = processing.find(".//emission-output")
#     if emission_elem is None:
#         emission_elem = ET.SubElement(processing, "emission-output")
#     emission_elem.set("value", emission_file)

#     tree.write(config_file, encoding="utf-8", xml_declaration=True)

# def run_sumo(config_file, cwd):
#     subprocess.run(["sumo", "-c", config_file], cwd=cwd)

# def parse_emissions(emission_path):
#     if not os.path.exists(emission_path):
#         print(f"⚠️ Không tìm thấy {emission_path}")
#         return None
#     tree = ET.parse(emission_path)
#     root = tree.getroot()
#     totals = {
#         "CO2 (g)": 0, "CO (g)": 0,
#         "NOx (g)": 0, "PMx (g)": 0,
#         "Fuel (L)": 0
#     }
#     for timestep in root.findall("timestep"):
#         for vehicle in timestep.findall("vehicle"):
#             totals["CO2 (g)"] += float(vehicle.get("CO2", 0))
#             totals["CO (g)"] += float(vehicle.get("CO", 0))
#             totals["NOx (g)"] += float(vehicle.get("NOx", 0))
#             totals["PMx (g)"] += float(vehicle.get("PMx", 0))
#             totals["Fuel (L)"] += float(vehicle.get("fuel", 0))
#     return pd.DataFrame([totals])

# def save_csv(df, path):
#     df.to_csv(path, index=False)

# def main():
#     if not check_input_files():
#         return

#     scenario = 1
#     all_data = []

#     while True:
#         print(f"\n🟢 Nhập phần trăm các loại xe cho Scenario {scenario}")
#         types = ["pkw", "bus", "bike", "scooter"]
#         distribution = {}
#         total = 0
#         for t in types:
#             percent = float(input(f"  {t}: "))
#             distribution[t] = percent
#             total += percent
#         if total != 100:
#             print("❌ Tổng phải là 100%. Nhập lại.")
#             continue

#         folder = os.path.join(OUTPUT_FOLDER, f"scenario_{scenario}")
#         os.makedirs(folder, exist_ok=True)

#         route_file = os.path.join(folder, "modified.rou.xml")
#         config_file = os.path.join(folder, "modified.sumocfg")
#         emission_file = os.path.join(folder, "emissions.xml")
#         csv_file = os.path.join(folder, f"emissions_scenario_{scenario}.csv")

#         shutil.copy(NETWORK_FILE, os.path.join(folder, NETWORK_FILE))

#         adjust_vehicle_numbers(ROUTE_FILE, route_file, distribution)
#         create_sumo_config(config_file, os.path.basename(route_file), os.path.basename(emission_file))
#         run_sumo(config_file=os.path.basename(config_file), cwd=folder)

#         df = parse_emissions(emission_file)
#         if df is not None:
#             df["Scenario"] = scenario
#             for k, v in distribution.items():
#                 df[k + " %"] = v
#             save_csv(df, csv_file)
#             all_data.append(df)

#         again = input("\n➕ Thêm scenario nữa không? (y/n): ")
#         if again.lower() != 'y':
#             break
#         scenario += 1

#     if all_data:
#         final_df = pd.concat(all_data, ignore_index=True)
#         final_csv = os.path.join(OUTPUT_FOLDER, "all_scenarios.csv")
#         save_csv(final_df, final_csv)
#         print(f"\n✅ Đã lưu toàn bộ vào: {final_csv}")

# if __name__ == "__main__":
#     main()
