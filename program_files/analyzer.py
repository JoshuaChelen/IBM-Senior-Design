import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import config

# --------------------------------------------------
# Step 2: Define delay model with μ sum constraint
# --------------------------------------------------

def combined_delay(lmbda_and_idx, *mu_params):
    lmbda, q_idx = lmbda_and_idx
    mu_vals = np.array(mu_params)  # no enforced sum constraint

    W_pred = np.zeros_like(lmbda, dtype=float)

    for i in range(len(lmbda)):
        q = int(q_idx[i])

        if mu_vals[q] <= lmbda[i]:
            W_pred[i] = 1e6  # overload protection
        else:
            W_pred[i] = 1.0 / (mu_vals[q] - lmbda[i])

    return W_pred



# Flow propagation engine
# Supports linear, branching, merging
def compute_lambdas(lambda_main, routing, source_queue):
    lambdas = {q: 0.0 for q in routing.keys()}
    lambdas[source_queue] = lambda_main

    for q in routing:
        for next_q, prob in routing[q].items():
            lambdas[next_q] += lambdas[q] * prob

    return lambdas


# System analysis function (baseline + what-if)
def analyze_system(lambda_main, mu_dict, routing, source_queue):
    lambdas = compute_lambdas(lambda_main, routing, source_queue)

    rho = {}
    for q in mu_dict:
        rho[q] = lambdas[q] / mu_dict[q]

    bottleneck = max(rho, key=rho.get)

    return {
        "lambdas": lambdas,
        "rho": rho,
        "bottleneck": bottleneck
    }


# Find Maximum System Capacity
def find_max_capacity(mu_dict, routing, source_queue, step=0.01, max_search=100):
    """
    Increase lambda_main gradually until some queue hits rho >= 1.
    Returns the maximum safe lambda and the bottleneck queue.
    """

    lambda_main = 0.0
    last_safe_lambda = 0.0
    bottleneck_queue = None

    while lambda_main < max_search:

        result = analyze_system(
            lambda_main=lambda_main,
            mu_dict=mu_dict,
            routing=routing,
            source_queue=source_queue
        )

        rho_vals = result["rho"]

        # Check if any queue overloaded
        if any(r >= 1 for r in rho_vals.values()):
            bottleneck_queue = max(rho_vals, key=rho_vals.get)
            break

        last_safe_lambda = lambda_main
        lambda_main += step

    return last_safe_lambda, bottleneck_queue



'''
THIS IS THE MAIN FUNCTION WHERE EVERYTHING UIS STARTING FROM AND THE HELPER FUNCTIONS FROM ABOVE WILL 
BE CALLED HERE AND USED.
'''
def run(csv_file_name:str):
    # --------------------------------------------------
    # Step 1: Load CSV Data
    # --------------------------------------------------
    cfg = config.get_config("dev_config.ini")
    data_path = cfg.get("paths","processed_data_dir")+"/"+csv_file_name
    df = pd.read_csv(data_path)

    # Dynamically detect queues from CSV
    queue_lambda_cols = [c for c in df.columns if c.startswith("queue_lambdas.")]
    queue_delay_cols = [c for c in df.columns if c.startswith("delays.")]

    queue_names = [c.split(".")[1] for c in queue_lambda_cols]
    N = len(queue_names)

    # Extract data dynamically
    lambda_arrays = [df[f"queue_lambdas.{q}"].values for q in queue_names]
    delay_arrays = [df[f"delays.{q}"].values for q in queue_names]

    # Combine all queues' data
    lambda_all = np.concatenate(lambda_arrays)
    W_all = np.concatenate(delay_arrays)

    queue_idx = np.concatenate([
        np.full(len(df), i, dtype=int)
        for i in range(N)
    ])

    # --------------------------------------------------
    # Step 3: Fit μ values
    # --------------------------------------------------

    p0 = [1.0] * N  # initial guess per queue

    popt, _ = curve_fit(
        combined_delay,
        (lambda_all, queue_idx),
        W_all,
        p0=p0,
        maxfev=20000
    )

    mu_est = popt  # CHANGED: no forced sum=1

    mu_dict = {queue_names[i]: mu_est[i] for i in range(N)}

    print("\nEstimated μ values:")
    for q in mu_dict:
        print(f"{q}: μ = {mu_dict[q]:.4f}")

    # --------------------------------------------------
    # Step 4: Plot actual vs fitted curves
    # --------------------------------------------------

    plt.figure(figsize=(8, 5))

    for i, q in enumerate(queue_names):
        mask = queue_idx == i

        plt.scatter(
            lambda_all[mask],
            W_all[mask],
            label=f"{q} Data"
        )

        l_space = np.linspace(0, max(lambda_all[mask]) * 1.1, 200)
        W_fit = 1.0 / (mu_est[i] - l_space)

        plt.plot(
            l_space,
            W_fit,
            linestyle="--",
            label=f"{q} Fit"
        )

    plt.xlabel("λ (Arrival Rate)")
    plt.ylabel("W (Delay)")
    plt.title("Curve Fit for μ Estimation")
    plt.legend()
    plt.grid(True)
    plt.show()

    # NEW: Define routing 
    # Q1 -> Q2 -> Q3
    routing = {
        queue_names[0]: {queue_names[1]: 1.0} if N > 1 else {},
        queue_names[1]: {queue_names[2]: 1.0} if N > 2 else {},
        queue_names[2]: {} if N > 2 else {}
    }


    source_queue = queue_names[0]

    # --------------------------------------------------
    # Baseline Analysis
    # --------------------------------------------------
    lambda_main = df["lambda_main"].mean()

    baseline = analyze_system(
        lambda_main=lambda_main,
        mu_dict=mu_dict,
        routing=routing,
        source_queue=source_queue
    )

    print("\n--- Baseline Analysis ---")
    for q in baseline["rho"]:
        print(f"{q}: λ = {baseline['lambdas'][q]:.4f}, ρ = {baseline['rho'][q]:.4f}")

    print(f"Bottleneck: {baseline['bottleneck']}")

    # What-If Scenario (MVP)
    # Increase λ_main by 20%
    lambda_main_new = lambda_main * 1.2

    what_if = analyze_system(
        lambda_main=lambda_main_new,
        mu_dict=mu_dict,
        routing=routing,
        source_queue=source_queue
    )

    print("\n--- What-If: Increase λ_main by 20% ---")
    for q in what_if["rho"]:
        print(f"{q}: λ = {what_if['lambdas'][q]:.4f}, ρ = {what_if['rho'][q]:.4f}")

    print(f"New Bottleneck: {what_if['bottleneck']}")

    # --------------------------------------------------
    # Comparison Summary
    # --------------------------------------------------
    print("\n--- Comparison Summary ---")
    for q in baseline["rho"]:
        print(
            f"{q}: ρ_old = {baseline['rho'][q]:.4f}, "
            f"ρ_new = {what_if['rho'][q]:.4f}"
        )


    # --------------------------------------------------
    # Maximum System Capacity
    # --------------------------------------------------
    max_lambda, bottleneck_queue = find_max_capacity(
        mu_dict=mu_dict,
        routing=routing,
        source_queue=source_queue
    )
    #printing out evrything
    print("\n--- Maximum System Capacity ---")
    print(f"Maximum safe λ_main: {max_lambda:.4f}")
    print(f"System Bottleneck at Capacity: {bottleneck_queue}")