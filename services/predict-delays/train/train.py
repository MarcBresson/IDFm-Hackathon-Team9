import pandas as pd
from dataset_building.dataset_builder import build_full_trip_dataset
from model_building.pipeline import modeling_pipeline
from sklearn.model_selection import train_test_split

full_dataset = build_full_trip_dataset()


full_dataset = pd.read_parquet("full_trip_dataset.parquet")


X = full_dataset.drop(
    columns=["Retard_additionnel_a_l_arrivee", "Retard_a_gare_d_arrivee"]
)
y = full_dataset["Retard_additionnel_a_l_arrivee"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

modeling_pipeline.fit(X_train, y_train)
