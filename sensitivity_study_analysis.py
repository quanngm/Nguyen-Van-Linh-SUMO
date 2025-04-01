"""Script to coordinate sensitivity study analysis and visualisation"""

from SALib.analyze import sobol
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr
import pandas as pd
import numpy as np


# set results file
RESULTS_FILE = "./sensitivity_results.csv"


# Define problem with 4 independent vars
problem = {
    'num_vars': 4,
    'names': ['pkw', 'bus', 'scooter', 'bike'],
    'bounds': [[0, 1]] * 4
}


# read in the csv file output from simulations
data = np.genfromtxt(RESULTS_FILE, delimiter=',', skip_header=0)


X = data[:, 0:3]  # input variables
Y = data[:, 8]  # output variable   


# convert Y to np array
Y = np.array(Y)


# Run sobol sensitivity analysis
Si = sobol.analyze(problem, Y, calc_second_order=True, print_to_console=True)


# Visualise results (main effects)
labels = ['pkw', 'bus', 'scooter', 'bike']
S1 = Si['S1']
ST = Si['ST']

x = np.arange(len(labels))
width = 0.35

plt.bar(x - width/2, S1, width, label='Main Effect')
plt.bar(x + width/2, ST, width, label='Total Effect')
plt.xticks(x, labels)
plt.ylabel('Sensitivity Index')
plt.title('Sobol Sensitivity Analysis (PM2.5)')
plt.legend()
plt.tight_layout()
plt.show()


# Plot scatter plots of each vehicle type vs PM2.5

df = pd.DataFrame(data[:, 0:4], columns=labels) # vehicle proportions
df['PM2.5'] = data[:, 8]  # PM2.5

# Set up 2x2 grid of plots
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
axes = axes.flatten()

for i, var in enumerate(labels):
    x = df[var]
    y = df['PM2.5']

    # Plot scatter and regression line
    sns.regplot(x=x, y=y, ax=axes[i],
                scatter_kws={'alpha': 0.4},
                line_kws={'color': 'red'})

    # Spearman correlation
    rho, pval = spearmanr(x, y)

    # Gradient (slope) of the linear fit
    slope, intercept = np.polyfit(x, y, deg=1)

    # Title with correlation and gradient
    axes[i].set_title(
        f'{var} vs PM2.5\n'
        f'Spearman r = {rho:.3f}, p = {pval:.3g}, slope = {slope:.3f}'
    )
    axes[i].set_xlabel(f'{var} proportion')
    axes[i].set_ylabel('PM2.5')

plt.tight_layout()
plt.show()
