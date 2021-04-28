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

    def __init__(self, filename: str, vrd_path: str):
        self.filename = filename
        self.vrd_path = vrd_path

    def is_valid(self) -> bool:
        return os.path.exists(self.filename)

    def _check(self):
        if not self.is_valid():
            raise ValueError('invalid apache config')

    @property
    def publications(self) -> List[str]:
        self._check()

        result: List[str] = []
        start_expr = re.compile('^{}\\s([^\\s]*)$'.format(re.escape(ApacheConfig.start_tag)), re.M)
        with open(self.filename, 'r') as f:
            txt = f.read()
            for match in start_expr.finditer(txt):
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
            f.write(f'\n{ApacheConfig.end_tag} {ibname}\n')

    def remove_publication(self, ibname: str):
        if not self.is_publicated(ibname):
            raise KeyError(f'infobase "{ibname}" not publicated')

        start_pub = re.compile('^{}\\s{}'.format(re.escape(ApacheConfig.start_tag), re.escape(ibname)))
        end_pub = re.compile('^{}\\s{}'.format(re.escape(ApacheConfig.end_tag), re.escape(ibname)))
        lines: List[str] = []
        skip_flag: bool = False
        with open(self.filename, "r+") as f:
            for line in f:
                lines.append(line)

            f.seek(0)
            f.truncate()

            for line in lines:
                if skip_flag:
                    if end_pub.match(line):
                        skip_flag = False
                    continue
                if start_pub.match(line):
                    skip_flag = True
                    continue
                f.write(line)
        return


class Commands:
    """1C: Enterprice infobase web publication tool."""

    def __init__(self, config='w31c.yml', verbose=False):
        level = logging.INFO if verbose else logging.WARNING
        logging.basicConfig(level=level)
        logging.getLogger("w31c").setLevel(level)
        with open(config, 'r') as cfg_file:
            self._config = yaml.safe_load(cfg_file)
            self._apache_cfg = ApacheConfig(self._config['apache_config'], self._config['vrd_path'])

    def list(self):
        """ List publications """
        return self._apache_cfg.publications

    def check(self):
        """ Check config """

        print('config: {}'.format(self._config))
        apache_cfg_valid = self._apache_cfg.is_valid()
        print('apache cfg is {}'.format('valid' if apache_cfg_valid else 'invalid'))
        return

    def add(self, ibname):
        """ Add new publication """
        self._apache_cfg.add_publication(ibname)
        print(f'publication added: {ibname}')

    def remove(self, ibname):
        """ Remove publication """
        self._apache_cfg.remove_publication(ibname)
        print(f'publication removed: {ibname}')


def main(args=None):
    fire.Fire(Commands, command=args)


if __name__ == "__main__":
    main()
