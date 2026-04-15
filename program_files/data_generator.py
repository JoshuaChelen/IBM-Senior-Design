import json
import numpy as np
import pandas as pd
import config
from pathlib import Path

"""
# Load Data Generation Configurations
cfg = config.get_config("dev_config.ini")
data_gen_config = cfg['data_generation']
stress_test_config = cfg['stress_test_params']


# Extract parameters
ALPHA = data_gen_config.getfloat("alpha")
K = data_gen_config.getint("k")
C = data_gen_config.getfloat("C")
STARTING_MAIN_LAMBDA = data_gen_config.getfloat("starting_main_lambda")
TIME_POINTS = data_gen_config.getint("time_points")
GAUSSIAN_MEAN = data_gen_config.getfloat("gaussian_mean")
GAUSSIAN_STD = data_gen_config.getfloat("gaussian_std")
SEED = stress_test_config.getint("random_seed")
QUEUE_NETWORK_FILE = cfg.get("paths","queueing_network_file")

with open(QUEUE_NETWORK_FILE, 'r') as file:
    queue_network = json.load(file)
"""




"""
Procedure: 
1) Obtain a queue network graph.
2) Generate random values for the service rate, but still satisfy 
constraint.
3) Vary main arrival rate (λ_main). This arrival rate should be 
between 0 and 1 for any time period.
4) Compute λ_i for each of the queue. Then compute delay for each 
of the queue. 
5) Add noise to the appropriate values. 
"""



def assign_service_rates(queue_network: dict, seed:int):
    """
    Pick random values for service rate (μ). All of the μ_i should 
    follow the constraint in the queue network. 

    Args:
        queue_network (dict): The incomplete default queue network application
        schema.
        seed (int): the random seed

    Returns:
        queue_network (dict): The queue network application will randomly 
        picked service rates. 
    """
    queues = queue_network["system"]["queues"]
    constraint = queue_network["system"]["constraint"]["service_rate_sum"]
    n = len(queues)

    np.random.seed(seed)  # For reproducibility
    x = np.random.rand(n)
    nums = (x / x.sum()) * constraint  # Normalize to the value of the constraint
    
    for i, q in enumerate(queues):
        q["service_rate"] = float(nums[i])
    
    # print("Assigned service rates:", nums)
    # print("Sum:", nums.sum()) # Checking to see if it adds up
    return queue_network

# print(assign_service_rates(queue_network))

# Noise is added in a seperate function.
def compute_curr_lambda(main_lambdas, k, alpha, C) -> float:
    """
    Compute λ_main for the current timepoint based on previous timepoints. 
    Let t be the timepoint. So t+1 is the current time point, and the lambda 
    is computed as follow: 

    λ_{t+1} = αλ_t + α²λ_{t-1} + ... + αᵏλ_{t+1−k} + C
    
    Args: 
        main_lambdas (list[int]): List keeping track of all the main_lambda values from 
        all the time point. 
        k (float): How long is the dependency of λ is. 
        alpha (float): How much λ is dependent on the previous time point.
        C (float): Constant 

    Returns:
        main_lambda (float): The lambda value of the current time point. 
    """
    main_lambda = 0.0
    n = len(main_lambdas)
    
    # Loop over the last k previous lambdas
    for i in range(1, k+1):
        if n - i < 0:
            break  # Not enough history yet, so loop over existing ones
        main_lambda += (alpha ** i) * main_lambdas[-i]

    main_lambda += C
    return main_lambda

# These 2 should equal to each other 
# print(compute_curr_lambda([0.2,0.3,0.4], 2, 0.5, 0.1))
# print((0.5*0.4)+((0.5**2)*0.3)+0.1) # k = 2, alpha = 0.5, C = 0.1

# These 2 should equal to each other 
# print(compute_curr_lambda([0.3], 2, 0.5, 0.1)) # When there is not enough history 
# print(0.5*0.3+0.1) # k = 2, alpha = 0.5, C = 0.1

# Adding noise to computed main lambda 
def add_gaussian_noise(value:float, mean:float, std:float):
    """
    Add Gaussian noise to a numeric value.

    Parameters:
        value (float): original number
        mean (float): mean of Gaussian noise (default = 0)
        std (float): standard deviation of Gaussian noise (default = 0.01)

    Returns:
        float: value + noise
    """
    noise = np.random.normal(mean, std)
    return value + noise

def compute_queue_lambdas(main_lambda, queues, entry_id):
    """
    Compute the lambda for each of the queue based on their routing probability 
    and main lambda. 

    Args: 
        main_lambda (int): The main lambda entering the queue network.
        queues (list[dict]): A list of queues, where each queue has a `id`,
        `service_rate`, and `next_queue` field.
        entry_id (int): Where the main lambda will enter in the queue. 

    Returns:
        lambdas (dict): The queue id is the key, and the computed lambda for each queue 
        are the values. 
    """
    lambdas = {q["id"]: 0.0 for q in queues}
    lambdas[entry_id] = main_lambda
    
    for q in queues:
        q_id = q["id"]
        for nxt in q["next_queue"]:
            if nxt["id"] == "External": # Reached end of the queue 
                break 

            prob = nxt["probability"] / 100.0 # Convert to a probability where between 0 to 1
            routed = lambdas[q_id] * prob # We already assigned the first queue a lambda value (via entry point)
            lambdas[nxt["id"]] = lambdas.get(nxt["id"], 0) + routed
    return lambdas

