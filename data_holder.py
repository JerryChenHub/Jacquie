import numpy as np
import pandas as pd
from scipy.spatial.distance import euclidean
from itertools import product
from scipy.io import loadmat
from scipy.optimize import minimize
from itertools import combinations
from scipy.spatial.distance import euclidean


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.float_format', '{:.5e}'.format)
np.seterr(divide='ignore', invalid='ignore')

class Data():
    def __init__(self,index):
        self._index=index

        d=loadmat(f"data/oparray{index}.mat")[f"oparray{index}"]
        oparray_columns = [
            "Top rotor RPM",
            "Bottom rotor RPM",
            "x/Diameter of the two rotors",
            "z/Diameter of the two rotors",
            "Top rotor thrust (N)",
            "Bottom rotor thrust (N)",
            "Top rotor torque (Nm)",
            "Bottom rotor torque (Nm)"
        ]
        self.df_oparray = pd.DataFrame(d, columns=oparray_columns)

        n_bot = loadmat("data/Noise.mat")[f"micdatBot{index}"]
        n_top = loadmat("data/Noise.mat")[f"micdatTop{index}"]
        n_both = loadmat("data/Noise.mat")[f"micdatBoth{index}"]
        noise_columns = [f"Mic{i + 1}" for i in range(n_bot.shape[1])]

        df_bot = pd.DataFrame(n_bot, columns=noise_columns)
        df_top = pd.DataFrame(n_top, columns=noise_columns)
        df_both = pd.DataFrame(n_both, columns=noise_columns)

        self.df_noise = df_bot.combine_first(df_top).combine_first(df_both)

        self.D=index   #SI unit
        self.rho=1.225  #air density
        self.a=340.3    #air speed

        top_rpm = self.df_oparray["Top rotor RPM"]
        bot_rpm = self.df_oparray["Bottom rotor RPM"]

        self.top_only_idx = np.where((top_rpm != 0) & (bot_rpm == 0))[0]
        self.bot_only_idx = np.where((top_rpm == 0) & (bot_rpm != 0))[0]
        self.both_on_idx = np.where((top_rpm != 0) & (bot_rpm != 0))[0]

        self.calc_parameters()

    def calc_parameters(self):
        """
        Calculate possible related quantity
        :return:
        """
        R = self.D / 2
        A = np.pi * R ** 2

        RPM_top = self.df_oparray["Top rotor RPM"].values
        Omega_top = 2 * np.pi * RPM_top / 60
        tip_speed_top = Omega_top * R
        self.M_HT_top = tip_speed_top / self.a
        T_top = self.df_oparray["Top rotor thrust (N)"].values
        self.C_T_top = T_top / (self.rho * A * tip_speed_top**2)
        # Q_top = self.df_oparray["Top rotor torque (Nm)"].values
        # self.C_Q_top = Q_top / (self.rho * A * R * tip_speed_top**2)

        RPM_bot = self.df_oparray["Bottom rotor RPM"].values
        Omega_bot = 2 * np.pi * RPM_bot / 60
        tip_speed_bot = Omega_bot * R
        self.M_HT_bot = tip_speed_bot / self.a
        T_bot = self.df_oparray["Bottom rotor thrust (N)"].values
        self.C_T_bot = T_bot / (self.rho * A * tip_speed_bot ** 2)
        # Q_bot = self.df_oparray["Bottom rotor torque (Nm)"].values
        # self.C_Q_bot = Q_bot / (self.rho * A * R * tip_speed_bot ** 2)


    def get_dimensionless_dataframe(self, idx=None):
        if idx is None:
            idx = self.both_on_idx
        noise_vectors = self.df_noise.iloc[idx].values.tolist()
        df = pd.DataFrame({
            "Index": idx,
            "Dataset(Diameter)": f"{self._index}",
            "Top M_HT": self.M_HT_top[idx],
            "Bottom M_HT": self.M_HT_bot[idx],
            "Top C_T": self.C_T_top[idx],
            "Bottom C_T": self.C_T_bot[idx],
            "x/Diameter": self.df_oparray.loc[idx, "x/Diameter of the two rotors"].values,
            "z/Diameter": self.df_oparray.loc[idx, "z/Diameter of the two rotors"].values,
            "Noise Vector": noise_vectors
        })
        return df

