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
    '''
    Creates a slug according to the given string

    Parameters
    ----------
    value: str
        The string input to be converted to a slug
    lang: str
        The language used to properly convert the given string to a slug
        (Default is 'ru', Russian)

    Return
    ------
    str
        The converted string with the format of a slug
    '''

    # Check if value is not an ASCII string, if true, transliterate it
    if value != unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii'):
        value = translit(value, lang, reversed=True)
    # Normalize the string and retain only ASCII characters
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    # Remove special characters and convert to lowercase
    value = re.sub(r'[^\w\s-]', '', value.lower())
    # Clean up dashes and spaces
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def urlpath_join(prefix: str, url_path: str) -> str:
    '''
    Joins two paths with the prefix being on the left

    Parameters
    ----------
    prefix: str
        First part of the resulting URL
    url_path: str
        Second part of the resulting URL

    Return
    ------
    str
        The joined URL
    '''

    prefix = prefix.rstrip('/') + '/'
    if url_path.startswith(prefix):
        return url_path
    url_path = url_path.lstrip('/')
    return f"{prefix}{url_path}" if url_path else prefix[:-1]
