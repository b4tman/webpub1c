from typing import List

import fire
import jinja2
import logging
import yaml
import os
import re


class ApacheConfig:
    """ apache config """

    start_tag: str = '# --- W31C PUBLICATION START:'
    end_tag: str = '# --- W31C PUBLICATION END:'

    def __init__(self, filename: str):
        self.filename = filename

    def is_valid(self) -> bool:
        return os.path.exists(self.filename)

    def _check(self):
        if not self.is_valid():
            raise ValueError('invalid apache config')

    @property
    def publications(self) -> List[str]:
        self._check()

        result = []
        start_expr = re.compile('^{}\\s([^\\s]*)$'.format(re.escape(ApacheConfig.start_tag)), re.M)
        with open(self.filename, 'r') as f:
            txt = f.read()
            for match in start_expr.finditer(txt):
                result.append(match.group(1))

        return result

    def is_publicated(self, ibname: str):
        return ibname in self.publications

    def add_publication(self, ibname: str):
        if self.is_publicated(ibname):
            raise KeyError(f'infobase "{ibname}" already publicated')

        return

    def remove_publication(self, ibname: str):
        if not self.is_publicated(ibname):
            raise KeyError(f'infobase "{ibname}" not publicated')

        return


class Commands:
    """1C: Enterprice infobase web publication tool."""

    def __init__(self, config='w31c.yml', verbose=False):
        level = logging.INFO if verbose else logging.WARNING
        logging.basicConfig(level=level)
        logging.getLogger("w31c").setLevel(level)
        with open(config, 'r') as cfg_file:
            self._config = yaml.safe_load(cfg_file)
            self._apache_cfg = ApacheConfig(self._config['apache_config'])

    def list(self):
        """ List publications """
        return self._apache_cfg.publications

    def check(self):
        """ Check config """

        print('config: {}'.format(self._config))
        apache_cfg_valid = self._apache_cfg.is_valid()
        print('apache cfg is {}'.format('valid' if apache_cfg_valid else 'invalid'))
        return

    def add(self, ibase):
        """ Add new publication """
        self._apache_cfg.add_publication(ibase)
        print(f'publication added: {ibase}')

    def remove(self, ibase):
        """ Remove publication """
        self._apache_cfg.remove_publication(ibase)
        print(f'publication removed: {ibase}')


def main(args=None):
    fire.Fire(Commands, command=args)


if __name__ == "__main__":
    main()
