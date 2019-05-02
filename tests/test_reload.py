from distutils.version import LooseVersion
from unittest import TestCase

from unittest_mixins import TempDirMixin


from coverage import __version__ as coverage_version
from coverage.backward import StringIO
from coverage.control import Coverage


class ConfigReloadPluginTest(TempDirMixin, TestCase):
    """Test plugins through the Coverage class."""

    def _test_no_reload_plugin(self):
        debug_out = StringIO()
        cov = Coverage(debug=['sys'])
        cov._debug_file = debug_out
        cov.set_option('run:plugins', [])
        cov.start()
        cov.stop()

        out_lines = [line.strip() for line in debug_out.getvalue().splitlines()]
        self.assertIn('plugins.file_tracers: -none-', out_lines)
        if LooseVersion(coverage_version) >= LooseVersion('4.5'):
            self.assertIn('plugins.configurers: plugin_no_sys_info.Plugin', out_lines)
        expected_end = [
            '-- sys: plugin_no_sys_info.Plugin ----------------------------',
            '-- end -------------------------------------------------------',
            ]
        self.assertEqual(expected_end, out_lines[-len(expected_end):])

    def test_plugin_init(self):
        self.make_file('coveragerc_test_config', '')

        debug_out = StringIO()
        cov = Coverage(config_file='coveragerc_test_config', debug=['sys'])
        cov._debug_file = debug_out
        cov.set_option('run:plugins', ['coverage_config_reload_plugin'])
        cov.start()
        cov.stop()

        out_lines = [line.strip() for line in debug_out.getvalue().splitlines()]
        self.assertIn('plugins.file_tracers: -none-', out_lines)

        expected_end = [
            '-- sys: coverage_config_reload_plugin.ConfigReloadPlugin -----',
            'config reloader: True',
            '-- end -------------------------------------------------------',
        ]
        self.assertEqual(expected_end, out_lines[-len(expected_end):])

        #if LooseVersion(coverage_version) >= LooseVersion('4.5'):
        #    self.assertIn('plugins.configurers: coverage_config_reload_plugin.ConfigReloadPlugin', out_lines)

    def test_reload_config(self):
        self.make_file('coveragerc_test_config', """\
            [coverage:report]
            ignore_errors = true
            [report]
            ignore_errors = true
            """)

        debug_out = StringIO()
        cov = Coverage(config_file='coveragerc_test_config', debug=['sys'])
        assert cov.config.get_option('report:ignore_errors') is True
        cov._debug_file = debug_out

        self.make_file('coveragerc_test_config', """\
            [coverage:report]
            ignore_errors = off
            [report]
            ignore_errors = off
            """)

        cov.set_option('run:plugins', ['coverage_config_reload_plugin'])
        cov.start()
        cov.stop()

        assert cov.config.get_option('report:ignore_errors') is False
