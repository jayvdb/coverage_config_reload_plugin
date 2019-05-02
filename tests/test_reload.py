from distutils.version import LooseVersion
from unittest import TestCase

from unittest_mixins import TempDirMixin


from coverage import __version__ as coverage_version
from coverage.backward import StringIO
from coverage.control import Coverage


class ConfigReloadPluginTest(TempDirMixin, TestCase):
    """Test plugin through the Coverage class."""

    def test_no_reload_plugin(self):
        debug_out = StringIO()
        cov = Coverage(debug=['sys'])
        cov._debug_file = debug_out
        cov.set_option('run:plugins', [])
        cov.start()
        cov.stop()

        out_lines = [line.strip() for line in debug_out.getvalue().splitlines()]
        self.assertIn('plugins.file_tracers: -none-', out_lines)

        expected_end = [
            '-- end -------------------------------------------------------',
        ]
        self.assertEqual(expected_end, out_lines[-len(expected_end):])

        if LooseVersion(coverage_version) >= LooseVersion('4.6'):
            self.assertIn('plugins.configurers: -none-', out_lines)

        assert cov.config.get_option('report:ignore_errors') is False

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
            'configreload: True',
            '-- end -------------------------------------------------------',
        ]
        self.assertEqual(expected_end, out_lines[-len(expected_end):])

        if LooseVersion(coverage_version) >= LooseVersion('4.6'):
            self.assertIn('plugins.configurers: coverage_config_reload_plugin.ConfigReloadPlugin', out_lines)

    def _check_config(self, filename, own_rc):
        section = 'report' if own_rc else 'coverage:report'

        # Force own rc for pre 4.4.1
        if LooseVersion(coverage_version) < LooseVersion('4.4.1'):
            self.make_file(filename, """\
                [report]
                ignore_errors = true
                """)
        else:
            self.make_file(filename, """\
                [{}]
                ignore_errors = true
                """.format(section))

        debug_out = StringIO()
        cov = Coverage(config_file=filename, debug=['sys'])
        assert cov.config.get_option('report:ignore_errors') is True
        cov._debug_file = debug_out

        self.make_file(filename, """\
            [{}]
            ignore_errors = off
            """.format(section))

        cov.set_option('run:plugins', ['coverage_config_reload_plugin'])
        cov.start()
        cov.stop()

        assert cov.config.get_option('report:ignore_errors') is False

    def test_reload_config_rc(self):
        self._check_config('coveragerc_test_config', True)

    def test_reload_config_not_rc(self):
        self._check_config('coveragerc_test_config', False)

    def test_reload_config_toxini(self):
        self._check_config('tox.ini', False)

    def test_reload_config_setupcfg(self):
        self._check_config('setup.cfg', False)

    def test_reload_config_coveragerc(self):
        self._check_config('.coveragerc', True)
