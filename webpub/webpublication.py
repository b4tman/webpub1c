import json
import os
import re
import shutil
from typing import Optional, Dict, Callable, Iterable

import jinja2
import markupsafe
from pathvalidate import is_valid_filepath, sanitize_filename

from .common import VRDConfig, files_encoding, default_templates_env, slugify


def _try(actions: Iterable[Callable[[], None]]) -> None:
    for action in actions:
        try:
            action()
        finally:
            pass


class WebPublication:
    """ 1c web publication info for apache2 config """

    def __init__(self, name: str,
                 directory: str = '',
                 vrd_filename: str = '',
                 url_path: str = '',
                 vrd_params: Optional[VRDConfig] = None,
                 templates_env: Optional[jinja2.Environment] = None,
                 infobase_filepath=''):
        if '' == name:
            raise ValueError('publication name empty')
        self.name: str = name
        self.directory: str = directory
        self.vrd_filename: str = vrd_filename
        self.url_path: str = url_path
        self.vrd_params: VRDConfig = {}
        if vrd_params is not None:
            self.vrd_params = vrd_params

        if templates_env is None:
            self.templates_env = default_templates_env
        else:
            self.templates_env = templates_env

        self.infobase_filepath: str = infobase_filepath

    @staticmethod
    def from_config(name: str, config: str, templates_env: Optional[jinja2.Environment] = None) -> 'WebPublication':
        """ read publication info from config block """

        url_expr = re.compile(r'Alias\s"([^"]+)"')
        dir_expr = re.compile(r'<Directory\s"([^"]+)">')
        vrd_expr = re.compile(r'ManagedApplicationDescriptor\s"([^"]+)"')
        file_expr = re.compile(r'#\sinfobase_filepath:\s"([^"]+)"')

        url_match = url_expr.search(config)
        dir_match = dir_expr.search(config)
        vrd_match = vrd_expr.search(config)
        file_match = file_expr.search(config)

        _url: str = url_match.group(1) if url_match is not None else ""
        _dir: str = dir_match.group(1) if dir_match is not None else ""
        _vrd: str = vrd_match.group(1) if vrd_match is not None else ""
        _file: str = file_match.group(1) if file_match is not None else ""
        return WebPublication(name, _dir, _vrd, _url, templates_env=templates_env, infobase_filepath=_file)

    def to_config(self) -> str:
        """ get config block from publication info """

        template = self.templates_env.get_template('apache_pub.cfg')
        pub_params: Dict[str, str] = {
            'directory': self.directory,
            'vrd_filename': self.vrd_filename,
            'url_path': self.url_path,
            'name': self.name,
            'infobase_filepath': self.infobase_filepath,
            'is_file_infobase': self.is_file_infobase(),
        }
        return template.render(ctx=pub_params)

    def is_file_infobase(self):
        return '' != self.infobase_filepath

    def describe(self) -> str:
        """ describe publication info"""

        return json.dumps({
            'name': self.name,
            'url_path': self.url_path,
            'directory': self.directory,
            'vrd_filename': self.vrd_filename,
            'infobase_filepath': self.infobase_filepath,
            'is_file_infobase': self.is_file_infobase(),
        }, ensure_ascii=False, indent=2)

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
        safe_name = sanitize_filename(slug_name, platform='auto')
        safe_name_url = sanitize_filename(slug_name, platform='posix')
        self.directory = os.path.join(dir_prefix, safe_name)
        self.vrd_filename = os.path.join(vrd_prefix, f'{safe_name}.vrd')
        self.url_path = url_prefix + safe_name_url

    def is_valid(self) -> bool:
        """ is directory path, vrd filepath, url, name valid """

        return \
            is_valid_filepath(self.directory, platform='auto') and \
            is_valid_filepath(self.vrd_filename, platform='auto') and \
            is_valid_filepath(self.url_path, platform='posix') and \
            self.url_path.startswith('/') and \
            '' != self.name

    def is_ok_to_create(self) -> bool:
        """ can create directory, vrd file """

        return self.is_valid() and not (
                os.path.exists(self.directory) or
                os.path.exists(self.vrd_filename)
        )

    def is_exist(self) -> bool:
        """ directory and vrd file exists """

        return \
            os.path.isdir(self.directory) and \
            os.path.exists(self.vrd_filename)

    def create_directory(self):
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

    def remove_directory(self, force: bool = False):
        if os.path.exists(self.directory):
            if force:
                shutil.rmtree(self.directory)
            else:
                os.rmdir(self.directory)

    def create_vrd(self, force: bool = False):
        if not force:
            if not self.is_valid():
                raise ValueError('publication is invalid')
            if os.path.exists(self.vrd_filename):
                raise ValueError(f'vrd file "{self.vrd_filename}" exists')

        vrd_params: VRDConfig = {
            'url_path': markupsafe.escape(self.url_path),
            'ibname': markupsafe.escape(self.name),
            'infobase_filepath': markupsafe.escape(self.infobase_filepath),
            'is_file_infobase': self.is_file_infobase(),
        }
        vrd_params.update(self.vrd_params)
        template = self.templates_env.get_template('vrd.xml')

        vrd_data: str = template.render(ctx=vrd_params)
        with open(self.vrd_filename, "w", encoding=files_encoding) as f:
            f.write(vrd_data)

    def remove_vrd(self):
        if os.path.exists(self.vrd_filename):
            os.unlink(self.vrd_filename)

    def create(self, force: bool = False):
        """ create all """

        if force:
            _try([self.create_directory,
                  lambda: self.create_vrd(force=True)])
            return

        if not self.is_ok_to_create():
            raise ValueError(f'can\'t create pub: {self.name}')
        self.create_directory()
        self.create_vrd()

    def remove(self, force: bool = False):
        """ remove all """

        if force:
            _try([self.remove_vrd,
                  lambda: self.remove_directory(force)])
            return

        self.remove_vrd()
        self.remove_directory()
