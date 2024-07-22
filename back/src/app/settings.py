from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, FilePath, DirectoryPath


class Config(BaseSettings):
  model_config = SettingsConfigDict(env_file='.env')
  ml_model_path: FilePath = Path('model/tr.pkl')
  haha_tresh: float = 3.0

