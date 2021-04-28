from typing import List, Dict

import fire
import jinja2
import logging
import yaml
import os
import re
import glob


class VrdManager:
    def __init__(self, path: str):
        self.path = path

    def is_valid(self) -> bool:
        return os.path.exists(self.path)

    def _check(self):
        if not self.is_valid():
            raise ValueError('invalid vrd path')

    @property
    def files(self) -> List[str]:
        self._check()

        result: List[str] = []
        for file in glob.glob(os.path.join(self.path, '*.vrd')):
            ibname: str = os.path.splitext(os.path.basename(file))[0]
            result.append(ibname)
        return result

    def filename(self, ibname: str) -> str:
        return os.path.join(self.path, f'{ibname}.vrd')

    def exists(self, ibname: str) -> bool:
        return os.path.exists(self.filename(ibname))

    def add(self, ibname, params: Dict):
        self._check()

        if self.exists(ibname):
            raise KeyError(f'vrd file "{ibname}" exists')
        vrd_params = {
            'ibname': ibname
        }
        vrd_params.update(params)
        env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
        template = env.get_template('vrd.xml')

        vrd_data = template.render(ctx=vrd_params)
        with open(self.filename(ibname), "w") as f:
            f.write(vrd_data)

    def remove(self, ibname):
        self._check()

        if not self.exists(ibname):
            raise KeyError(f'vrd file "{ibname}" not found')
        os.unlink(self.filename(ibname))


class ApacheConfig:
    """ apache config """

    start_tag: str = '# --- W31C PUBLICATION START:'
    end_tag: str = '# --- W31C PUBLICATION END:'

    def __init__(self, filename: str, vrd_path: str):
        self.filename = filename
        self.vrd_path = vrd_path

    def is_valid(self) -> bool:
        return os.path.exists(self.filename)

    def _check(self):
        if not self.is_valid():
            raise ValueError('invalid apache config')

    @property
    def text(self) -> str:
        self._check()

        txt: str = ''
        with open(self.filename, 'r') as f:
            txt = f.read()
        return txt

    def has_1cws_module(self) -> bool:
        ws_expr = re.compile('^LoadModule\\s_1cws_module\\s[^\\s]*$', re.M)
        result: bool = (ws_expr.search(self.text) is not None)

        return result

    def add_1cws_module(self, module_filename: str):
        if self.has_1cws_module():
            return

        with open(self.filename, "a") as f:
            f.write(f'\nLoadModule _1cws_module "{module_filename}"\n')

    @property
    def publications(self) -> List[str]:
        result: List[str] = []
        start_expr = re.compile('^{}\\s([^\\s]*)$'.format(re.escape(ApacheConfig.start_tag)), re.M)
        for match in start_expr.finditer(self.text):
            result.append(match.group(1))

        return result

    def is_publicated(self, ibname: str) -> bool:
        return ibname in self.publications

    def add_publication(self, ibname: str):
        if self.is_publicated(ibname):
            raise KeyError(f'infobase "{ibname}" already publicated')

        env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
        template = env.get_template('apache_pub.cfg')
        pub_params = {
            'vrd_filename': os.path.join(self.vrd_path, f'{ibname}.vrd'),
            'ibname': ibname
        }
        pub = template.render(ctx=pub_params)

        with open(self.filename, "a") as f:
            f.write(f'\n{ApacheConfig.start_tag} {ibname}\n')
            f.write(pub)
            f.write(f'\n{ApacheConfig.end_tag} {ibname}')

    def remove_publication(self, ibname: str):
        if not self.is_publicated(ibname):
            raise KeyError(f'infobase "{ibname}" not publicated')

        start_pub = re.compile('^{}\\s{}'.format(re.escape(ApacheConfig.start_tag), re.escape(ibname)))
        end_pub = re.compile('^{}\\s{}'.format(re.escape(ApacheConfig.end_tag), re.escape(ibname)))
        is_pub_started: bool = False
        lines: List[str] = self.text.splitlines()
        with open(self.filename, "w") as f:
            for line in lines:
                if is_pub_started:
                    if end_pub.match(line):
                        is_pub_started = False
                    continue
                if start_pub.match(line):
                    is_pub_started = True
                    continue
                f.write(line)
        return


class Commands:
    """1C: Enterprice infobase web publication tool."""

    def __init__(self, config='w31c.yml', verbose=False):
        level = logging.INFO if verbose else logging.WARNING
        logging.basicConfig(level=level)
        self._log = logging.getLogger("w31c")
        self._log.setLevel(level)

        with open(config, 'r') as cfg_file:
            self._config = yaml.safe_load(cfg_file)
        self._apache_cfg = ApacheConfig(self._config['apache_config'], self._config['vrd_path'])
        self._vrdmgr = VrdManager(self._config['vrd_path'])

    def list(self):
        """ List publications """

        self._log.info('vrds: %s', ', '.join(self._vrdmgr.files))
        return self._apache_cfg.publications

    def has_module(self) -> bool:
        """ Ensure apache config has 1cws module """

        return self._apache_cfg.has_1cws_module()

    def add_module(self):
        """ Add 1cws module to apache config """

        if self._apache_cfg.has_1cws_module():
            self._log.info('config unchanged')
        else:
            self._apache_cfg.add_1cws_module(os.path.join(self._config['platform_path'], self._config['ws_module']))
            self._log.info('module added')

    def check(self):
        """ Check config """

        print('config: {}'.format(self._config))
        apache_cfg_valid = self._apache_cfg.is_valid()
        print('apache cfg is {}'.format('valid' if apache_cfg_valid else 'invalid'))
        return

    def add(self, ibname):
        """ Add new publication """

        self._apache_cfg.add_publication(ibname)
        if self._vrdmgr.exists(ibname):
            self._log.warning(f'vrd file for {ibname} exists')
        else:
            self._vrdmgr.add(ibname, self._config['vrd_params'])

        self._log.info(f'publication added: {ibname}')

    def remove(self, ibname):
        """ Remove publication """

        self._apache_cfg.remove_publication(ibname)
        if self._vrdmgr.exists(ibname):
            self._vrdmgr.remove(ibname)
        else:
            self._log.warning(f'vrd file for {ibname} not found')
        self._log.info(f'publication removed: {ibname}')

if __name__ == "__main__":
    fire.Fire(Commands)
