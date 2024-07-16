
import joblib # type: ignore
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import settings


class PredictRequest(BaseModel):
  text: str

class PredictResponse(BaseModel):
  rating: float


app = FastAPI()
cfg = settings.Config()
model = joblib.load(cfg.ml_model_path)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/predict")
def predict(req: PredictRequest) -> PredictResponse:
  rating = model.predict(
    [req.text]
  )
  return PredictResponse(rating=rating)

if __name__ == '__main__':
  uvicorn.run("main:app", port=cfg.app_port, host=cfg.app_host)