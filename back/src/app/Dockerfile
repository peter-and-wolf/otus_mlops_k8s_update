FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

ENV APP_PORT=80
ENV APP_HOST='0.0.0.0'
ENV ML_MODEL_PATH=stage.pkl

COPY main.py .
COPY settings.py .
COPY requirements.txt .
COPY stage.pkl .

RUN pip install -r requirements.txt

CMD ["python", "main.py"]
