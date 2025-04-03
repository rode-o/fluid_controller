import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

def exp_grow_function(t, A, K, B, C):
    """
    Growing exponential function:
      f(t) = A + (K - A)*[1 - exp(-((t - C)/B))]
    
    As t -> large, f(t) -> K.
    As t -> C or below, f(t) -> near A.
    """
    return A + (K - A)*(1.0 - np.exp(-((t - C)/B)))

def exp_grow_derivative(t, A, K, B, C):
    """
    Derivative of the growing exponential w.r.t t:
      f'(t) = (K - A)*(1/B)*exp(-((t - C)/B))
    
    For t < C, (t - C) is negative => exponent is positive => big slope, etc.
    """
    return (K - A)*(1.0/B)*np.exp(-((t - C)/B))

def main():
    print("==== Exponential Growing Slope-Matching ====\n")

    # -----------------------------------------------------------------
    # 1) PRIMARY CURVE (Hard-coded)
    #    You can change A1, K1, B1, C1, T_ref as needed
    # -----------------------------------------------------------------
    A1 = 0.001     # lower bound
    K1 = 0.23    # upper bound
    B1 = 5.0     # "width" or "steepness"
    C1 = 0.0     # shift
    T_ref = 0.5  # reference point where we match derivatives

    # Slope of the primary at T_ref
    slope_primary = exp_grow_derivative(T_ref, A1, K1, B1, C1)

    # -----------------------------------------------------------------
    # 2) SECONDARY CURVE pinned to: A2=0, K2=1, C2=0, solve for B2
    #    so that derivative at T_ref matches slope_primary
    # -----------------------------------------------------------------
    A2 = 0.0
    K2 = 1.0
    C2 = 0.0  # pinned shift for the secondary

    def slope_equation(B2):
        # slope of f2 at T_ref minus slope_primary => zero means matched slopes
        slope2 = exp_grow_derivative(T_ref, A2, K2, B2, C2)
        return slope2 - slope_primary

    B2_guess = 1.0
    B2_solution = fsolve(slope_equation, B2_guess)[0]
    slope_secondary = exp_grow_derivative(T_ref, A2, K2, B2_solution, C2)

    print("=== Slope-Matching Results ===")
    print(f"Primary: A1={A1}, K1={K1}, B1={B1}, C1={C1}")
    print(f" T_ref = {T_ref}")
    print(f" Primary slope @T_ref = {slope_primary:.6f}")

    print(f"\nSecondary: A2={A2}, K2={K2}, B2={B2_solution:.6f}, C2={C2}")
    print(f" Secondary slope @T_ref = {slope_secondary:.6f}")

    # -----------------------------------------------------------------
    # 3) Plot both curves
    # -----------------------------------------------------------------
    t_min = -0.5  # can be negative if you want to see behavior, but be mindful if t<C
    t_max = 3.0
    t_vals = np.linspace(t_min, t_max, 400)

    # Evaluate both
    Y1_vals = exp_grow_function(t_vals, A1, K1, B1, C1)
    Y2_vals = exp_grow_function(t_vals, A2, K2, B2_solution, C2)

    # Plot
    plt.figure(figsize=(8, 5))
    plt.plot(t_vals, Y1_vals, label="Primary (A1,K1,B1,C1)")
    plt.plot(t_vals, Y2_vals, label="Secondary (A2,K2,B2,C2)")

    # Mark T_ref
    plt.axvline(T_ref, color='gray', linestyle='--', alpha=0.7, label=f"T_ref={T_ref}")
    Y1_ref = exp_grow_function(T_ref, A1, K1, B1, C1)
    Y2_ref = exp_grow_function(T_ref, A2, K2, B2_solution, C2)
    plt.scatter([T_ref], [Y1_ref], color='black', zorder=5, label="Primary slope match pt")
    plt.scatter([T_ref], [Y2_ref], color='red', zorder=5, label="Secondary slope match pt")

    plt.title("Primary & Secondary Growing Exponential, Slope-Matched at T_ref")
    plt.xlabel("t")
    plt.ylabel("f(t)")
    plt.xlim(t_min, t_max)
    plt.ylim(min(Y1_vals.min(), Y2_vals.min())-0.1, max(Y1_vals.max(), Y2_vals.max())+0.1)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
not really coding lollll