class FunctionFinder:
    def __init__(self, data_list):
        self.data_list = data_list  # list of Data objects
        self.X, self.Y = self.prepare_data()

    def prepare_data(self):
        X_list, Y_list = [], []
        for data in self.data_list:
            df = data.get_dimensionless_dataframe()
            X = np.column_stack([
                df["Top C_T"],
                df["Bottom C_T"],
                df["Top M_HT"],
                df["Bottom M_HT"],
                df["x/Diameter"],
                df["z/Diameter"]
            ])
            Y = np.vstack(df["Noise Vector"])
            X_list.append(X)
            Y_list.append(Y)
        return np.vstack(X_list), np.vstack(Y_list)

    def compute_f(self, X, theta):
        return np.prod(X ** theta, axis=1)

    def loss(self, theta):
        f_values = self.compute_f(self.X, theta)
        f_dists = np.array([abs(f_values[i] - f_values[j]) for i, j in combinations(range(len(f_values)), 2)])
        y_dists = np.array([euclidean(self.Y[i], self.Y[j]) for i, j in combinations(range(len(self.Y)), 2)])
        return np.sum((f_dists - y_dists) ** 2)

    def fit(self, theta_init=None):
        if theta_init is None:
            theta_init = np.zeros(self.X.shape[1])
        result = minimize(self.loss, theta_init, method='L-BFGS-B')
        self.best_theta = result.x
        return result

    def get_best_theta(self):
        return self.best_theta

    def predict_f(self, data_obj):
        df = data_obj.get_dimensionless_dataframe()
        X = np.column_stack([
            df["Top C_T"],
            df["Bottom C_T"],
            df["Top M_HT"],
            df["Bottom M_HT"],
            df["x/Diameter"],
            df["z/Diameter"]
        ])
        return self.compute_f(X, self.best_theta)








