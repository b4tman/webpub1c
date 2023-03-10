# webpub1c

1C: Enterprise infobase web publication tool

for publicate 1C: Enterprise infobase with Apache web server
( inspired by [TihonV/vrdmaker](https://github.com/TihonV/vrdmaker) )

as an alternative to standart [webinst](https://1c-dn.com/anticrisis/tools-and-technologies/embedded-web-client/setting-up/) utility

## Installation

To install using [pip](https://pypi.python.org/pypi/pip), run:

```sh
pip install git+https://github.com/b4tman/webpub1c
```

Or download source code and install using poetry:

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
