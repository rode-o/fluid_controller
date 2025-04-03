import numpy as np
import matplotlib.pyplot as plt

def custom_exp(t, A, K, B, c):
    """
    Custom function:
      f(t) = A + (K - A)*exp( -1 / [B * (t - c)] )
    """
    return A + (K - A) * np.exp(-1.0 / (B * (t - c)))

# Example parameters
A = 0.001  # lower bound
K = 0.023   # upper bound
B = 100  # "steepness" factor in the exponent
c = 0  # shift to control the position

# Time range
t = np.linspace(0.0, 0.03, 1000)

# Evaluate custom function
f = custom_exp(t, A, K, B, c)

# Plot
plt.plot(t, f, label='Custom Exponential Curve')
plt.axvline(c, linestyle='--', label=f'c = {c}')

plt.xlabel('Time')
plt.ylabel('f(t)')
plt.title('Custom Exponential Function Example')
plt.legend()
plt.show()
