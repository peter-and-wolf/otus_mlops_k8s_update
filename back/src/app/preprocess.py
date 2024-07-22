import re
from typing import Any, Iterable
from functools import lru_cache

from pymorphy3 import MorphAnalyzer #type: ignore
from stop_words import get_stop_words # type: ignore

morph_analyzer = MorphAnalyzer()
stop_words_ru = set(get_stop_words("ru"))
word_regex = re.compile(r'\w+')


@lru_cache
def get_normal_form(word: str) -> str:
  return morph_analyzer.parse(word)[0].normal_form

def lemmatize(line):
  return ' '.join(
    filter (
      lambda word: word not in stop_words_ru,
      map(
        lambda x: get_normal_form(str(x)),
        word_regex.findall(line)
      )
    )
  )
