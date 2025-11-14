This service aims at providing delay predictions for train lines using machine learning models. It leverages historical data and real-time inputs to forecast potential delays, helping passengers and operators make informed decisions.


## Data Source

1. Historical train timetable dataset provided by IDFM (Île-de-France Mobilités). This dataset includes various features such as train line, departure and arrival stations, scheduled and actual departure times. https://datalab.data-platform-self-service.net/file-explorer/dlb-hackathon/datasets-diffusion/2025/12_Donnees_transilien_SNCF/Courses%20et%20comptage/
2. Weather forecasting data from Météo France. https://datalab.data-platform-self-service.net/file-explorer/dlb-hackathon/datasets-diffusion/2025/10_Meteo_France_Climatologie_horaire/
3. Weather alerts from Météo France. https://datalab.data-platform-self-service.net/file-explorer/dlb-hackathon/datasets-diffusion/2025/03_Vigilance_meteo_20221127_20250722/


## Model target

The target variable for the model is `Delais_additionnel_a_l_arrivee`, which represents the additional delay at the arrival station in minutes. This was choosen to provide a more accurate measure of delays experienced by passengers, as it accounts for any delays that may have occurred during the journey rather than just the delay vs the scheduled arrival time.


## Model pipeline

The model is an XGBoost regressor with a preprocessing pipeline. Here is an overview of the preprocessing steps:

![model pipeline](assets/pipeline.png)


## How to train the delay prediction model

1. Download the datasets from https://datalab.data-platform-self-service.net/file-explorer/dlb-hackathon/datasets-diffusion/2025/12_Donnees_transilien_SNCF/Courses%20et%20comptage/
    1. keep the most recent version (i.e. 2024 and 2025 files) for more accurate predictions (since it will take into account potential train renovations on the lines).
2. Place the datasets in the `train/` directory.
3. Run the training script:
    ```bash
    cd services/predict-delays/train
    python train.py
    ```
4. The trained model will be saved as `model.joblib` in the `train/` directory.
5. You can then build the Docker image and run the service using Docker Compose:
    ```bash
    cd services/predict-delays
    docker-compose up --build
    ```
