import os
import re
import unicodedata
from typing import Dict, Union

import jinja2
from transliterate import translit

VRDConfig = Dict[str, Union[str, None]]
DictConfig = Dict[str, Union[str, 'DictConfig', None]]

files_encoding: str = 'utf-8'
default_templates_dir = os.path.join(os.path.dirname(__file__), '../templates')
default_templates_env = jinja2.Environment(loader=jinja2.FileSystemLoader(default_templates_dir))


def slugify(value: str, lang: str = 'ru') -> str:
    if value != unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii'):
        value = translit(value, lang, reversed=True)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def urlpath_join(prefix: str, url_path: str) -> str:
    if not prefix.endswith('/'):
        prefix += '/'
    if not url_path.startswith(prefix):
        if url_path.startswith('/'):
            url_path = url_path.lstrip('/')
        url_path = prefix + url_path
    return url_path
