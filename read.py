import xml.etree.ElementTree as ET
from collections import defaultdict

# Load and parse the tripinfo file
tree = ET.parse('data.xml')
root = tree.getroot()

# Dictionary: {flow_id: {vehicle_type: count}}
flow_vehicle_counts = defaultdict(lambda: defaultdict(int))

for trip in root.findall('tripinfo'):
    full_id = trip.get('id')      # e.g., pkw12.0
    vtype = trip.get('vType')     # e.g., pkw

    if '.' in full_id:
        flow_id = full_id.split('.')[0]  # e.g., pkw12
        flow_vehicle_counts[flow_id][vtype] += 1

# In kết quả
print("📊 Vehicle counts by flow and type:\n")
for flow_id, vtype_dict in flow_vehicle_counts.items():
    print(f"Flow: {flow_id}")
    for vtype, count in vtype_dict.items():
        print(f"  - {vtype}: {count}")
    print()