def generate_data(queue_network: json, time, main_lambda, k, alpha, C, gaussian_mean:float, gaussian_std:float):
    """
    Generate synthethic datas. 

    Args: 
        queue_network (dict): The queue network application.
        time (int): Number of time points to generate data for.
        main_lambda (int): The starting main_lambda value. 
        k (float): How long is the dependency of λ is. 
        alpha (float): How much λ is dependent on the previous time point.
        C (float): Constant 

    Returns:
        timeline (dict): Synthetic data.  
    """
    system = queue_network["system"]
    queues = system["queues"]
    entry_id = system["entry_points"]

    # Initialize backlog and lambda tracking
    backlog = {q["id"]: 0.0 for q in queues}
    main_lambdas = []
    timeline = []

    for t in range(time):
        curr_time = t + 1
        print(f"\nTime: {curr_time}")

        # Compute main lambda
        if curr_time == 1: 
            curr_main_lambda = main_lambda
            main_lambdas.append(curr_main_lambda)
        else: 
            curr_main_lambda = compute_curr_lambda(main_lambdas, k, alpha, C)
            curr_main_lambda = add_gaussian_noise(curr_main_lambda,gaussian_mean,gaussian_std)
            main_lambdas.append(curr_main_lambda)

        print("λ_main =", curr_main_lambda)

        # Compute queue lambdas (main λ + backlog)
        queue_lambdas = {}
        """
        # Old code for linear example...
        for q in queues:
            q_id = q["id"]
            queue_lambdas[q_id] = curr_main_lambda + backlog[q_id] # Setting each queue to main lambda plus any backlog
        """
        queue_lambdas = compute_queue_lambdas(curr_main_lambda, queues, entry_id)
        for q in queues:
            q_id = q["id"]
            queue_lambdas[q_id] += backlog[q_id]
        
        print("Queue λ values:", queue_lambdas)

        # Compute delays  
        delays = {}
        
        for q in queues: 
            q_id = q["id"]
            mu = q["service_rate"]
            lam = queue_lambdas[q_id]
            delays[q_id] = 1/(mu-lam) 

        # Compute served and update backlog
        served = {}
        new_backlog = {}

        for q in queues:
            q_id = q["id"]
            mu = q["service_rate"]
            lam = queue_lambdas[q_id]

            served[q_id] = min(mu, lam)
            new_backlog[q_id] = max(0, lam - mu)

        backlog = new_backlog

        print("Delays:", delays)
        print("Served:", served)
        print("Backlog:", backlog)

        # Record timestep summary
        timeline.append({
            "time": curr_time,
            "lambda_main": curr_main_lambda,
            "queue_lambdas": queue_lambdas,
            # "served": served, # Evenually remove
            # "backlog": backlog.copy(), # Evenually remove 
            "delays": delays
        })

    return timeline

# An example 
# k = 3
# alpha = 0.4
# print(generate_data(queue_network, 10, 0.1, k, alpha, 0.05))

def convert_data_to_csv(data, saved_file_path):
    df = pd.json_normalize(data)   # Flattens nested dictionaries
    df.to_csv(saved_file_path, index=False) # Output csv file



def run(QUEUE_NETWORK_FILE): # Feed in a queue network file
    # Load Data Generation Configurations
    cfg = config.get_config("dev_config.ini")
    data_gen_config = cfg['data_generation']
    stress_test_config = cfg['stress_test_params']

    # Extract parameters
    ALPHA = data_gen_config.getfloat("alpha")
    K = data_gen_config.getint("k")
    C = data_gen_config.getfloat("C")
    STARTING_MAIN_LAMBDA = data_gen_config.getfloat("starting_main_lambda")
    TIME_POINTS = data_gen_config.getint("time_points")
    GAUSSIAN_MEAN = data_gen_config.getfloat("gaussian_mean")
    GAUSSIAN_STD = data_gen_config.getfloat("gaussian_std")
    SEED = stress_test_config.getint("random_seed")
    # QUEUE_NETWORK_FILE = cfg.get("paths", "queueing_network_file") # Removed

    with open(QUEUE_NETWORK_FILE, 'r') as file:
        queue_network = json.load(file)

    # Testing with an example
    # data = generate_data(queue_network, 100, 0.1, k, alpha, 0.05)
    data = generate_data(
        assign_service_rates(queue_network, SEED),
        TIME_POINTS,
        STARTING_MAIN_LAMBDA,
        K,
        ALPHA,
        C,
        GAUSSIAN_MEAN,
        GAUSSIAN_STD
    )

    queue_file = Path(QUEUE_NETWORK_FILE) 
    queue_name = queue_file.stem # e.g, "queue_diverge_example"
    out_dir = cfg.get("paths", "processed_data_dir")
    out_path = Path(out_dir) / f"{queue_name}_data.csv"
    convert_data_to_csv(data, out_path)
    print("Saved to ",out_path)

    return f"{queue_name}_data.csv"