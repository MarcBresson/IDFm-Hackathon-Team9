from typing import List

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import (
    FunctionTransformer,
    MinMaxScaler,
    OneHotEncoder,
    PolynomialFeatures,
    SplineTransformer,
    StandardScaler,
)
from xgboost import XGBRegressor

# dataset schema (kept for reference)
dataset_schema = {
    "Ligne": "category",  # nom de la ligne de train
    "DateTemps_gare_depart": "datetime",  # date et heure de départ de la gare
    "Gare_depart_index": "float",  # index de la gare de départ dans la ligne
    "Gare_arrivee_index": "float",  # index de la gare d'arrivée dans la ligne
    "Direction": "int8",  # 1 if the train is moving towards increasing station indexes, -1 otherwise
    "Nombre_arret": "float",  # nombre d'arrêts entre la gare de départ et la gare d'arrivée
    "Taux_occupation_total": "float32",  # taux d'occupation total du train en pourcentage
    "Delais_additionnel_a_l_arrivee": "float",  # retard additionnel du train à l'arrivée en secondes par rapport au depart
    "Retard_a_gare_d_arrivee": "float",  # retard du train à l'arrivée en secondes par aux horaires prévus
    # Les phenomenes vont de 1 à 4 pour indiquer leur intensité
    "phenomene_1": "int8",  # vent
    "phenomene_2": "int8",  # pluie
    "phenomene_3": "int8",  # orages
    "phenomene_4": "int8",  # crues
    "phenomene_5": "int8",  # neige / verglas
    "phenomene_6": "int8",  # canicule
    "phenomene_7": "int8",  # grand froid
    "temperature_instant": "int32",  # température instantanée en degrés Celsius
    "quantite_precipitations": "float32",  # quantité de précipitations en mm
}


TARGET_COLUMN = "Delais_additionnel_a_l_arrivee"
DROP_COLUMN = "Retard_a_gare_d_arrivee"


# Small helpers ---------------------------------------------------------------
def select_columns(cols: List[str]):
    """Return a FunctionTransformer that selects DataFrame columns by name."""

    return FunctionTransformer(lambda X: X[cols], validate=False)


def datetime_to_timestamp_seconds(X):
    """Convert a single-column DataFrame/array with datetimes to a (n_samples,1) float array of seconds since epoch."""
    # accept DataFrame or array-like
    # coerce to 1-d series safely
    arr = pd.Series(X).squeeze()
    s = pd.to_datetime(arr)
    return (s.astype("int64") / 1e9).to_numpy().reshape(-1, 1)


def datetime_to_workingday(X):
    """Return a (n_samples, 1) array with 1 for working day (Mon-Fri) else 0.

    Expects a single-column DataFrame/array of datetimes or strings.
    """
    arr = pd.Series(X["DateTemps_gare_depart"])
    s = pd.to_datetime(arr)
    # pandas weekday: Monday=0 .. Sunday=6
    is_working = s.dt.weekday < 5
    return is_working.astype(int).to_numpy().reshape(-1, 1)


def datetime_to_month(X):
    """Return a (n_samples, 1) array with month (1-12).

    Expects a single-column DataFrame/array of datetimes or strings.
    """
    arr = pd.Series(X["DateTemps_gare_depart"])
    s = pd.to_datetime(arr)
    return s.dt.month.to_numpy().reshape(-1, 1)


def datetime_to_hour(X):
    """Return a (n_samples, 1) array with hour (0-23).

    Expects a single-column DataFrame/array of datetimes or strings.
    """
    arr = pd.Series(X["DateTemps_gare_depart"])
    s = pd.to_datetime(arr)
    return s.dt.hour.to_numpy().reshape(-1, 1)


def datetime_to_weekday(X):
    """Return a (n_samples, 1) array with weekday number 0..6 extracted from datetimes."""
    arr = pd.Series(X["DateTemps_gare_depart"])
    s = pd.to_datetime(arr)
    return s.dt.weekday.to_numpy().reshape(-1, 1)


# Build pipelines -------------------------------------------------------------
# Date pipeline: extract timestamp then spline transform


def periodic_spline_transformer(period, n_splines=None, degree=3):
    if n_splines is None:
        n_splines = period
    n_knots = n_splines + 1  # periodic and include_bias is True
    return SplineTransformer(
        degree=degree,
        n_knots=n_knots,
        knots=np.linspace(0, period, n_knots).reshape(n_knots, 1),
        extrapolation="periodic",
        include_bias=True,
    )


date_pipeline = Pipeline(
    [
        (
            "extract",
            FeatureUnion(
                [
                    (
                        "working_day",
                        FunctionTransformer(datetime_to_workingday, validate=False),
                    ),
                    (
                        "month",
                        FunctionTransformer(datetime_to_month, validate=False),
                    ),
                    (
                        "weekday",
                        FunctionTransformer(datetime_to_weekday, validate=False),
                    ),
                    (
                        "hour",
                        FunctionTransformer(datetime_to_hour, validate=False),
                    ),
                ]
            ),
        ),
        (
            "spline",
            ColumnTransformer(
                [
                    (
                        "cyclic_month",
                        periodic_spline_transformer(12, n_splines=6),
                        [1],
                    ),
                    (
                        "cyclic_weekday",
                        periodic_spline_transformer(7, n_splines=3),
                        [2],
                    ),
                    (
                        "cyclic_hour",
                        periodic_spline_transformer(24, n_splines=12),
                        [3],
                    ),
                ],
                remainder="drop",
                sparse_threshold=0,
            ),
        ),
    ]
)

# combine originals + interaction using FeatureUnion

# poly pipeline that returns only the interaction term x1*x2
poly_interaction_only = Pipeline(
    [
        (
            "poly",
            PolynomialFeatures(degree=2, interaction_only=True, include_bias=False),
        ),
        (
            "select_interaction",
            FunctionTransformer(lambda X: X[:, -1].reshape(-1, 1), validate=False),
        ),
    ]
)

# combine originals + interaction using FeatureUnion
phen_pipeline = Pipeline(
    [
        (
            FeatureUnion(
                [
                    ("original", FunctionTransformer(lambda X: X, validate=False)),
                    ("interaction", poly_interaction_only),
                ]
            ),
        )
    ]
)

# Numeric columns to scale (exclude phenomene_1 and phenomene_3 because handled above)
numeric_cols = [
    "Nombre_arret",
    "Direction",
    # "temperature_instant",
    # "quantite_precipitations",
    "Taux_occupation_total",
]


# FeatureUnion for gare indices: keep originals and add min-max scaled versions
gare_index_cols = ["Gare_depart_index", "Gare_arrivee_index"]


preprocessor = ColumnTransformer(
    [
        ("date", date_pipeline, ["DateTemps_gare_depart"]),
        ("ligne", OneHotEncoder(handle_unknown="error"), ["Ligne"]),
        (
            "gare_indices",
            FeatureUnion([("original", "passthrough"), ("minmax", MinMaxScaler())]),
            gare_index_cols,
        ),
        ("numeric", StandardScaler(), numeric_cols),
        # ("phenomene_interaction", phen_pipeline, phen_cols),
    ],
    remainder="drop",
    sparse_threshold=0,
)


# Final pipeline with XGBoost regressor
modeling_pipeline = Pipeline(
    [
        ("preprocessor", preprocessor),
        (
            "model",
            XGBRegressor(
                objective="reg:squarederror", n_estimators=100, random_state=42
            ),
        ),
    ]
)
