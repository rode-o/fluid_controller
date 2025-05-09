import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brentq

# ── Firmware‑style parameters ────────────────────────────────────────────────
EXP_KI_A  = 0.001             # primary A1
EXP_KI_K  = 0.23              # primary K1
EXP_KI_B  =100.0              # primary B1

FILTER_T_REF        = 0.05   # slope‑match reference |error|

FILTER_SECONDARY_A2 = 0.0     # secondary A2 (pinned)
FILTER_SECONDARY_K2 = 0.5     # secondary K2 (pinned)

SEARCH_LOW_B  = 1e-3          # bracketing range for B2
SEARCH_HIGH_B = 1e+2
# ─────────────────────────────────────────────────────────────────────────────

def dfdx(t, A, K, B):
    """Derivative of A+(K‑A)*exp(‑1/(B*t)) wrt t (same as firmware)."""
    t = np.asarray(t)
    mask = t > 1e-9
    return np.where(
        mask,
        (K - A)*np.exp(-1.0/(B*t), where=mask)/(B*t**2),
        0.0
    )

# Primary slope at T_REF ------------------------------------------------------
slope_primary = dfdx(FILTER_T_REF, EXP_KI_A, EXP_KI_K, EXP_KI_B)

# Solve B2 so that slope_secondary == slope_primary --------------------------
def slope_diff(B):
    return dfdx(FILTER_T_REF,
                FILTER_SECONDARY_A2,
                FILTER_SECONDARY_K2,
                B) - slope_primary

# Find a bracket that changes sign -------------------------------------------
B_candidates = np.logspace(np.log10(SEARCH_LOW_B), np.log10(SEARCH_HIGH_B), 400)
signs = np.sign(slope_diff(B_candidates))
# locate first sign change
bracket = None
for lo, hi, s_lo, s_hi in zip(B_candidates[:-1], B_candidates[1:],
                              signs[:-1], signs[1:]):
    if s_lo == 0:
        bracket = (lo, lo)  # exact root
        break
    if s_lo * s_hi < 0:
        bracket = (lo, hi)
        break

if bracket is None:
    raise RuntimeError("Could not bracket a root for B2 in the search range")

B2 = brentq(slope_diff, *bracket)
print(f"Solved B₂ = {B2:.6f}   (bracket {bracket[0]:.3g}–{bracket[1]:.3g})")

# Primary & secondary curves --------------------------------------------------
def f_primary(t):
    d = EXP_KI_B * t
    return np.where(d > 0,
                    EXP_KI_A + (EXP_KI_K - EXP_KI_A)*np.exp(-1.0/d, where=d>0),
                    EXP_KI_K)

def f_secondary(t):
    d = B2 * t
    return np.where(d > 0,
                    FILTER_SECONDARY_A2
                    + (FILTER_SECONDARY_K2 - FILTER_SECONDARY_A2)
                      * np.exp(-1.0/d, where=d>0),
                    FILTER_SECONDARY_K2)

# Plot -----------------------------------------------------------------------
x = np.linspace(1e-4, 0.2, 500)  # domain of interest (>0 avoids divide‑by‑0)
y1, y2 = f_primary(x), f_secondary(x)

plt.figure(figsize=(8,5))
plt.plot(x, y1,
         label=rf"Primary $f_1$ (A={EXP_KI_A:g}, K={EXP_KI_K:g}, B={EXP_KI_B:g})")
plt.plot(x, y2,
         label=rf"Secondary $f_2$ (A={FILTER_SECONDARY_A2:g}, "
               rf"K={FILTER_SECONDARY_K2:g}, B={B2:.3f})")

plt.axvline(FILTER_T_REF, ls='--', c='grey', label=rf"$T_{{REF}}$ = {FILTER_T_REF}")
plt.scatter([FILTER_T_REF], [f_primary(FILTER_T_REF)],
            c='black', zorder=5, label="slope‑match point")

plt.title("Firmware dynamic‑LP filter curves (primary vs secondary)")
plt.xlabel("|error|  (t)")
plt.ylabel("f(t)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
