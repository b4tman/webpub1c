# webpub1c
1C: Enterprise infobase web publication tool

for publicate 1C: Enterprise infobase with Apache web server
( inspired by [TihonV/vrdmaker](https://github.com/TihonV/vrdmaker) )

as an alternative to standart [webinst](https://1c-dn.com/anticrisis/tools-and-technologies/embedded-web-client/setting-up/) utility

## Synopsis
`webpub1c.py` - _COMMAND_

## Commands
_COMMAND_ is one of the following:
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

## Examples
- `webpub1c.py -h` - show help
- `webpub1c.py list` - list publications
- `webpub1c.py add test` - add publication with name _'test'_ (infobase name)
- `webpub1c.py add test --url my-infobase` - add publication with name _'test'_ and url _'/1c/my-infobase'_ (_'/1c'_ is **url_base** value in config)
- `webpub1c.py set_url test another-infobase` - set url for publication with name _'test'_, to _'/1c/another-infobase'_
- `webpub1c.py get test` - get info about publication with name _'test'_
- `webpub1c.py remove test` - remove publication with name _'test'_
