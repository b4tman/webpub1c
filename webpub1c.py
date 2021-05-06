#!/usr/bin/env python3


import logging
import os
import pprint
import re
import unicodedata
from typing import List, Dict, Union, Optional, Iterable

import fire
import jinja2
import yaml
from pathvalidate import is_valid_filepath, sanitize_filename
from transliterate import translit

_xml_esc = str.maketrans({
    "&": "&amp;", '"': "&quot;", "'": "&apos;",
    "<": "&lt;", ">": "&gt;",
})

files_encoding: str = 'utf-8'


def xml_escape(txt: str) -> str:
    return txt.translate(_xml_esc)


def slugify(value: str, lang: str = 'ru') -> str:
    if value != unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii'):
        value = translit(value, lang, reversed=True)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


class WebPublication:
    """ 1c web publication info for apache2 config """

    def __init__(self, name: str,
                 directory: str = '',
                 vrd_filename: str = '',
                 url_path: str = '',
                 vrd_params: Optional[Dict[str, Union[str, None]]] = None):
        if '' == name:
            raise ValueError('publication name empty')
        self.name: str = name
        self.directory: str = directory
        self.vrd_filename: str = vrd_filename
        self.url_path: str = url_path
        self.vrd_params: Dict[str, str] = {}
        if vrd_params is not None:
            self.vrd_params = vrd_params

    @staticmethod
    def from_config(name: str, config: str):
        """ read publication info from config block """

        url_expr = re.compile('Alias\\s"([^"]+)"')
        dir_expr = re.compile('<Directory\\s"([^"]+)">')
        vrd_expr = re.compile('ManagedApplicationDescriptor\\s"([^"]+)"')

        url_match = url_expr.search(config)
        dir_match = dir_expr.search(config)
        vrd_match = vrd_expr.search(config)

        _url: str = url_match.group(1) if url_match is not None else ""
        _dir: str = dir_match.group(1) if dir_match is not None else ""
        _vrd: str = vrd_match.group(1) if vrd_match is not None else ""
        return WebPublication(name, _dir, _vrd, _url)

    def to_config(self) -> str:
        """ get config block from publication info """

        env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
        template = env.get_template('apache_pub.cfg')
        pub_params: Dict[str, str] = {
            'directory': self.directory,
            'vrd_filename': self.vrd_filename,
            'url_path': self.url_path,
            'name': self.name
        }
        return template.render(ctx=pub_params)

    def describe(self) -> str:
        """ describe publication info"""

        return pprint.pformat({
            'name': self.name,
            'url_path': self.url_path,
            'directory': self.directory,
            'vrd_filename': self.vrd_filename,
        }, 2)

    def generate_paths(self, dir_prefix: str, vrd_prefix: str, url_prefix: str):
        """ generate directory path, vrd filepath, url for named publication """

        if not os.path.isdir(dir_prefix):
            raise ValueError(f'pub dir not found: {dir_prefix}')
        if not os.path.isdir(vrd_prefix):
            raise ValueError(f'vrd dir not found: {vrd_prefix}')
        if not is_valid_filepath(url_prefix, platform='posix'):
            raise ValueError(f'url prefix invalid: {url_prefix}')
        if not url_prefix.endswith('/'):
            url_prefix = url_prefix + '/'

        slug_name = slugify(self.name)
        safe_name = sanitize_filename(slug_name)
        safe_name_url = sanitize_filename(slug_name, platform='posix')
        self.directory = os.path.join(dir_prefix, safe_name)
        self.vrd_filename = os.path.join(vrd_prefix, f'{safe_name}.vrd')
        self.url_path = url_prefix + safe_name_url

    def is_valid(self) -> bool:
        """ is directory path, vrd filepath, url, name valid """

        return is_valid_filepath(self.directory) and \
               is_valid_filepath(self.vrd_filename) and \
               is_valid_filepath(self.url_path, platform='posix') and \
               '' != self.name

    def is_ok_to_create(self) -> bool:
        """ can create directory, vrd file """

        return self.is_valid() and not (
                os.path.exists(self.directory) or
                os.path.exists(self.vrd_filename)
        )

    def is_exist(self) -> bool:
        """ directory and vrd file exists """

        return os.path.isdir(self.directory) and \
               os.path.exists(self.vrd_filename)

    def create_directory(self):
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

    def remove_directory(self):
        if os.path.exists(self.directory):
            os.rmdir(self.directory)

    def create_vrd(self):
        if not self.is_valid():
            raise ValueError('publication is invalid')
        if os.path.exists(self.vrd_filename):
            raise ValueError(f'vrd file "{self.vrd_filename}" exists')

        vrd_params: Dict[str, str] = {
            'url_path': xml_escape(self.url_path),
            'ibname': xml_escape(self.name)
        }
        vrd_params.update(self.vrd_params)
        env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
        template = env.get_template('vrd.xml')

        vrd_data: str = template.render(ctx=vrd_params)
        with open(self.vrd_filename, "w", encoding=files_encoding) as f:
            f.write(vrd_data)

    def remove_vrd(self):
        if os.path.exists(self.vrd_filename):
            os.unlink(self.vrd_filename)

    def create(self):
        """ create all """

        if not self.is_ok_to_create():
            raise ValueError(f'can\'t create pub: {self.name}')
        self.create_directory()
        self.create_vrd()

    def remove(self):
        """ remove all """

        self.remove_vrd()
        self.remove_directory()


