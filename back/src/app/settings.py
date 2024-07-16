from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, FilePath, DirectoryPath


class Config(BaseSettings):
  model_config = SettingsConfigDict(env_file='.env')
  app_host: str = 'localhost' 
  app_port: int = 80
  ml_model_path: FilePath = Path('model/stage.pkl')

