import json
import os

import pytest
import yaml

from webpub1c.cli import Commands


@pytest.fixture
def temp_config(tmpdir) -> str:
    configfile = str(tmpdir.join('config.yml'))
    vrd_path = tmpdir.mkdir('vrds')
    dir_path = tmpdir.mkdir('pubs')
    apache_config = tmpdir.join('apache.cfg')
    apache_config.write('#start\n')

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


@pytest.fixture
def cmd(temp_config) -> Commands:
    return Commands(temp_config)


def test_has_module(cmd):
    assert not cmd.has_module()


def test_add_module(cmd):
    assert not cmd.has_module()
    cmd.add_module()
    assert cmd.has_module()


def test_list(cmd):
    assert [] == cmd.list()


def test_add(cmd):
    assert [] == cmd.list()
    assert cmd.add('test123') == '/1c/test123'
    assert ['test123'] == cmd.list()


def test_add_force(cmd):
    cmd.add('test123')
    assert cmd.list() == ['test123']
    with pytest.raises(KeyError, match='already publicated'):
        cmd.add('test123')
    cmd.add('test123', force=True)
    assert cmd.list() == ['test123']


def test_add_force_dir_exist(cmd):
    os.mkdir(os.path.join(cmd._config['dir_path'], 'test123'))
    with pytest.raises(ValueError, match='can\'t create publication'):
        cmd.add('test123')
    cmd.add('test123', force=True)
    assert cmd.list() == ['test123']


def test_add_file(cmd):
    assert [] == cmd.list()
    assert cmd.add('test_file', file='/test/file') == '/1c/test_file'
    assert ['test_file'] == cmd.list()
    info = cmd.get('test_file')
    info = json.loads(info)
    assert '/test/file' == info['infobase_filepath']
    assert info['is_file_infobase']


def test_remove(cmd):
    assert [] == cmd.list()
    cmd.add('test123')
    assert ['test123'] == cmd.list()
    cmd.remove('test123')
    assert [] == cmd.list()


def test_remove_force(cmd):
    cmd.add('test123')

    lockfile = os.path.join(cmd._config['dir_path'], 'test123', 'lock')
    with open(lockfile, 'w') as f:
        f.write('')

    with pytest.raises(OSError):
        cmd.remove('test123')
    cmd.remove('test123', force=True)
    assert cmd.list() == []


def test_remove_clean_cfg(cmd):
    """
    the contents of the apache configuration
    before adding and after removing should be the same
    """
    assert [] == cmd.list()
    cfg_before_add = cmd._apache_cfg.text
    cmd.add('test123')
    cmd.add('test456')
    cfg_before_remove = cmd._apache_cfg.text
    cmd.remove('test123')
    cmd.remove('test456')
    cfg_after_remove = cmd._apache_cfg.text

    assert cfg_before_add != cfg_before_remove
    assert cfg_before_add == cfg_after_remove


def test_get(cmd):
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


def test_set_url(cmd):
    assert [] == cmd.list()
    cmd.add('test123')
    info = cmd.get('test123')
    info = json.loads(info)
    assert '/1c/test123' == info['url_path']

    cmd.set_url('test123', 'hello-world')
    info = cmd.get('test123')
    info = json.loads(info)
    assert '/1c/hello-world' == info['url_path']
