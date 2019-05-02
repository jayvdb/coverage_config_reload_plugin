# coverage config reload plugin

This is a plugin for coveragepy that forces it to reload its
configuration.  Typically this is used when the config file needs to
be dynamic, or the environment which is used when parsing the
config file.

Place as the last plugin to be loaded, this plugin will
reloads the configuration files after other plugins have been loaded
and performed their changes to the configuration file or environment.

This plugin was developed as a helper for
[coverage-env-plugin](https://github.com/jayvdb/coverage_env_plugin/),
so it does not need worry about the internals of coveragepy.
