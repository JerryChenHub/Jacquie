import os
import numpy as np
import pandas as pd
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
from scipy.io import loadmat

def load_combined_data(diameter, data_dir="..\\data"):
    """
    Load operating parameters and noise data for a given propeller diameter,
    and return a combined pandas DataFrame.

    Parameters:
    - diameter: int or str, one of 6, 13, or 40, corresponding to oparray files
    - data_dir: str, path to directory containing .mat files

    Returns:
    - df_combined: pandas DataFrame, columns include:
        ['Top rotor RPM', 'Bottom rotor RPM', 'x/Diameter', 'z/Diameter',
         'Top rotor thrust (N)', 'Bottom rotor thrust (N)',
         'Top rotor torque (Nm)', 'Bottom rotor torque (Nm)',
         'Mic1', 'Mic2', ..., 'MicM']
      and rows indexed by sample number.
    """
    # 1) Load operating parameters
    oparray_path = os.path.join(data_dir, f"oparray{diameter}.mat")
    mat_ops = loadmat(oparray_path)
    key_ops = next(k for k in mat_ops if k.startswith('oparray'))
    oparray = mat_ops[key_ops]
    op_cols = [
        "Top rotor RPM", "Bottom rotor RPM",
        "x/Diameter",   "z/Diameter",
        "Top rotor thrust (N)", "Bottom rotor thrust (N)",
        "Top rotor torque (Nm)", "Bottom rotor torque (Nm)"
    ]
    df_ops = pd.DataFrame(oparray, columns=op_cols)


    noise_mat = loadmat(os.path.join(data_dir, "Noise.mat"))
    bot_key  = f"micdatBot{diameter}"
    top_key  = f"micdatTop{diameter}"
    both_key = f"micdatBoth{diameter}"
    n_bot  = noise_mat.get(bot_key)
    n_top  = noise_mat.get(top_key)
    n_both = noise_mat.get(both_key)
    if n_bot is None or n_top is None or n_both is None:
        raise KeyError(f"Noise data for diameter {diameter} not found in Noise.mat")

    mic_names = [f"Mic{i+1}" for i in range(n_bot.shape[1])]
    df_bot  = pd.DataFrame(n_bot,  columns=mic_names)
    df_top  = pd.DataFrame(n_top,  columns=mic_names)
    df_both = pd.DataFrame(n_both, columns=mic_names)
    df_noise = df_bot.combine_first(df_top).combine_first(df_both)

    df_combined = pd.concat([df_ops, df_noise], axis=1)
    df_combined.index.name = 'Sample'
    return df_combined


def pi_data(diameters,log_features=False):
    """
    Combined the required data into one dataset
    :param diameters: Diameters of the dataset needed to be combined
    :return: Combined dataset with pi-columns
    """
    df_list = []
    rho = 1.225  # kg/m3
    a = 340.3    # m/s
    nu = 1.5e-5  # m2/s
    for D_cm in diameters:
        df = load_combined_data(D_cm)
        df["Prop_Dia"]=D_cm
        df = df[(df['Top rotor RPM'] > 0) & (df['Bottom rotor RPM'] > 0)].copy()

        mic_cols = [c for c in df.columns if c.startswith('Mic')]
        df['Noise_RMS'] = np.sqrt((df[mic_cols]**2).mean(axis=1))
        df['Omega_top'] = 2 * np.pi * df['Top rotor RPM'] / 60.0
        df['Omega_bot'] = 2 * np.pi * df['Bottom rotor RPM'] / 60.0
        D = D_cm/100
        R = D_cm / 2.0 /100
        # π1: M_tip_top, M_tip_bot
        df['M_tip_top'] = df['Omega_top'] * R / a
        df['M_tip_bot'] = df['Omega_bot'] * R / a
        # π2: C_T_top, C_T_bot
        A = np.pi * R**2
        df['C_T_top'] = df['Top rotor thrust (N)'] / (rho * A * (df['Omega_top']*R)**2)
        df['C_T_bot'] = df['Bottom rotor thrust (N)'] / (rho * A * (df['Omega_bot']*R)**2)
        # π3: C_Q_top, C_Q_bot
        n_top_rps = df['Top rotor RPM'] / 60.0
        n_bot_rps = df['Bottom rotor RPM'] / 60.0
        df['C_Q_top'] = df['Top rotor torque (Nm)'] / (rho * n_top_rps**2 * D**5)
        df['C_Q_bot'] = df['Bottom rotor torque (Nm)'] / (rho * n_bot_rps**2 * D**5)
        # π5: Re_top, Re_bot
        df['Re_top'] = df['Omega_top'] * R**2 / nu
        df['Re_bot'] = df['Omega_bot'] * R**2 / nu
        # π6/7: x_D, z_D
        df.rename(columns={'x/Diameter':'x_D','z/Diameter':'z_D'}, inplace=True)
        # π9: phi ratio
        df['phi'] = df['Top rotor RPM'] / df['Bottom rotor RPM']
        # π10: invT_top, invT_bot
        df['invT_top'] = (rho * a**2 * D**2) / df['Top rotor thrust (N)']
        df['invT_bot'] = (rho * a**2 * D**2) / df['Bottom rotor thrust (N)']
        pi_cols = [
            'M_tip_top','M_tip_bot',
            'C_T_top','C_T_bot',
            'C_Q_top','C_Q_bot',
            'Re_top','Re_bot',
            'x_D','z_D','phi',
            'invT_top','invT_bot'
        ]
        for col in pi_cols:
            df[col] = df[col].replace(0, np.nan)
            if log_features:
                df[f'log_{col}'] = np.log(df[col])
        required = ['Noise_RMS'] + [f'log_{c}' for c in pi_cols]
        df_list.append(df.dropna(subset=required))
    return pd.concat(df_list, ignore_index=True)


if __name__ == '__main__':
    df = load_combined_data(40)
    print(df.sort_values(by="Top rotor thrust (N)",ascending=True))

    df = pd.read_csv("../data/combined40_fixed.csv")
    print(df.sort_values(by="Top rotor thrust (N)",ascending=True))