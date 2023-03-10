#!/usr/bin/env python3


import json
import logging
import os
from typing import List, Optional

import fire
import jinja2
import yaml
from pathvalidate import is_valid_filepath

from .apache_config import ApacheConfig
from .common import (
    VRDConfig,
    files_encoding,
    default_templates_env,
    DictConfig,
    urlpath_join,
)


class Commands:
    """1C: Enterprise infobase web publication tool."""

    def __init__(self, config: str = "webpub1c.yml", verbose: bool = False):
        level = logging.INFO if verbose else logging.WARNING
        logging.basicConfig(level=level)
        self._log = logging.getLogger("webpub1c")
        self._log.setLevel(level)

        with open(config, "r", encoding=files_encoding) as cfg_file:
            self._config: DictConfig = yaml.safe_load(cfg_file)

        vrd_params: Optional[VRDConfig] = self._config.get("vrd_params", None)
        apache_config: str = self._config.get("apache_config", "")
        self._vrd_path: str = self._config.get("vrd_path", "")
        self._dir_path: str = self._config.get("dir_path", "")
        self._url_base: str = self._config.get("url_base", "")

        templates_env = default_templates_env
        if self._config.get("templates", None) is not None:
            templates = self._config["templates"]
            templates_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(templates)
            )

        self._apache_cfg = ApacheConfig(
            apache_config,
            self._vrd_path,
            self._dir_path,
            self._url_base,
            vrd_params,
            templates_env,
        )

    def _is_vrd_path_valid(self) -> bool:
        return os.path.isdir(self._vrd_path)

    def _is_dir_path_valid(self) -> bool:
        return os.path.isdir(self._dir_path)

    def _is_url_base_valid(self) -> bool:
        return is_valid_filepath(
            self._url_base, platform="posix"
        ) and self._url_base.startswith("/")

    def _is_module_valid(self) -> bool:
        if "platform_path" not in self._config:
            return False
        if "ws_module" not in self._config:
            return False
        return os.path.isfile(
            os.path.join(self._config["platform_path"], self._config["ws_module"])
        )

    def check(self) -> None:
        """Check config"""

        print("config:")
        print(json.dumps(self._config, ensure_ascii=False, indent=2))
        print("\n---")
        print(
            "apache cfg: {}".format("ok" if self._apache_cfg.is_valid() else "invalid")
        )
        print("  vrd path: {}".format("ok" if self._is_vrd_path_valid() else "invalid"))
        print("  dir path: {}".format("ok" if self._is_dir_path_valid() else "invalid"))
        print("  url base: {}".format("ok" if self._is_url_base_valid() else "invalid"))
        print(" ws module: {}".format("ok" if self._is_module_valid() else "not found"))

    def has_module(self) -> bool:
        """Ensure apache config has 1cws module"""

        return self._apache_cfg.has_1cws_module()

    def add_module(self) -> None:
        """Add 1cws module to apache config"""

        if self._apache_cfg.has_1cws_module():
            self._log.info("config unchanged")
        else:
            module: str = os.path.join(
                self._config["platform_path"], self._config["ws_module"]
            )
            self._apache_cfg.add_1cws_module(module)
            self._log.info("module added")

    def list(self) -> List[str]:
        """List publications"""

        return list(self._apache_cfg.publications)

    def get(self, ibname: str) -> Optional[str]:
        """Get publication info"""

        publication = self._apache_cfg.get_publication(ibname)
        if publication is None:
            return publication
        return publication.describe()

    def add(
        self,
        ibname: str,
        url: Optional[str] = None,
        file: str = "",
        force: bool = False,
    ) -> str:
        """Add new publication"""

        publication = self._apache_cfg.create_publication(ibname, url, file, force)
        self._apache_cfg.add_publication(publication, force)
        self._log.info(f"publication added: {ibname}")
        return publication.url_path

    def set_url(self, ibname: str, url: str) -> None:
        """Set publication url"""

        publication = self._apache_cfg.get_publication(ibname)
        if publication is None:
            raise KeyError(f'infobase "{ibname}" not publicated')

        publication.url_path = urlpath_join(self._url_base, url)
        self._apache_cfg.remove_publication(publication.name, destroy=False)
        self._apache_cfg.add_publication(publication)
        self._log.info(f"publication changed: {ibname}")

    def remove(self, ibname: str, force: bool = False) -> None:
        """Remove publication"""

        self._apache_cfg.remove_publication(ibname, force=force)
        self._log.info(f"publication removed: {ibname}")


def main():
    fire.Fire(Commands)


if __name__ == "__main__":
    main()
