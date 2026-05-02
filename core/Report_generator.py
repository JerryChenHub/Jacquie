import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from core.DataLoader import load_combined_data

def creat_table():
    rename_map = {
        "Top rotor RPM": "RPM_T",
        "Bottom rotor RPM": "RPM_B",
        "Top rotor thrust (N)": "T_T",
        "Bottom rotor thrust (N)": "T_B",
        "x/Diameter": "x/D",
        "z/Diameter": "z/D",
        "Top rotor torque (Nm)":"Tau_T",
        "Bottom rotor torque (Nm)":"Tau_B",
        "Noise_RMS": "NRMS",
    }

    files = ["../data/combined6_fixed.csv",
             "../data/combined13_fixed.csv",
             "../data/combined40_fixed.csv"]

    with PdfPages("combined_tables_raw.pdf") as pdf:
        # for f in files:
        for i in [6,13,40]:
            # df = pd.read_csv(f)
            df = load_combined_data(i)

            df_fmt = df.copy()
            for col in df_fmt.select_dtypes(include="number").columns:
                if col not in ["Top rotor RPM","Bottom rotor RPM"]:
                    df_fmt[col] = df_fmt[col].map(lambda x: f"{x:.4f}")
            df_fmt.index = df_fmt.index.astype(str)  # index 转字符串

            df_fmt = df_fmt.rename(columns=rename_map)

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.axis("off")

            data = df_fmt.reset_index()
            tbl = ax.table(cellText=data.values,
                           colLabels=data.columns,
                           loc="center",
                           cellLoc="center")

            tbl.auto_set_font_size(False)
            tbl.set_fontsize(8)
            tbl.scale(1.2, 1.2)

            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)


def control_vatiable_plots():
    from Plotting.control_variable import plot_fix3_vary1_16
    params = [
        (40, (50, 100), True, False, False),
        (40, (0, 200), False, True, False),
        (40, (0, 5), False, False, True),
        (13, (50, 100), True, False, False),
        (13, (0, 200), False, True, False),
        (13, (0, 5), False, False, True),
        (6, (50, 100), True, False, False),
        (6, (0, 200), False, True, False),
        (6, (0, 5), False, False, True),
    ]

    with PdfPages("control_variable_plots.pdf") as pdf:
        for param in params:
            fig = plot_fix3_vary1_16("x/Diameter",
                                     param[0],
                                     ylim=param[1],
                                     noise=param[2],
                                     thrust=param[3],
                                     C_T=param[4])
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)

if __name__ == '__main__':
    control_vatiable_plots()