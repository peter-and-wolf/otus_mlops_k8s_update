FROM python:3.12-slim

WORKDIR /app

ARG MODEL_TO_USE

ENV HAHA_TRESH=3.0
ENV ML_MODEL_PATH=model.pkl

COPY app/main.py .
COPY app/settings.py .
COPY app/preprocess.py .
COPY requirements.txt .
COPY models/${MODEL_TO_USE} model.pkl

RUN pip install -r requirements.txt

CMD ["fastapi", "run", "main.py", "--port", "80"]
