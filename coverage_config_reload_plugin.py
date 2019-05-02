"""Coverage Config reload Plugin

config.from_file was broken in coveragepy 4.4.2
https://bitbucket.org/ned/coveragepy/issues/616

add_configurer was added in coveragepy 4.5, which also intentionally
broke this plugins hacky get_coverage_config().  The price to be paid.
"""
import sys

import coverage

__version__ = '0.3.0'


class ConfigReloadPlugin(coverage.CoveragePlugin):

    def __init__(self, config=None, now=False):
        self.config = config
        self.done = False
        if now:
            self.reload_config()

    def reload_config(self):
        read_config_files(self.config)
        self.done = True

    def configure(self, config):
        assert not self.done
        if isinstance(config, coverage.Coverage):
            config = config.config
        self.config = config

        self.reload_config()

    def sys_info(self):
        if not self.done:
            try:
                self.reload_config()
            except:
                pass
        return [('config reloader', str(self.done))]


def get_coverage_config():
    """Get coverage config from stack."""
    # Stack
    # 1. get_coverage_config (i.e. this function)
    # 2. coverage_init
    # 3. load_plugins
    frame = sys._getframe(2)
    config = frame.f_locals['config']
    return config


def read_config_file(config, filename):
    rc_file = filename == '.coveragerc'
    # Try the old pre 4.2.2 invocation
    try:
        config.from_file(
            filename,
            section_prefix='' if rc_file else 'coverage:'
        )
        return
    except TypeError:
        pass

    # coverage 5+
    if hasattr(config, 'config_file'):
        config.config_file = filename

    # coverage 4.2.2+
    config.from_file(filename, our_file=rc_file)


def read_config_files(config):
    if not hasattr(config, 'config_files'):
        if config.config_file:
            read_config_file(config, config.config_file)
            return

    config_filenames = config.config_files[:]
    for filename in config_filenames:
        read_config_file(config, filename)

    # restore original as from_file appends to the config_files list
    config.config_files = config_filenames


def coverage_init(reg, options):
    # Try using coverage 4.5
    try:
        reg.add_configurer(ConfigReloadPlugin())
        return
    except AttributeError:
        pass

    # Fallback to using noop added v4.0
    config = get_coverage_config()
    reg.add_noop(ConfigReloadPlugin(config, now=True))