class ApacheConfig:
    """ apache config """

    start_tag: str = '# --- WEBPUB1C PUBLICATION START:'
    end_tag: str = '# --- WEBPUB1C PUBLICATION END:'

    def __init__(self, filename: str,
                 vrd_path: str,
                 dir_path: str,
                 url_base: str,
                 vrd_params: Optional[Dict[str, Union[str, None]]] = None):
        self.filename: str = filename
        self.vrd_path: str = vrd_path
        self.dir_path: str = dir_path
        self.url_base: str = url_base
        self.vrd_params: Optional[Dict[str, Union[str, None]]] = vrd_params

    def is_valid(self) -> bool:
        return os.path.isfile(self.filename)

    def _check(self):
        if not self.is_valid():
            raise ValueError('invalid apache config')

    @property
    def text(self) -> str:
        self._check()

        with open(self.filename, 'r', encoding=files_encoding) as f:
            txt: str = f.read()
        return txt

    def has_1cws_module(self) -> bool:
        ws_expr = re.compile('^LoadModule\\s_1cws_module\\s.*$', re.M)
        result: bool = (ws_expr.search(self.text) is not None)

        return result

    def add_1cws_module(self, module_filename: str):
        if self.has_1cws_module():
            return

        with open(self.filename, "a", encoding=files_encoding) as f:
            f.write(f'\nLoadModule _1cws_module "{module_filename}"\n')

    @property
    def publications(self) -> Iterable[str]:
        start_expr = re.compile('^{}\\s(.+)$'.format(re.escape(ApacheConfig.start_tag)), re.M)
        for match in start_expr.finditer(self.text):
            yield match.group(1).strip()

    def is_publicated(self, ibname: str) -> bool:
        return ibname in self.publications

    def add_publication(self, ibname: str):
        if self.is_publicated(ibname):
            raise KeyError(f'infobase "{ibname}" already publicated')

        publication = WebPublication(ibname, vrd_params=self.vrd_params)
        publication.generate_paths(self.dir_path, self.vrd_path, self.url_base)
        if not publication.is_ok_to_create():
            raise ValueError(f'can\'t create publication: {publication.describe()}')

        publication.create()
        pub_cfg = publication.to_config()
        with open(self.filename, "a", encoding=files_encoding) as f:
            f.write(f'\n{ApacheConfig.start_tag} {ibname}\n')
            f.write(pub_cfg)
            f.write(f'\n{ApacheConfig.end_tag} {ibname}')

    def get_publication(self, ibname: str) -> Optional[WebPublication]:
        if not self.is_publicated(ibname):
            return None

        start_pub = re.compile('^{}\\s{}'.format(re.escape(ApacheConfig.start_tag), re.escape(ibname)))
        end_pub = re.compile('^{}\\s{}'.format(re.escape(ApacheConfig.end_tag), re.escape(ibname)))

        is_pub_started: bool = False
        pub_lines: List[str] = []
        lines: List[str] = self.text.splitlines(keepends=True)
        for line in lines:
            if is_pub_started:
                if end_pub.match(line):
                    break
                else:
                    pub_lines.append(line)
                continue
            if start_pub.match(line):
                is_pub_started = True

        if 0 == len(pub_lines):
            raise ValueError('can\'t parse config :(')

        publication = WebPublication.from_config(ibname, ''.join(pub_lines))
        return publication

    def remove_publication(self, ibname: str):
        if not self.is_publicated(ibname):
            raise KeyError(f'infobase "{ibname}" not publicated')

        start_pub = re.compile('^{}\\s{}'.format(re.escape(ApacheConfig.start_tag), re.escape(ibname)))
        end_pub = re.compile('^{}\\s{}'.format(re.escape(ApacheConfig.end_tag), re.escape(ibname)))
        is_pub_started: bool = False

        # filter lines for new config and publication
        pub_lines: List[str] = []
        new_lines: List[str] = []
        lines: List[str] = self.text.splitlines(keepends=True)
        for line in lines:
            if is_pub_started:
                if end_pub.match(line):
                    is_pub_started = False
                else:
                    pub_lines.append(line)
                continue
            if start_pub.match(line):
                is_pub_started = True
                continue
            new_lines.append(line)

        # remove vrd and directory
        publication = WebPublication.from_config(ibname, ''.join(pub_lines))
        publication.remove()

        # write new config
        with open(self.filename, "w", encoding=files_encoding) as f:
            f.write(''.join(new_lines))


