"""Coverage Config reload Plugin

config.from_file was broken in coveragepy 4.4.1
https://bitbucket.org/ned/coveragepy/issues/616

add_configurer was added in coveragepy 4.5, but also included
a few easter eggs to make this plugin a tiny bit harder.
"""
import sys

import coverage
from coverage.backward import configparser

__version__ = '0.3.0'


class PluginBase(coverage.CoveragePlugin):

    @classmethod
    def _register(cls, reg, options, now=True):
        config = get_coverage_config()
        plugin = cls(reg, options, config, now)

        # Try using coverage 4.5
        try:
            reg.add_configurer(plugin)
            return plugin
        except AttributeError:
            pass

        # Fallback to using noop added v4.0
        try:
            reg.add_noop(plugin)
        except Exception:
            reg._add_plugin(plugin, None)
        return plugin

    def __init__(self, reg, options, config=None, now=False):
        self._name = self.__class__.__name__.lower().replace('plugin', '')
        self.reg = reg
        self.options = options
        self.config = config
        self.done = False
        self.status = None
        if now:
            self.do()

    def configure(self, config):
        if isinstance(config, coverage.Coverage):
            config = config.config
        self.config = config

        self.do()

    def do(self):
        if not self.done:
            self._do()
            self.done = True

    def sys_info(self):
        if not self.done:
            try:
                self.do()
            except:
                pass
        return [(self._name,
                 str(self.status) if self.status else str(self.done))]


class ConfigReloadPlugin(PluginBase):

    def _do(self):
        read_config_files(self.config)


def get_coverage_config():
    """Get coverage config from stack."""
    # Stack
    # 1. get_coverage_config (i.e. this function)
    # 2. PluginBase._register
    # 3. coverage_init
    # 4. load_plugins
    frame = sys._getframe(3)
    config = frame.f_locals['config']
    return config


def read_config_file(config, filename):
    if filename == '.coveragerc':
       rc_file = True
    elif filename in ('tox.ini', 'setup.cfg'):
       rc_file = False
    else:
       # Very likely all other config files are 'own rc' files.
       # However the cost here is minimal for correctness and this
       # reduces the chance it can be broken by future childishness :P
       parser = configparser.RawConfigParser()
       parser.read(filename)
       sections = parser.sections()
       rc_file = not any(section.startswith('coverage:')
                         for section in sections)

    # Try the old pre 4.4.1 invocation
    try:
        return config.from_file(
            filename,
            section_prefix='' if rc_file else 'coverage:'
        )
    except TypeError:
        pass

    # coverage 5+
    if hasattr(config, 'config_file'):
        config.config_file = filename

    # coverage 4.4.1+
    return config.from_file(filename, our_file=rc_file)


def read_config_files(config):
    if not hasattr(config, 'config_files'):
        if config.config_file:
            rv = read_config_file(config, config.config_file)
            assert rv is True
            return

    config_filenames = config.config_files[:]
    for filename in config_filenames:
        rv = read_config_file(config, filename)
        assert rv is True

    # restore original as from_file appends to the config_files list
    config.config_files = config_filenames


def coverage_init(reg, options):
    ConfigReloadPlugin._register(reg, options)
