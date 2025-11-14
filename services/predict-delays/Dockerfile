FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY train/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY train/model.joblib /app/model.joblib
ENV MODEL_PATH=/app/model.joblib

COPY train/ /app/

EXPOSE 8000

ENTRYPOINT [ "python",  "/app/main.py"]
