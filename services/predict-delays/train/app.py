from datetime import datetime

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Model API", description="API for model inference")

model = joblib.load("model.joblib")


class ModelInput(BaseModel):
    Ligne: str
    DateTemps_gare_depart: datetime
    Gare_depart_index: float
    Gare_arrivee_index: float
    Direction: int
    Nombre_arret: float
    Taux_occupation_total: float


@app.post("/predict")
def predict(
    data: ModelInput,
) -> list[float]:
    features = pd.DataFrame([data.model_dump()])
    prediction = model.predict(features)
    return prediction
