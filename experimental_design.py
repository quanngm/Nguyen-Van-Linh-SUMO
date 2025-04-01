"""Functions for experimental design and sensitivity analysis"""

from SALib.sample import saltelli
import numpy as np


def sobol_sensitivity(total_vehicles):
    """code to generate sobol design for sensitivity analysis using saltelli sampling"""

    # Define problem with 4 independent vars
    problem = {
        'num_vars': 4,
        'names': ['pkw', 'bus', 'scooter', 'bike'],
        'bounds': [[0, 1]] * 4
    }

    # Generate Sobol samples (512 samples is hard coded but can be changed)
    param_values = saltelli.sample(problem, 512, calc_second_order=True) 

    # Normalize each row to sum to 1
    proportions = param_values / param_values.sum(axis=1, keepdims=True)

    # Scale to total vehicle counts
    vehicle_counts = np.floor(proportions * total_vehicles).astype(int)

    # Fix rounding to sum to total_vehicles (will slightly affect the design)
    adjustment = total_vehicles - vehicle_counts.sum(axis=1)
    for i in range(len(vehicle_counts)):
        if adjustment[i] > 0:
            fractions = proportions[i] * total_vehicles - vehicle_counts[i]
            for idx in np.argsort(fractions)[-adjustment[i]:]:
                vehicle_counts[i, idx] += 1

    return vehicle_counts
