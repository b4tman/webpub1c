import os
import re
from typing import Optional, Iterator, List

import jinja2

from .common import VRDConfig, default_templates_env, files_encoding, urlpath_join
from .webpublication import WebPublication


class ApacheConfig:
    """apache config"""

    start_tag: str = "# --- WEBPUB1C PUBLICATION START:"
    end_tag: str = "# --- WEBPUB1C PUBLICATION END:"

    def __init__(
        self,
        filename: str,
        vrd_path: str,
        dir_path: str,
        url_base: str,
        vrd_params: Optional[VRDConfig] = None,
        templates_env: Optional[jinja2.Environment] = None,
    ):
        self.filename: str = filename
        self.vrd_path: str = vrd_path
        self.dir_path: str = dir_path
        self.url_base: str = url_base
        self.vrd_params: Optional[VRDConfig] = vrd_params

        if templates_env is None:
            self.templates_env = default_templates_env
        else:
            self.templates_env = templates_env

    def is_valid(self) -> bool:
        return os.path.isfile(self.filename)

    def _check(self):
        if not self.is_valid():
            raise ValueError("invalid apache config")

    @property
    def text(self) -> str:
        self._check()

        with open(self.filename, "r", encoding=files_encoding) as f:
            txt: str = f.read()
        return txt

    def has_1cws_module(self) -> bool:
        ws_expr = re.compile(r"^LoadModule\s_1cws_module\s.*$", re.M)
        result: bool = ws_expr.search(self.text) is not None

        return result

    def add_1cws_module(self, module_filename: str):
        if self.has_1cws_module():
            return

        with open(self.filename, "a", encoding=files_encoding) as f:
            f.write(f'\nLoadModule _1cws_module "{module_filename}"\n')

    @property
    def publications(self) -> Iterator[str]:
        start_expr = re.compile(
            r"^{}\s(.+)$".format(re.escape(ApacheConfig.start_tag)), re.M
        )
        for match in start_expr.finditer(self.text):
            yield match.group(1).strip()

    def iter(self) -> Iterator[WebPublication]:
        start_pub = re.compile(r"^{}\s".format(re.escape(ApacheConfig.start_tag)))
        start_name = re.compile(r"^{}\s(.+)$".format(re.escape(ApacheConfig.start_tag)))
        end_pub = re.compile(r"^{}\s".format(re.escape(ApacheConfig.end_tag)))

        is_pub_started: bool = False
        cur_pub_name: str = ""
        cur_pub_lines: List[str] = []
        lines: List[str] = self.text.splitlines(keepends=True)
        for line in lines:
            if is_pub_started:
                if end_pub.match(line):
                    if 0 == len(cur_pub_lines):
                        raise ValueError("can't parse config :(")
                    publication = WebPublication.from_config(
                        cur_pub_name,
                        "".join(cur_pub_lines),
                        templates_env=self.templates_env,
                    )
                    yield publication
                    cur_pub_name = ""
                    cur_pub_lines.clear()
                    is_pub_started = False
                else:
                    cur_pub_lines.append(line)
                continue
            if start_pub.match(line):
                is_pub_started = True
                match = start_name.match(line)
                if match is None:
                    raise ValueError("can't parse config :(")
                cur_pub_name = match.group(1).strip()

    def is_publicated(self, ibname: str) -> bool:
        return ibname in self.publications

    def create_publication(
        self,
        ibname: str,
        url_path: Optional[str] = None,
        infobase_filepath="",
        force: bool = False,
    ) -> WebPublication:
        if self.is_publicated(ibname) and not force:
            raise KeyError(f'infobase "{ibname}" already publicated')

        publication = WebPublication(
            ibname,
            vrd_params=self.vrd_params,
            templates_env=self.templates_env,
            infobase_filepath=infobase_filepath,
        )
        publication.generate_paths(self.dir_path, self.vrd_path, self.url_base)

        if url_path is not None:
            publication.url_path = urlpath_join(self.url_base, url_path)

        if not (force or publication.is_ok_to_create()):
            raise ValueError(f"can't create publication: {publication.describe()}")

        publication.create(force)
        return publication

    def add_publication(self, publication: WebPublication, force: bool = False) -> None:
        if self.is_publicated(publication.name):
            if force:
                self.remove_publication(publication.name, destroy=False)
            else:
                raise KeyError(f'infobase "{publication.name}" already publicated')

        pub_cfg = publication.to_config()
        with open(self.filename, "a", encoding=files_encoding) as f:
            f.write(f"\n{ApacheConfig.start_tag} {publication.name}\n")
            f.write(pub_cfg)
            f.write(f"\n{ApacheConfig.end_tag} {publication.name}")

    def get_publication(self, ibname: str) -> Optional[WebPublication]:
        if not self.is_publicated(ibname):
            return None

        start_pub = re.compile(
            r"^{}\s{}".format(re.escape(ApacheConfig.start_tag), re.escape(ibname))
        )
        end_pub = re.compile(
            r"^{}\s{}".format(re.escape(ApacheConfig.end_tag), re.escape(ibname))
        )

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
            raise ValueError("can't parse config :(")

        publication = WebPublication.from_config(
            ibname, "".join(pub_lines), templates_env=self.templates_env
        )
        return publication

    def remove_publication(
        self, ibname: str, destroy: bool = True, force: bool = False
    ):
        if not self.is_publicated(ibname):
            raise KeyError(f'infobase "{ibname}" not publicated')

        start_pub = re.compile(
            r"^{}\s{}".format(re.escape(ApacheConfig.start_tag), re.escape(ibname))
        )
        end_pub = re.compile(
            r"^{}\s{}".format(re.escape(ApacheConfig.end_tag), re.escape(ibname))
        )
        is_pub_started: bool = False

        # filter lines for new config and publication
        pub_lines: List[str] = []
        new_lines: List[str] = []
        lines: List[str] = self.text.splitlines(keepends=True)
        for line in lines:
            if is_pub_started:
                if end_pub.match(line):
                    is_pub_started = False
                    # remove last empty line
                    if len(new_lines) > 0:
                        if new_lines[-1].strip() == "":
                            new_lines.pop()
                else:
                    pub_lines.append(line)
                continue
            if start_pub.match(line):
                is_pub_started = True
                continue
            new_lines.append(line)

        # remove vrd and directory
        if destroy:
            publication = WebPublication.from_config(ibname, "".join(pub_lines))
            publication.remove(force)

        # write new config
        with open(self.filename, "w", encoding=files_encoding) as f:
            f.write("".join(new_lines))
