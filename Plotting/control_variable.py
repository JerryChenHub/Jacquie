import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from core.DataLoader import load_combined_data


def _dominant_two_values(v: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Return: centers_used[2] (for distance), labels (0/1),
            centers_display[2] (most frequent actual values in each cluster).
    Zeros are ignored for clustering but included for labeling distance assignment.
    """
    v = np.asarray(v, dtype=float)
    if v.size == 0:
        return np.array([np.nan, np.nan]), np.zeros(0, dtype=int), np.array([np.nan, np.nan])

    nz = v[v != 0]
    if nz.size == 0:
        centers = np.array([0.0, 0.0])
        labels = np.zeros_like(v, dtype=int)
        return centers, labels, centers

    vmin, vmax = np.min(nz), np.max(nz)
    if vmin == vmax:
        centers = np.array([vmin, vmax])
        labels = (np.abs(v - centers[1]) < np.abs(v - centers[0])).astype(int)
        # display centers use the exact repeated value
        return np.sort(centers), labels, np.sort(centers)

    # histogram to get two peaks
    n = nz.size
    q75, q25 = np.percentile(nz, [75, 25])
    iqr = max(q75 - q25, 1e-9)
    width = 2 * iqr / (n ** (1/3))
    if width <= 0 or not np.isfinite(width):
        width = max((vmax - vmin) / 10.0, 1.0)
    bins = int(np.clip(np.ceil((vmax - vmin) / width), 2, 50))
    hist, edges = np.histogram(nz, bins=bins)
    top2 = np.argsort(hist)[-2:]
    centers = 0.5 * (edges[top2] + edges[top2 + 1])
    centers = np.sort(centers.astype(float))

    # assign labels by nearest center
    labels = (np.abs(v - centers[1]) < np.abs(v - centers[0])).astype(int)

    # compute display centers as modes of actual values within each cluster (non-zero only)
    def cluster_mode(actual):
        if actual.size == 0:
            return np.nan
        vals, cnts = np.unique(actual, return_counts=True)
        mx = np.max(cnts)
        cand = vals[cnts == mx]
        if cand.size == 1:
            return float(cand[0])
        # tie-breaker: pick candidate closest to cluster median
        med = float(np.median(actual))
        return float(cand[np.argmin(np.abs(cand - med))])

    nz_labels = labels[v != 0]
    disp0 = cluster_mode(nz[nz_labels == 0])
    disp1 = cluster_mode(nz[nz_labels == 1])
    centers_disp = np.array([disp0, disp1], dtype=float)

    # enforce ascending order for display centers; flip if needed
    if np.isfinite(centers_disp).all() and centers_disp[0] > centers_disp[1]:
        labels = 1 - labels
        centers = centers[::-1]
        centers_disp = centers_disp[::-1]

    return centers, labels, centers_disp

def thrust_to_ct(T, rpm, diameter_m, rho=1.225):
    # T: ndarray (N), rpm: ndarray, diameter_m: float (meters)
    n = rpm / 60.0  # rev/s
    D = float(diameter_m)
    return T / (rho * (n**2) * (D**4))

def plot_fix3_vary1_16(vary_col: str, diameter: int = 13, ylim=None, noise=False, thrust=False, C_T=False):
    """
    Single-function plotter. vary_col ∈ {"x/Diameter", "z/Diameter"}.
    4×4 grid; zeros are excluded; RPM clustered to two non-zero modes;
    subplot curves: Noise_RMS, Top thrust, Bottom thrust.
    """
    assert vary_col in ("x/Diameter", "z/Diameter"), "vary_col must be 'x/Diameter' or 'z/Diameter'."

    # df = load_combined_data(diameter)
    df = pd.read_csv(f"../data/combined{diameter}_fixed.csv")

    def col(name):
        return np.asarray(df[name])

    mic_cols = [c for c in getattr(df, "columns", []) if isinstance(c, str) and c.startswith("Mic")]
    if len(mic_cols) == 0:
        raise RuntimeError("No Mic* columns found; cannot compute Noise_RMS.")

    mic_stack_full = np.column_stack([col(c) for c in mic_cols]).astype(float)
    noise_rms_full = np.sqrt(np.mean(mic_stack_full ** 2, axis=1))

    top_rpm_full = col("Top rotor RPM").astype(float)
    bot_rpm_full = col("Bottom rotor RPM").astype(float)
    xD_full = col("x/Diameter").astype(float)
    zD_full = col("z/Diameter").astype(float)
    top_thrust_full = col("Top rotor thrust (N)").astype(float)
    bot_thrust_full = col("Bottom rotor thrust (N)").astype(float)
    vary_full = col(vary_col).astype(float)

    D_m = diameter / 100.0

    # exclude zero-RPM rows for plotting
    keep = (top_rpm_full != 0) & (bot_rpm_full != 0)
    if not np.any(keep):
        raise RuntimeError("All rows have Top or Bottom RPM equal to 0; nothing to plot.")

    noise_rms = noise_rms_full[keep]
    top_rpm_raw = top_rpm_full[keep]
    bot_rpm_raw = bot_rpm_full[keep]
    xD = xD_full[keep]
    zD = zD_full[keep]
    top_thrust = top_thrust_full[keep]
    bot_thrust = bot_thrust_full[keep]
    vary = vary_full[keep]

    # --- FIX 1: get row-levels from FULL dataset (not filtered), round to stabilize floats
    other_geo = "z/Diameter" if vary_col == "x/Diameter" else "x/Diameter"
    full_other = zD_full if other_geo == "z/Diameter" else xD_full
    other_vals_all = np.unique(np.round(full_other.astype(float), 6))
    # if other_vals_all.size == 0:
    #     raise RuntimeError(f"{other_geo} has no valid levels.")
    # if other_vals_all.size < 4:
    #     other_vals = np.concatenate([other_vals_all, np.repeat(other_vals_all[-1], 4 - other_vals_all.size)])
    # else:
    #     other_vals = np.sort(other_vals_all)[:4]

    if other_vals_all.size == 0:
        raise RuntimeError(f"{other_geo} has no valid levels.")
    other_vals = np.sort(other_vals_all)[:4]
    n_rows = len(other_vals)

    # cluster RPM (unchanged)
    top_centers, top_lbl, top_disp = _dominant_two_values(top_rpm_raw)
    bot_centers, bot_lbl, bot_disp = _dominant_two_values(bot_rpm_raw)

    rpm_pairs = [(0, 0), (0, 1), (1, 0), (1, 1)]

    a = 340.3  # m/s
    R = (diameter / 100) / 2.0
    def rpm_to_mach(rpm):
        omega = 2 * np.pi * rpm / 60.0
        return omega * R / a
    top_mach = [rpm_to_mach(r) for r in top_disp]
    bot_mach = [rpm_to_mach(r) for r in bot_disp]

    # fig, axes = plt.subplots(4, 4, figsize=(16, 16), sharex=True)
    fig, axes = plt.subplots(n_rows, 4, figsize=(16, 4 * n_rows), sharex=True)
    fig.suptitle(
        f"D={diameter} | Vary: {vary_col}\n"
        f"(Top≈{top_disp[0]:.0f}/{top_disp[1]:.0f} rpm"
        f"M_tip≈{top_mach[0]:.3f}/{top_mach[1]:.3f}; "
        f"Bottom≈{bot_disp[0]:.0f}/{bot_disp[1]:.0f} rpm, "
        f"M_tip≈{bot_mach[0]:.3f}/{bot_mach[1]:.3f})",
        y=0.94,fontsize=18
    )

    # --- FIX 2: derive vary levels from FULL vector and round (optional, safer domain)
    vary_levels_all = np.unique(np.round(vary_full, 6))
    try:
        vary_levels_sorted = np.sort(vary_levels_all.astype(float))
    except Exception:
        vary_levels_sorted = np.sort(vary_levels_all)

    for i_row, og_val in enumerate(other_vals):
        for i_col, (t_lbl, b_lbl) in enumerate(rpm_pairs):
            ax = axes[i_row, i_col]

            # --- FIX 3: use isclose to match the row-level instead of exact ==
            if other_geo == "x/Diameter":
                mask = (top_lbl == t_lbl) & (bot_lbl == b_lbl) & np.isclose(xD, og_val, rtol=0, atol=1e-6)
            else:
                mask = (top_lbl == t_lbl) & (bot_lbl == b_lbl) & np.isclose(zD, og_val, rtol=0, atol=1e-6)

            if not np.any(mask):
                ax.set_title(
                    f"{other_geo}={og_val:.3f}, Top≈{top_disp[t_lbl]:.0f}, Bot≈{bot_disp[b_lbl]:.0f}\n(no samples)",
                    fontsize=9
                )
                ax.grid(True, linestyle="--", alpha=0.3)
                continue

            means_noise, means_topF, means_botF = [], [], []
            stds_noise, stds_topF, stds_botF = [], [], []
            xs = []
            for xv in vary_levels_sorted:
                # --- FIX 4: isclose for vary matching
                sub = mask & np.isclose(vary, xv, rtol=0, atol=1e-6)
                if np.any(sub):
                    xs.append(float(xv))
                    means_noise.append(float(np.mean(noise_rms[sub])))
                    means_topF.append(float(np.mean(top_thrust[sub])))
                    means_botF.append(float(np.mean(bot_thrust[sub])))
                    stds_noise.append(float(np.std(noise_rms[sub])))
                    stds_topF.append(float(np.std(top_thrust[sub])))
                    stds_botF.append(float(np.std(bot_thrust[sub])))

            xs = np.array(xs, dtype=float) if len(xs) > 0 else np.array([])
            if xs.size == 0:
                ax.set_title(
                    f"{other_geo}={og_val:.3f}, Top≈{top_disp[t_lbl]:.0f}, Bot≈{bot_disp[b_lbl]:.0f}\n(no matching levels)",
                    fontsize=9
                )
                ax.grid(True, linestyle="--", alpha=0.3)
                continue

            if noise:
                ax.errorbar(xs, means_noise, yerr=stds_noise, marker="o", label="Noise_RMS")

            if thrust:
                ax.errorbar(xs, means_topF, yerr=stds_topF, marker="s", label="Top thrust (N)")
                ax.errorbar(xs, means_botF, yerr=stds_botF, marker="^", label="Bottom thrust (N)")

            if C_T:
                ax.plot(xs, thrust_to_ct(means_topF, np.full(len(xs), top_disp[t_lbl]), D_m),
                        marker="o", linestyle="-", label="Top C_T")
                ax.plot(xs, thrust_to_ct(means_botF, np.full(len(xs), bot_disp[t_lbl]), D_m),
                        marker="o", linestyle="-", label="Bot C_T")

            if ylim:
                ax.set_ylim(ylim)
            ax.grid(True, linestyle="--", alpha=0.3)


            ax.set_title(
                f"{other_geo}={og_val:.3f}, Top≈{top_disp[t_lbl]:.0f}, Bot≈{bot_disp[b_lbl]:.0f}",
                fontsize=9
            )
            if i_row == 3:
                ax.set_xlabel(vary_col)
            if i_col == 0:
                pass
            if i_row == 0 and i_col == 0:
                ax.legend(fontsize=8, loc="best")

    return fig

if __name__ == '__main__':
    fig=plot_fix3_vary1_16("x/Diameter",40, noise=True)
    fig.show()