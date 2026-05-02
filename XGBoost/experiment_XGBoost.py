import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from xgboost import XGBRegressor, plot_importance
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

from core.DataLoader import prepare_pi_data

DIAMS = [6, 13, 40]
SEED = 42
OUTDIR = "./artifacts"


BASE_PI_COLS = [
    'M_tip_top','M_tip_bot',
    'C_T_top','C_T_bot',
    'C_Q_top','C_Q_bot',
    'Re_top','Re_bot',
    'x_D','z_D','phi',
    'invT_top','invT_bot'
]
def train(normalize=True, rand=False, specific_PI=None):



    MODEL_KWARGS = dict(
        objective='reg:squarederror',
        n_estimators=800,
        max_depth=6,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        random_state=SEED,
        n_jobs=0,
        eval_metric='rmse'
    )


    df = prepare_pi_data(DIAMS, log_features=True)

    if not specific_PI:
        FEATURES = BASE_PI_COLS.copy()
    else:
        FEATURES = specific_PI

    if 'Prop_Radius' in df.columns:
        FEATURES.append('Prop_Radius')

    X = df[FEATURES].copy()
    y = df['Noise_RMS'].astype(float).values

    if normalize:
        scaler = StandardScaler()
        X = pd.DataFrame(
            scaler.fit_transform(X),
            columns=FEATURES,
            index=X.index
        )

    if rand:
        rng = np.random.default_rng(SEED)
        X = pd.DataFrame(
            rng.normal(size=X.shape),  # 正态分布随机数
            columns=FEATURES,
            index=X.index
        )

    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y, test_size=0.2, random_state=SEED
    )


    model = XGBRegressor(**MODEL_KWARGS)
    model.fit(
        X_train, y_train,
        eval_set=[(X_valid, y_valid)],
        verbose=False
    )


    y_pred = model.predict(X_valid)
    rmse = float(np.sqrt(mean_squared_error(y_valid, y_pred)))
    r2 = float(r2_score(y_valid, y_pred))


    os.makedirs(OUTDIR, exist_ok=True)

    with open(os.path.join(OUTDIR, 'metrics.json'), 'w') as f:
        json.dump({"rmse": rmse, "r2": r2}, f, indent=2)

    # model.save_model(os.path.join(OUTDIR, 'xgb_noise_model.json'))

    ax = plot_importance(model, importance_type='gain', show_values=False)
    ax.set_title('XGBoost Feature Importance (gain)')
    ax.text(
        0.95, 0.02,
        f'Validation R² = {r2:.3f}',
        ha='right', va='bottom',
        transform=ax.transAxes,
        fontsize=10, color='blue'
    )
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, 'feature_importance.png'), dpi=200)
    plt.show()

    preview = pd.concat([X.head(10), pd.Series(y[:10], name='Noise_RMS')], axis=1)
    preview.to_csv(os.path.join(OUTDIR, 'preview.csv'), index=False)

    print('--- Training complete ---')
    print('Validation RMSE:', rmse)
    print('Validation R^2:', r2)


if __name__ == '__main__':
    # train(normalize=True)
    # train(normalize=False)
    F1=[
    'M_tip_top','M_tip_bot',
    'C_T_top','C_T_bot',
    'C_Q_top','C_Q_bot',
    'Re_top','Re_bot',
    'x_D','z_D','phi',
    'invT_top','invT_bot'
    ]
    F2=[
    'Re_top','Re_bot',
        'invT_top','M_tip_top'
    ]
    F3=['invT_top','M_tip_top',
        "z_D", "x_D"]
    F4=["Re_top","Re_bot",
        "z_D", "x_D"]

    Fs=[F1,F2,F3,F4]

    for i in Fs:
        train(specific_PI=i)