import os
import numpy as np
import pandas as pd
from core.DataLoader import load_combined_data

def fix_outliers_z025_simple_and_save(diameter,
                                      data_dir="..\\data",
                                      thrust_threshold=500.0,
                                      z_level=0.25,
                                      save_path=None,
                                      overwrite=False):
    """
    极简版：一次性修复并保存
    - 仅在 z/Diameter == z_level 的样本上，将 Top/Bottom thrust > threshold 的值设为 NaN，
      然后在每个 (Top RPM, Bottom RPM, z) 组内按 x/Diameter 线性插值填回（等价两侧邻点直线插值）。
    - 保存为 CSV（默认 <data_dir>/combined{diameter}_fixed.csv）。

    假设：每个 outlier 点在该分组内沿 x 都有左右两个邻点（你已确认）。
    """
    df = load_combined_data(diameter, data_dir=data_dir).copy()

    zcol = "z/Diameter"
    xcol = "x/Diameter"
    top_thrust = "Top rotor thrust (N)"
    bot_thrust = "Bottom rotor thrust (N)"
    top_rpm = "Top rotor RPM"
    bot_rpm = "Bottom rotor RPM"

    zmask = np.isclose(df[zcol].astype(float), float(z_level), rtol=0, atol=1e-12)
    if not zmask.any():
        if save_path is None:
            save_path = os.path.join(data_dir, f"combined{diameter}_fixed.csv")
        if (not overwrite) and os.path.exists(save_path):
            return save_path
        df.to_csv(save_path, index=False)
        return save_path

    sub = df.loc[zmask].copy()

    def _interp_group(g: pd.DataFrame) -> pd.DataFrame:
        g = g.sort_values(by=xcol).copy()
        for col in (top_thrust, bot_thrust):
            y = g[col].astype(float).mask(g[col].astype(float) > thrust_threshold, np.nan)
            g[col] = y.interpolate(method="linear", limit_direction="both", limit_area="inside")
        return g

    sub_fixed = (
        sub.groupby([top_rpm, bot_rpm, zcol], sort=False, dropna=False, group_keys=False)
        .apply(_interp_group)
    )

    df.loc[sub_fixed.index, [top_thrust, bot_thrust]] = sub_fixed[[top_thrust, bot_thrust]].to_numpy()

    if save_path is None:
        save_path = os.path.join(data_dir, f"combined{diameter}_fixed.csv")

    if (not overwrite) and os.path.exists(save_path):
        return save_path

    df.to_csv(save_path, index=False)
    return save_path

if __name__ == '__main__':
    fix_outliers_z025_simple_and_save(6, data_dir="..\\data")


    # import pandas as pd
    # df_fixed_13 = pd.read_csv("..\\data\\combined40_fixed.csv")