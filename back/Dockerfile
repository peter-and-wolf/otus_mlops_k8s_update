FROM python:3.12-slim

WORKDIR /app

ENV HAHA_TRESH=3.0
ENV ML_MODEL_PATH=model.pkl

COPY src/app/main.py .
COPY src/app/settings.py .
COPY src/app/preprocess.py .
COPY requirements.txt .
COPY models/tr.pkl model.pkl

RUN pip install -r requirements.txt

CMD ["fastapi", "run", "main.py", "--port", "80"]
