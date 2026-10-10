

import random
import numpy as np







DEFAULT_SECRET_SEED = 10 
POLYNOMIAL_COEFFICIENT = 3 


def generate_mersenne(mersenne_b):
    return (2 ** mersenne_b) - 1









def generate_polynomial_points(mersenne, x_values, secret_seed=DEFAULT_SECRET_SEED, coefficient=POLYNOMIAL_COEFFICIENT):
    """
    Generate Poly1 points (X, Y) which are the 'shares' of the secret.
    
    Poly1(x) = Secret_Seed + c*x + c*x^2 + c*x^3 (mod M)
    
    Args:
        mersenne (int): The Mersenne prime used for modular arithmetic.
        x_values (list): List of x-coordinates (node identities for SSSS).

    Returns:
        tuple: Two lists containing x and y coordinates of the generated points.
    """
    x_list = []
    y_list = []
    
    for x in x_values:
        # Your original controller logic for Poly1:
        poly1_value = (secret_seed + (coefficient * x + coefficient * x**2 + coefficient * x**3))
        
        y = poly1_value % mersenne
        x_list.append(x)
        y_list.append(y)
        
    return x_list, y_list







def generate_poly2(x_values, mersenne, random_value):
    """
    Generate Poly2 values (shares of the public polynomial) for Core Nodes.
    
    Poly2(x) = Random_Value + x + x^2 + x^3 (mod M)
    
    Args:
        x_values (list): List of x-coordinates.
        mersenne (int): The Mersenne prime used for modular arithmetic.
        random_value (int): A public random value (RND) set by the edge.

    Returns:
        list: List of generated Poly2 values.
    """
    poly2_list = []
    for x in x_values:
        # Your original controller logic for Poly2:
        p2 = (random_value + x**3 + x**2 + x) 
        p2 = p2 % mersenne
        poly2_list.append(p2)
    
    return poly2_list








def generate_lagrange(X, mersenne):
    """
    Generate Lagrange polynomial coefficients (LPC's) for secret reconstruction.
    
    Args:
        X (list): List of x-coordinates.
        mersenne (int): The Mersenne prime used for modular arithmetic.

    Returns:
        list: List of Lagrange polynomial coefficients (LPC).
    """
    lpc_list = []
    mod = mersenne
    
    for i in range(len(X)):
        numerator = 1
        denominator = 1
        
        for j in range(len(X)):
            if j != i:
                numerator *= (0 - X[j])
                denominator *= (X[i] - X[j])
        
        # Calculates (numerator * denominator^-1) mod M 
        LPC = (numerator * pow(denominator, -1, mod)) % mod
        lpc_list.append(LPC)
        
    return lpc_list







def generate_cml_step(y, poly2, lpc, mersenne, mersenne_b, current_cml):
    """
    Performs the CML update step, simulating the P4 logic in the data plane 
    to confirm the final expected CML value.
    
    CML_new = (CML_old + (Poly1(X) + Poly2(X)) * LPC) mod M
    
    Args:
        y (int): Poly1(X) value (the 'Y' share).
        poly2 (int): Poly2(X) value.
        lpc (int): Lagrange polynomial constant.
        mersenne (int): Modulus M.
        mersenne_b (int): Exponent B.
        current_cml (int): The CML value entering this hop.

    Returns:
        int: The CML value after this step (before the final modulo).
    """
    # Note: This block mirrors the P4 switch logic for modulo operations.
    
    # Step 1: new_cml = (y + poly2) * lpc
    new_cml = (y + poly2) * lpc
    
    # Step 2: Apply Mersenne Modulo Trick (simulating P4)
    new_cml = (new_cml & mersenne) + (new_cml >> mersenne_b)
    
    if new_cml > mersenne:
        new_cml = new_cml - mersenne
        
    # Step 3: Final CML summation 
    new_cml_final = current_cml + new_cml
    
    return new_cml_final






def secret_reconstruction(y_values, lpc_values, mod):
    """
    Calculates the final CML value using the shares and constants.
    (This is functionally redundant with the final part of calculate_path_secrets_set 
    but kept for completeness based on your original file).
    """
    cml = 0
    for i in range(len(y_values)):
        y = y_values[i]
        lpc = lpc_values[i]
        cml = (cml + y * lpc) % mod
    return cml







def calculate_path_secrets_set(x_values, mersenne_b, random_value, secret_seed=DEFAULT_SECRET_SEED):
    """
    Calculates and aggregates all the necessary secrets for an entire path.
    This is the main API for the SDN controller.
    
    Args:
        x_values (list): The list of X-coordinates for the path (one per core node).
        mersenne_b (int): The exponent B.
        random_value (int): The RND value (constant coefficient of Poly2).
        secret_seed (int): The fixed secret coefficient of Poly1.

    Returns:
        dict: A comprehensive dictionary containing all parameters for 
              programming the switches and verification.
    """
    
    # 1. Calculate Mersenne Modulus
    mersenne = generate_mersenne(mersenne_b)
    
    # 2. Generate shares and constants
    x_list, y_list = generate_polynomial_points(mersenne, x_values, secret_seed=secret_seed)
    poly2_list = generate_poly2(x_list, mersenne, random_value)
    lpc_list = generate_lagrange(x_values, mersenne)

    # 3. Calculate the expected FINAL CML for Egress Verification
    current_cml = 0
    for i in range(len(x_list)):
        current_cml = generate_cml_step(y_list[i], poly2_list[i], lpc_list[i], mersenne, mersenne_b, current_cml)
            
    # The expected CML is the final accumulated value modulo M.
    expected_final_cml = current_cml % mersenne
    
    # 4. Aggregate Core Node Secrets for P4 programming
    core_node_secrets = []
    for i in range(len(x_list)):
        core_node_secrets.append({
            "x": x_list[i],
            "y": y_list[i],
            "lpc": lpc_list[i],
            "poly2": poly2_list[i],
        })
        
    return {
        "mersenne": mersenne,
        "mersenne_b": mersenne_b,
        "secret_seed": secret_seed,
        "random_value": random_value,
        "expected_final_cml": expected_final_cml,
        "core_node_secrets": core_node_secrets
    }






