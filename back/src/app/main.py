import logging

import joblib # type: ignore
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, Response

import settings


class PredictRequest(BaseModel):
  text: str

class PredictResponse(BaseModel):
  rating: float


app = FastAPI()
cfg = settings.Config()
model = joblib.load(cfg.ml_model_path)
api_prefix = '/api/v1'


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
  rating = model.predict(
    [req.text]
  )
  return PredictResponse(rating=rating)

if __name__ == '__main__':
  uvicorn.run("main:app", port=cfg.app_port, host=cfg.app_host)