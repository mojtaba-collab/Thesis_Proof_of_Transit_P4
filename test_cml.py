
#!/usr/bin/env python3

import random

def generate_mersenne(mersenne_b):
    mersenne = (2 ** mersenne_b) - 1
    return mersenne





def generate_poly2(x_values, mersenne, random_value):
    p2_list = []
    for x in x_values:
        p2 = (random_value + x**3 + x**2 + x) 
        p2 = p2 % mersenne
        p2_list.append(p2)
    return p2_list, random_value





def generate_polynomial_points(secret, mersenne, x_values):
    coefficient = 3
    x_list = []
    y_list = []
    for x in x_values:
        poly1 = (secret + (coefficient*x + coefficient*x**2 + coefficient*x**3))
        y = poly1 % mersenne
        x_list.append(x)
        y_list.append(y)
    return x_list, y_list





def generate_lagrange(X, mersenne):
    LPCs = []
    for i in range(len(X)):
        numerator = 1
        denominator = 1
        for j in range(len(X)):
            if j != i:
                numerator *= (0 - X[j])
                denominator *= (X[i] - X[j])
        LPC = (numerator * pow(denominator, -1, mersenne)) % mersenne
        LPCs.append(LPC)
    return LPCs




def calc_cml(y, poly2, lpc, mersenne, mersenne_b, current_cml):
    new_cml = (y + poly2) * lpc
    new_cml = (new_cml & mersenne) + (new_cml >> mersenne_b)
    if new_cml > mersenne:
        new_cml = new_cml - mersenne
    new_cml = current_cml + new_cml
    return new_cml





def main():
    mersenne_b = 5
    secret = 10
    x_values_list = [1, 3, 5, 7]
    random_value = 69 #random.randint(1, 50)



    # Generate mersenne
    mersenne = generate_mersenne(mersenne_b)
    print(f"Mersenne = {mersenne}")
    print(f"Mersenne_b = {mersenne_b}")



    # Generate share of secret (X, Y)
    x, y = generate_polynomial_points(secret, mersenne, x_values_list)
    print(f"X values = {x}")
    print(f"Y values = {y}")



    # Compute LPC's
    lpc_output = generate_lagrange(x, mersenne)
    print(f"LPC = {lpc_output}")



    # Calculate Poly2 for CORE NODES / public polynomial / RND
    Poly2, rnd_value = generate_poly2(x_values_list, mersenne, random_value)
    print(f"Poly2 = {Poly2}")
    print(f"RND = {rnd_value}")



    # Calculate CML for each parameter
    current_cml = 0
    for i in range(len(x_values_list)):
        current_cml = calc_cml(y[i], Poly2[i], lpc_output[i], mersenne, mersenne_b, current_cml)
        print(f"CML after Core Switch {i+1}: {current_cml}")



    
    current_cml = current_cml % mersenne
    print(f"Final CML: {current_cml}")

if __name__ == "__main__":
    main()






