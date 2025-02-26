from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, FilePath, DirectoryPath


VESRION="0.1"


class Config(BaseSettings):
  model_config = SettingsConfigDict(env_file='.env')
  ml_model_path: FilePath = Path('model.pkl')
  haha_tresh: float = 3.0

