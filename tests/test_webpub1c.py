import pytest

from webpub1c import *


@pytest.mark.parametrize('input_str,expected_str', [
    ('<img src="test" />', '&lt;img src=&quot;test&quot; /&gt;'),
    ('test1 & test2', 'test1 &amp; test2'),
])
def test_xml_escape(input_str: str, expected_str: str):
    assert xml_escape(input_str) == expected_str


@pytest.mark.parametrize('input_str,expected_str', [
    ('Бухгалтерия 2345', 'buhgalterija-2345'),
    ('true & false', 'true-false'),
])
def test_slugify(input_str: str, expected_str: str):
    assert slugify(input_str) == expected_str


@pytest.mark.parametrize('prefix,url_path,expected_str', [
    ('/base', 'path', '/base/path'),
    ('/base', '/path', '/base/path'),
    ('/base/', 'path', '/base/path'),
    ('/base/', '/path', '/base/path'),
])
def test_urlpath_join(prefix: str, url_path: str, expected_str: str):
    assert urlpath_join(prefix, url_path) == expected_str


@pytest.fixture
def temp_config(tmpdir) -> str:
    configfile = str(tmpdir.join('config.yml'))
    vrd_path = tmpdir.mkdir('vrds')
    dir_path = tmpdir.mkdir('pubs')
    apache_config = tmpdir.join('apache.cfg')
    apache_config.write('#start')

    with open(configfile, 'w') as f:
        yaml.dump({
            'apache_config': str(apache_config),
            'vrd_path': str(vrd_path),
            'dir_path': str(dir_path),
            'url_base': '/1c',
            'platform_path': '/opt/1cv8/x86_64/current',
            'ws_module': 'wsap24.so',
            'vrd_params': {
                'debug': None,
                'server_addr': 'localhost'
            }
        }, f)
    return configfile


def test_has_module(temp_config):
    cmd = Commands(temp_config)
    assert not cmd.has_module()


def test_add_module(temp_config):
    cmd = Commands(temp_config)
    assert not cmd.has_module()
    cmd.add_module()
    assert cmd.has_module()


def test_list(temp_config):
    cmd = Commands(temp_config)
    assert [] == cmd.list()


def test_add(temp_config):
    cmd = Commands(temp_config)
    assert [] == cmd.list()
    assert cmd.add('test123') == '/1c/test123'
    assert ['test123'] == cmd.list()


def test_remove(temp_config):
    cmd = Commands(temp_config)
    assert [] == cmd.list()
    cmd.add('test123')
    assert ['test123'] == cmd.list()
    cmd.remove('test123')
    assert [] == cmd.list()


def test_get(temp_config):
    cmd = Commands(temp_config)
    assert [] == cmd.list()
    cmd.add('test123')
    info = cmd.get('test123')
    assert json.loads(info) == {
        'name': 'test123',
        'url_path': '/1c/test123',
        'directory': os.path.join(cmd._config['dir_path'], 'test123'),
        'vrd_filename': os.path.join(cmd._config['vrd_path'], 'test123.vrd'),
        'infobase_filepath': '',
        'is_file_infobase': False,
    }


def test_set_url(temp_config):
    cmd = Commands(temp_config)
    assert [] == cmd.list()
    cmd.add('test123')
    info = cmd.get('test123')
    info = json.loads(info)
    assert '/1c/test123' == info['url_path']

    cmd.set_url('test123', 'hello-world')
    info = cmd.get('test123')
    info = json.loads(info)
    assert '/1c/hello-world' == info['url_path']