class Comparer:
    def __init__(self):
        self.D6=Data(6)
        self.D13=Data(13)
        self.D40 = Data(40)

    def visualize_dimension_less(self,name="Top C_T"):
        """
        List all the specified dimensionless quantity
        :param name: The name of the parameter you want to sort on
        :return:
        """
        def compile_dataframe(data_obj, label):
            idx = data_obj.both_on_idx
            df = pd.DataFrame({
                "Dataset": label,
                "Index": idx,
                "Top M_HT": data_obj.M_HT_top[idx],
                "Bottom M_HT": data_obj.M_HT_bot[idx],
                "Top C_T": data_obj.C_T_top[idx],
                "Bottom C_T": data_obj.C_T_bot[idx],
                "x/Diameter": data_obj.df_oparray.loc[idx, "x/Diameter of the two rotors"].values,
                "z/Diameter": data_obj.df_oparray.loc[idx, "z/Diameter of the two rotors"].values

            })
            return df

        df_combined = pd.concat([
            compile_dataframe(self.D6, "D6"),
            compile_dataframe(self.D13, "D13"),
            compile_dataframe(self.D40, "D40")
        ], ignore_index=True)

        print(df_combined.sort_values(by=name, ascending=True).reset_index(drop=True))

    def visualize_noise(self,name="Mic1"):
        """List all the noise data"""
        def compile_noise(data_obj, label):
            idx = data_obj.both_on_idx
            df = data_obj.df_noise.iloc[idx].copy()
            df.insert(0, "Dataset", label)
            df.insert(1, "Index", idx)
            return df

        df_combined = pd.concat([
            compile_noise(self.D6, "D6"),
            compile_noise(self.D13, "D13"),
            compile_noise(self.D40, "D40")
        ], ignore_index=True)

        print(df_combined.sort_values(by=name, ascending=True).reset_index(drop=True))

    def find_closest_samples(self,datasets, top_n=10):
        """
        Find closest samples between two datasets (dataset1 and dataset2)
        :param dataset1: Data object (e.g., self.D6)
        :param dataset2: Data object (e.g., self.D13)
        :param top_n: Number of closest pairs to find
        """
        noises = [ds.df_noise.iloc[ds.both_on_idx].values for ds in datasets]
        idx_lists = [ds.both_on_idx for ds in datasets]

        results = []

        if len(datasets) == 2:
            for i, j in product(range(len(noises[0])), range(len(noises[1]))):
                dist = euclidean(noises[0][i], noises[1][j])
                results.append({
                    f"{datasets[0]._index}_idx": idx_lists[0][i],
                    f"{datasets[1]._index}_idx": idx_lists[1][j],
                    "Distance": dist
                })

        elif len(datasets) == 3:
            for i, j, k in product(range(len(noises[0])), range(len(noises[1])), range(len(noises[2]))):
                d1 = euclidean(noises[0][i], noises[1][j])
                d2 = euclidean(noises[0][i], noises[2][k])
                d3 = euclidean(noises[1][j], noises[2][k])
                max_dist = max(d1, d2, d3)
                results.append({
                    f"{datasets[0]._index}_idx": idx_lists[0][i],
                    f"{datasets[1]._index}_idx": idx_lists[1][j],
                    f"{datasets[2]._index}_idx": idx_lists[2][k],
                    "Distance": max_dist
                })
        else:
            raise ValueError("Two or three ds supported")


        results = sorted(results, key=lambda x: x["Distance"])[:top_n]

        df_results = pd.DataFrame(results)
        pd.set_option('display.max_rows', None)
        print(df_results)

        return [{k: v for k, v in item.items() if "_idx" in k} for item in results]


    def compare_dimensionless_quantities(self, datasets, pairs):
        """
        datasets: list of Data objects (2 or 3)
        pairs: list of dicts with indexes
        returns: list of DataFrames (one per pair/group)
        """
        df_list = []

        for pair in pairs:
            rows = []
            for ds in datasets:
                idx = pair[f"{ds._index}_idx"]
                row = {
                    "Dataset": f"D{ds._index}",
                    "Index": idx,
                    "Top M_HT": ds.M_HT_top[idx],
                    "Bottom M_HT": ds.M_HT_bot[idx],
                    "Top C_T": ds.C_T_top[idx],
                    "Bottom C_T": ds.C_T_bot[idx],
                }
                rows.append(row)
            df = pd.DataFrame(rows)
            df_list.append(df)

        return df_list





if __name__ == '__main__':
    finder = FunctionFinder([Data(6), Data(13),Data(40)])
    result = finder.fit()
    print("Best theta:", finder.get_best_theta())



    exit()
    C=Comparer()

    C.visualize_dimension_less("Top M_HT")
    # C.visualize_dimension_less("Top C_T")

    pairs=C.find_closest_samples((C.D6,C.D13))
    print(pairs)
    for d in C.compare_dimensionless_quantities([C.D6,C.D13],pairs):
        print(d)
        print("*"*10)

#D6=56 D13=68
# 1.17983e+01  1.57310e+01 1.36434e-09 1.13189e-10 0.00000e+00 8.75000e-01
# 1.17294e+01  1.56398e+01 1.15881e-09 3.43960e-09 0.00000e+00 2.50000e-01
#D6=10 D13=19
# 1.57310e+01  1.57310e+01 2.04436e-09 1.59463e-10 2.75000e-01 1.50000e+00
# 1.17294e+01  1.56398e+01 1.25713e-09 3.43159e-09 2.75000e-01 8.75000e-01

#Translate: 我仔细的检查了您给我的数据，在这组实验（因为是静态实验）里Advance Ratio，and Inflow Velocity Distribution Ratio无法被考量。我仔细的检查了Tip Mach Number和Thrust Coefficient