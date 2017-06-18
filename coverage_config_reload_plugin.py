"""Coverage Config reload Plugin"""
import sys

def get_coverage_config():
    """Get coverage config from stack."""
    # Stack
    # 1. get_coverage_config (i.e. this function)
    # 2. coverage_init
    # 3. load_plugins
    frame = sys._getframe(2)
    config = frame.f_locals['config']
    return config

def read_config_files(config):
    config_filenames = config.config_files[:]
    for filename in config_filenames:
        prefix = '' if filename == '.coveragerc' else 'coverage:'
        config.from_file(filename, section_prefix=prefix)

    # restore original as from_file appends to the config_files list
    config.config_files = config_filenames

def coverage_init(reg, options):
    config = get_coverage_config()
    read_config_files(config)
