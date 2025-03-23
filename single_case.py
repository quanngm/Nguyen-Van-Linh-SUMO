import xml.etree.ElementTree as ET
import os
import subprocess
import pandas as pd

# 🛠 Định nghĩa đường dẫn đến các file đầu vào
NETWORK_FILE = "simpleT.net.xml"
ROUTE_FILE = "simpleT.rou.xml"
CONFIG_FILE = "simpleT.sumocfg"
EMISSION_FILE = "emissions_data.xml"

# 🛠 Thư mục chứa file đầu ra
OUTPUT_FOLDER = "output/"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

MODIFIED_ROUTE_FILE = os.path.join(OUTPUT_FOLDER, "modified_simpleT.rou.xml")

# 🛠 Kiểm tra các file đầu vào trước khi chạy mô phỏng
def check_input_files():
    """Kiểm tra xem các file đầu vào có tồn tại không."""
    missing_files = []
    for file in [NETWORK_FILE, ROUTE_FILE, CONFIG_FILE]:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Error: Missing input files: {', '.join(missing_files)}")
        return False
    return True

# 🛠 Lấy tổng số lượng xe hiện có từ .rou.xml
def get_total_vehicles(root, vehicle_types):
    """Lấy tổng số lượng xe hiện có trong file .rou.xml."""
    total_vehicles = 0
    vehicle_counts = {vtype: 0 for vtype in vehicle_types}
    
    for flow in root.findall("flow"):
        vtype = flow.get("type")
        if vtype in vehicle_counts:
            count = int(flow.get("number"))
            vehicle_counts[vtype] += count
            total_vehicles += count

    return total_vehicles, vehicle_counts

# 🛠 Điều chỉnh số lượng xe theo phần trăm nhập vào
def adjust_vehicle_numbers(xml_file, output_file, new_percentages):
    """Điều chỉnh số lượng xe trong file .rou.xml theo phần trăm do người dùng nhập vào."""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    vehicle_types = new_percentages.keys()
    total_vehicles, vehicle_counts = get_total_vehicles(root, vehicle_types)

    # Tính toán số lượng xe mới theo phần trăm người dùng nhập
    new_counts = {vtype: int((new_percentages[vtype] / 100) * total_vehicles) for vtype in vehicle_types}

    for flow in root.findall("flow"):
        vtype = flow.get("type")
        if vtype in new_counts:
            original_count = int(flow.get("number"))
            type_ratio = original_count / vehicle_counts[vtype] if vehicle_counts[vtype] > 0 else 1
            flow.set("number", str(max(1, int(new_counts[vtype] * type_ratio))))  # Cập nhật số lượng xe

    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"✅ Updated .rou.xml saved as: {output_file}")

# 🛠 Cập nhật file cấu hình SUMO để sử dụng file route mới
def update_sumo_config(config_file, output_file, new_route_file, emission_file):
    """Cập nhật file .sumocfg để sử dụng route file đã thay đổi và xuất file phát thải."""
    tree = ET.parse(config_file)
    root = tree.getroot()

    for elem in root.findall(".//route-files"):
        elem.set("value", new_route_file)

    # Cập nhật file phát thải
    processing = root.find(".//processing")
    if processing is None:
        processing = ET.SubElement(root, "processing")

    emission_elem = processing.find(".//emission-output")
    if emission_elem is None:
        emission_elem = ET.SubElement(processing, "emission-output")

    emission_elem.set("value", emission_file)

    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"✅ Updated .sumocfg saved as: {output_file}")

# 🛠 Chạy mô phỏng SUMO
def run_sumo_simulation(config_file):
    """Chạy mô phỏng SUMO với file cấu hình đã chỉnh sửa."""
    print("🚦 Running SUMO Simulation...")
    sumo_command = ["sumo", "-c", config_file]
    subprocess.run(sumo_command)

# 🛠 Trích xuất dữ liệu phát thải từ SUMO
def parse_emission_data(emission_file):
    """Trích xuất dữ liệu phát thải từ file emissions_data.xml."""
    if not os.path.exists(emission_file):
        print(f"❌ No emission data found for {emission_file}. Skipping...")
        return None

    tree = ET.parse(emission_file)
    root = tree.getroot()

    total_emissions = {
        "CO2 (g)": 0,
        "CO (g)": 0,
        "NOx (g)": 0,
        "PMx (g)": 0,
        "Fuel (L)": 0
    }

    for timestep in root.findall("timestep"):
        for vehicle in timestep.findall("vehicle"):
            total_emissions["CO2 (g)"] += float(vehicle.get("CO2", 0))
            total_emissions["CO (g)"] += float(vehicle.get("CO", 0))
            total_emissions["NOx (g)"] += float(vehicle.get("NOx", 0))
            total_emissions["PMx (g)"] += float(vehicle.get("PMx", 0))
            total_emissions["Fuel (L)"] += float(vehicle.get("fuel", 0))

    df = pd.DataFrame([total_emissions])
    return df

# 🛠 Lưu dữ liệu vào CSV
def save_data(df, output_file):
    """Lưu dữ liệu vào file CSV."""
    df.to_csv(output_file, index=False)
    print(f"✅ Emission data saved to {output_file}")

# 🛠 Chạy mô phỏng với một kịch bản duy nhất
def main():
    """Chạy toàn bộ quy trình mô phỏng với phần trăm xe nhập từ người dùng."""
    
    # 🔹 Bước 1: Kiểm tra file đầu vào
    if not check_input_files():
        print("⏭ Skipping simulation due to missing files.")
        return

    # 🔹 Bước 2: Nhập phần trăm xe từ người dùng
    print("\n🔢 Nhập tỷ lệ phần trăm của từng loại xe (tổng cộng phải là 100%)")
    vehicle_types = ["pkw", "bus", "bike", "scooter"]
    new_distribution = {}

    total_percent = 0
    for vtype in vehicle_types:
        percent = float(input(f"Nhập tỷ lệ phần trăm của {vtype}: "))
        new_distribution[vtype] = percent
        total_percent += percent

    if total_percent != 100:
        print("❌ Lỗi: Tổng phần trăm phải bằng 100%. Hãy nhập lại!")
        return

    print(f"\n🚗 Phân bố phương tiện: {new_distribution}")

    # 🔹 Bước 3: Chỉnh sửa số lượng xe
    adjust_vehicle_numbers(ROUTE_FILE, MODIFIED_ROUTE_FILE, new_distribution)
    update_sumo_config(CONFIG_FILE, CONFIG_FILE, MODIFIED_ROUTE_FILE, EMISSION_FILE)

    # 🔹 Bước 4: Chạy mô phỏng SUMO
    run_sumo_simulation(CONFIG_FILE)

    # 🔹 Bước 5: Trích xuất dữ liệu phát thải
    df_emission = parse_emission_data(EMISSION_FILE)
    if df_emission is None:
        print("❌ No emission data available. Exiting.")
        return

    # 🔹 Bước 6: Lưu dữ liệu phát thải vào CSV
    output_file = os.path.join(OUTPUT_FOLDER, "emissions_output_{new_distribution}.csv")
    save_data(df_emission, output_file)

    print("✅ SUMO Simulation Completed Successfully!")

# Chạy chương trình
if __name__ == "__main__":
    main()
