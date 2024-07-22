import csv
import json
import random
import asyncio
from pathlib import Path
from typing import Annotated, Generator

import typer
import aiohttp


jokers = dict(
  peter=.35,
  alex=.25,
  igor=.2,
  victor=.1,
  modest=.1,
)


def get_joker() -> str:
  return random.choices([*jokers], weights=[*jokers.values()])[0]


def get_joke(path_to_data: Path) -> Generator[str, None, None]:
 with open(path_to_data) as f:
  reader = csv.reader(f)
  for entry in reader:
    yield entry[1]


async def score(session, endpoint: str, joke_num: int, joke: str):
    data = dict(
      joker=get_joker(),
      text=joke
    )
    async with session.post(endpoint, json=data) as response:
      try: 
        result = await response.json()
        print(json.dumps(dict(
          joke_num=joke_num,
          rating=result['rating']
        )))
      except aiohttp.ContentTypeError as err:
        result = json.dumps(dict(
          code=err.code,
          msg=err.message
        ))

      return result


async def run(path_to_data: Path, endpoint: str):
  async with aiohttp.ClientSession() as session:
    def tasks():
      for joke_num, joke in enumerate(get_joke(path_to_data)):
        yield asyncio.ensure_future(
          score(session, str(endpoint), joke_num, joke)
        )
    await asyncio.gather(*tasks())


def main(path_to_data: Annotated[Path, typer.Option()] = Path('back/data/jokes.csv'),
         port: Annotated[int, typer.Option] = 80,
         host: Annotated[str, typer.Option()] = 'jokemeter.ai'):
  
  asyncio.run(run(
    path_to_data,
    f'http://{host}:{port}/api/v1/predict'
  ))


if __name__ == '__main__':
 typer.run(main)