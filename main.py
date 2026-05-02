import numpy as np
import pandas as pd
from scipy.io import loadmat

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.float_format', '{:.5e}'.format)
np.seterr(divide='ignore', invalid='ignore')

d6=loadmat("data/oparray6.mat")["oparray6"]
d13=loadmat("data/oparray13.mat")["oparray13"]
d40=loadmat("data/oparray40.mat")["oparray40"]

n6_bot = loadmat("data/Noise.mat")["micdatBot6"]
n6_top = loadmat("data/Noise.mat")["micdatTop6"]
n6_both = loadmat("data/Noise.mat")["micdatBoth6"]

n13_bot = loadmat("data/Noise.mat")["micdatBot13"]
n13_top = loadmat("data/Noise.mat")["micdatTop13"]
n13_both = loadmat("data/Noise.mat")["micdatBoth13"]

n40_bot = loadmat("data/Noise.mat")["micdatBot40"]
n40_top = loadmat("data/Noise.mat")["micdatTop40"]
n40_both = loadmat("data/Noise.mat")["micdatBoth40"]

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

noise_columns = [
    "Mic1",
    "Mic2",
    "Mic3",
    "Mic4",
    "Mic5",
    "Mic6",
    "Mic7",
    "Mic8",
    "Mic9"
]

df_6=pd.DataFrame(d6,columns=oparray_columns)
df_13=pd.DataFrame(d13,columns=oparray_columns)
df_40=pd.DataFrame(d40,columns=oparray_columns)

noise6_bot = pd.DataFrame(n6_bot, columns=noise_columns)
noise6_top = pd.DataFrame(n6_top, columns=noise_columns)
noise6_both = pd.DataFrame(n6_both, columns=noise_columns)

noise13_bot = pd.DataFrame(n13_bot, columns=noise_columns)
noise13_top = pd.DataFrame(n13_top, columns=noise_columns)
noise13_both = pd.DataFrame(n13_both, columns=noise_columns)

noise40_bot = pd.DataFrame(n40_bot, columns=noise_columns)
noise40_top = pd.DataFrame(n40_top, columns=noise_columns)
noise40_both = pd.DataFrame(n40_both, columns=noise_columns)

print(df_6)
print(noise6_both)
print(noise6_top)