class Commands:
    """ 1C: Enterprise infobase web publication tool. """
    _config: Dict[str, Union[str, Dict[str, Union[str, None]]]]

    def __init__(self, config: str = 'webpub1c.yml', verbose: bool = False):
        level = logging.INFO if verbose else logging.WARNING
        logging.basicConfig(level=level)
        self._log = logging.getLogger("webpub1c")
        self._log.setLevel(level)

        with open(config, 'r', encoding=files_encoding) as cfg_file:
            self._config = yaml.safe_load(cfg_file)

        vrd_params: Optional[Dict[str, Union[str, None]]] = self._config.get('vrd_params', None)
        apache_config: str = self._config.get('apache_config', '')
        self._vrd_path: str = self._config.get('vrd_path', '')
        self._dir_path: str = self._config.get('dir_path', '')
        self._url_base: str = self._config.get('url_base', '')

        self._apache_cfg = ApacheConfig(apache_config, self._vrd_path,
                                        self._dir_path, self._url_base,
                                        vrd_params)

    def _is_vrd_path_valid(self) -> bool:
        return os.path.isdir(self._vrd_path)

    def _is_dir_path_valid(self) -> bool:
        return os.path.isdir(self._dir_path)

    def _is_url_base_valid(self) -> bool:
        return is_valid_filepath(self._url_base, platform='posix')

    def _is_module_valid(self) -> bool:
        if 'platform_path' not in self._config:
            return False
        if 'ws_module' not in self._config:
            return False
        return os.path.isfile(os.path.join(self._config['platform_path'], self._config['ws_module']))

    def check(self):
        """ Check config """

        print('config:')
        pprint.pprint(self._config, indent=2)
        print('\n---')
        print('apache cfg: {}'.format('ok' if self._apache_cfg.is_valid() else 'invalid'))
        print('  vrd path: {}'.format('ok' if self._is_vrd_path_valid() else 'invalid'))
        print('  dir path: {}'.format('ok' if self._is_dir_path_valid() else 'invalid'))
        print('  url base: {}'.format('ok' if self._is_url_base_valid() else 'invalid'))
        print(' ws module: {}'.format('ok' if self._is_module_valid() else 'not found'))

    def has_module(self):
        """ Ensure apache config has 1cws module """

        print(self._apache_cfg.has_1cws_module())

    def add_module(self):
        """ Add 1cws module to apache config """

        if self._apache_cfg.has_1cws_module():
            self._log.info('config unchanged')
        else:
            module: str = os.path.join(self._config['platform_path'], self._config['ws_module'])
            self._apache_cfg.add_1cws_module(module)
            self._log.info('module added')

    def list(self):
        """ List publications """

        return list(self._apache_cfg.publications)

    def get(self, ibname: str) -> Optional[str]:
        """ Get publication info """

        publication = self._apache_cfg.get_publication(ibname)
        if publication is None:
            return publication
        return publication.describe()

    def add(self, ibname: str):
        """ Add new publication """

        self._apache_cfg.add_publication(ibname)
        self._log.info(f'publication added: {ibname}')

    def remove(self, ibname: str):
        """ Remove publication """

        self._apache_cfg.remove_publication(ibname)
        self._log.info(f'publication removed: {ibname}')


if __name__ == "__main__":
    fire.Fire(Commands)
