import logging

import joblib # type: ignore
from pydantic import BaseModel
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, Response
from starlette_exporter import PrometheusMiddleware, handle_metrics
from prometheus_client import Histogram, Counter

import settings
from preprocess import lemmatize

class PredictRequest(BaseModel):
  text: str
  joker: str

class PredictResponse(BaseModel):
  rating: float


app = FastAPI()
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)

cfg = settings.Config()
model = joblib.load(cfg.ml_model_path)
api_prefix = '/api/v1'


HAHA_COUNTER = Counter(
  name='haha_counter',
  documentation='total number of request'
)

JOKER_COUNTER = Counter(
  name='joker_counter',
  documentation='number of jokes from each client',
  labelnames=['joker_name']
)

HAHA_SUMMARY = Histogram(
  name='haha_summary',
  documentation='summary of predictions',
  buckets=list(range(0, 101, 10))
)


@app.get(f'{api_prefix}/startup')
def startup() -> Response:
  logging.info(f'get {api_prefix}/startup')
  return Response(status_code=status.HTTP_200_OK)


@app.get(f'{api_prefix}/ready')
def ready() -> Response:
  logging.info(f'get {api_prefix}/ready')
  return Response(status_code=status.HTTP_200_OK)


@app.get(f'{api_prefix}/health')
def health() -> Response:
  logging.info(f'get {api_prefix}/health')
  return Response(status_code=status.HTTP_200_OK)


@app.post(f'{api_prefix}/predict')
def predict(req: PredictRequest) -> PredictResponse:
  logging.info(f'post {api_prefix}/predict')
  
  JOKER_COUNTER.labels(joker_name=req.joker).inc()
  
  rating = model.predict(
    [lemmatize(req.text)]
  )

  HAHA_SUMMARY.observe(rating)

  if rating > cfg.haha_tresh:
    HAHA_COUNTER.inc()

  return PredictResponse(rating=rating)