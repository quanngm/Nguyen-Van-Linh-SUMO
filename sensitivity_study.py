"""sensitivity study to determine sensitivity of inputs and their interactions to PM2.5 using 
sobol sensitivity analysis"""

import csv
import numpy as np
from experimental_design import sobol_sensitivity
from random_route import generate_route_file
from sumo_interface import run_sumo_simulation, parse_emission_data


TOTAL_VEHICLES = 1000
CONFIG_FILE = "complex_juntion.sumocfg"
NET_FILE = "complex_juntion.net.xml"
ROUTE_FILE = "./simpleT_random.rou.xml"
SIMULATION_DURATION = 500
RESULTS_FILE = "./sensitivity_results.csv"
EMISSION_FILE = "emissions_data.xml"

# generate the vehicle proportions for the sensitivity study
vehicle_counts = sobol_sensitivity(total_vehicles=TOTAL_VEHICLES)

# simulation loop
for index, vehicle_proportions in enumerate(vehicle_counts): # loop through each set of vehicle proportions   

    # generate and write output_file for random routes according to the design
    generate_route_file(
        net_file=NET_FILE,
        route_file=ROUTE_FILE,
        total_vehicles=TOTAL_VEHICLES,
        duration=SIMULATION_DURATION,
        vehicle_proportions=vehicle_proportions)

    # run simulation
    print("Running simulation; ", index)
    run_sumo_simulation(config_file=CONFIG_FILE) # run simulation

    # parse emissions
    emissions = parse_emission_data(emission_file=EMISSION_FILE) 

    # save results
    # header = ['pkw', 'bus', 'scooter', 'bike', 'Total CO2 (mg)', 
    # 'Total CO mg)', 'Total HC (mg)', 'Total NOx (mg)', 'Total PMx (mg)', 'Total Fuel (mg)']
    combined = np.concatenate((vehicle_proportions, + emissions.values[0])) # combine vehicle proportions and emissions


    with open(RESULTS_FILE, mode='a', encoding="utf-8") as file: # write to csv file
        writer = csv.writer(file)
        writer.writerow(combined)
