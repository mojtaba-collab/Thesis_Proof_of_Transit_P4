





import random
import numpy as np
import sys

# --- Default Constants for the PoT-PolKA Path (Adjust as needed) ---
DEFAULT_MERSENNE_B = 5
DEFAULT_SECRET_SEED = 10 
POLYNOMIAL_COEFFICIENT = 3 
# We calculate the fixed Mersenne modulus once here, assuming the default B=5
MERSENNE_MODULUS = (2 ** DEFAULT_MERSENNE_B) - 1

# --- PoT SSSS Policy/Policy Calculation Functions (Based on your original code) ---
    
def generate_mersenne(mersenne_b):
    """Generate a Mersenne prime based on the given mersenne_b value."""
    return (2 ** mersenne_b) - 1


def generate_polynomial_points(mersenne, x_values, secret_seed=DEFAULT_SECRET_SEED, coefficient=POLYNOMIAL_COEFFICIENT):
    """
    Generate Poly1 points (X, Y) which are the 'shares' of the secret.
    
    Poly1(x) = Secret_Seed + c*x + c*x^2 + c*x^3 (mod M)
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
        
        # Ensure denominator is non-zero and invertible
        denominator %= mod
        if denominator == 0:
            print(f"Error: Non-invertible zero denominator for X[{i}]={X[i]}", file=sys.stderr)
            lpc_list.append(0)
            continue
            
        # Calculates (numerator * denominator^-1) mod M 
        LPC = (numerator * pow(denominator, -1, mod)) % mod
        lpc_list.append(LPC)
        
    return lpc_list


def generate_cml_step(y, poly2, lpc, mersenne, mersenne_b, current_cml):
    """
    Performs the CML update step, simulating the P4 logic in the data plane 
    to confirm the final expected CML value.
    """
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

if __name__ == '__main__':
    
    # --- TEST INPUTS ---
    X_VALUES_FORWARD = [1, 3, 5, 7]
    X_VALUES_REVERSE = [7, 5, 3, 1]
    
    # You can change these values to test different scenarios:
    TEST_MERSENNE_B = 5
    TEST_RND_FORWARD = 50
    TEST_RND_REVERSE = 50
    TEST_SECRET_SEED = 10
    
    print("=" * 70)
    print("           PoT/PolKA Secret Calculator Test")
    print("=" * 70)
    print(f"Constants: MERSENNE_B={TEST_MERSENNE_B}, Modulus M={generate_mersenne(TEST_MERSENNE_B)}")
    print(f"Secret Seed: {TEST_SECRET_SEED}, Polynomial Coeff: {POLYNOMIAL_COEFFICIENT}")
    print("-" * 70)
    
    
    # --- A. FORWARD PATH TEST (X = [1, 3, 5, 7]) ---
    
    forward_results = calculate_path_secrets_set(
        x_values=X_VALUES_FORWARD, 
        mersenne_b=TEST_MERSENNE_B, 
        random_value=TEST_RND_FORWARD,
        secret_seed=TEST_SECRET_SEED
    )
    
    # Print results in a table format
    print(f"Expected Final CML: {forward_results['expected_final_cml']}")
    print("Core Node Shares:")
    print("  | X |   Y | LPC | Poly2 |")
    print("  |---|-----|-----|-------|")
    for secret in forward_results['core_node_secrets']:
        print(f"  | {secret['x']:1} | {secret['y']:3} | {secret['lpc']:3} | {secret['poly2']:5} |")

    
    # --- B. REVERSE PATH TEST (X = [7, 5, 3, 1]) ---
    
    reverse_results = calculate_path_secrets_set(
        x_values=X_VALUES_REVERSE, 
        mersenne_b=TEST_MERSENNE_B, 
        random_value=TEST_RND_REVERSE,
        secret_seed=TEST_SECRET_SEED
    )

    # Print results in a table format
    print(f"Expected Final CML: {reverse_results['expected_final_cml']}")
    print("Core Node Shares:")
    print("  | X |   Y | LPC | Poly2 |")
    print("  |---|-----|-----|-------|")
    for secret in reverse_results['core_node_secrets']:
        print(f"  | {secret['x']:1} | {secret['y']:3} | {secret['lpc']:3} | {secret['poly2']:5} |")
