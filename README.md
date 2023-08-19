[![Documentation Status](https://readthedocs.org/projects/webpub1c/badge/?version=latest)](https://webpub1c.readthedocs.io/en/latest/?badge=latest)

# webpub1c

1C: Enterprise infobase web publication tool.

For 1C: Enterprise infobase publication with Apache web server
(inspired by [TihonV/vrdmaker](https://github.com/TihonV/vrdmaker) ).
As an alternative to standard [webinst](https://1c-dn.com/anticrisis/tools-and-technologies/embedded-web-client/setting-up/) utility.

All publication data stored into apache configuration file and vrd files.
With this tool you can **list**, **add** and **remove** publications.

## Installation

To install using [pip](https://pypi.python.org/pypi/pip), run:

```sh
pip install git+https://github.com/b4tman/webpub1c
```

Or download source code and install using [Poetry](https://python-poetry.org/docs/):

```sh
# install poetry
pip install poetry
# install project and deps to virtualenv
poetry install
# run
poetry run webpub1c
```

## Configuration

The configuration is stored in [YAML](https://yaml.org) file `webpub1c.yml` located in the current working directory.

~~~yaml
apache_config: example/apache.cfg # path to Apache config file
vrd_path: example/vrds  # path where to save .vrd files
dir_path: example/pubs  # path where to save publication directories
url_base: /1c # prefix for all publications
platform_path: /opt/1cv8/x86_64/current # path to installed 1C:Enterprise platform bin dir
ws_module: wsap24.so # 1c module file name (this one is for Apache 2.4)
vrd_params: # template params for (all) vrd files
  debug: # enable debug or not (bool)
  server_addr: localhost # server addr
~~~

## Usage

### Synopsis

`webpub1c` _COMMAND_

### Commands

- `add` - Add new publication
- `add_module`
       Add 1cws module to apache config
- `check`
       Check config
- `get`
       Get publication info
- `has_module`
       Ensure apache config has 1cws module
- `list`
       List publications
- `remove`
       Remove publication
- `set_url`
       Set publication url

### Examples

- `webpub1c -h` - show help
- `webpub1c list` - list publications
- `webpub1c add test` - add publication with name _'test'_ (infobase name)
- `webpub1c add test --url my-infobase` - add publication with name _'test'_ and url _'/1c/my-infobase'_ (_'/1c'_ is **url_base** value in config)
- `webpub1c add test --file /path/to/infobase` - add publication with name _'test'_ for file infobase in _'/path/to/infobase'_ folder
- `webpub1c set_url test another-infobase` - set url for publication with name _'test'_, to _'/1c/another-infobase'_
- `webpub1c get test` - get info about publication with name _'test'_
- `webpub1c remove test` - remove publication with name _'test'_
