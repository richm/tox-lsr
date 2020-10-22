#                                                         -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
"""Install tox-lsr hooks to tox."""

import os

import pkg_resources
from tox import hookimpl
from tox.config import Config, TestenvConfig, testenvprefix

try:
    from tox.config import ParseIni as ToxParseIni  # tox 3.4.0+
except ImportError:
    from tox.config import parseini as ToxParseIni


TEST_SCRIPTS_SUBDIR = "data/test_scripts"


# code uses some protected members such as _cfg, _parser, _reader
# pylint: disable=protected-access


def prop_is_set(envconf: TestenvConfig, propname: str) -> bool:
    """Determine if property propname was explicitly set in envconf.

    Use a heuristic to determine if the property named propname was
    explicitly set in envconf (as opposed to being set to a default
    value).  In some cases, usually for scalar types, we cannot
    determine if the value was set.  For non-scalar types, assume
    that the property was set if the value is non-empty.
    Return True if the property was set, False otherwise.
    """

    section_name = testenvprefix + envconf.envname
    cfg = envconf._reader._cfg.sections.get(section_name, {})
    tecfg = envconf._reader._cfg.sections.get("testenv", {})
    if propname in cfg or propname in tecfg:
        return True
    val = getattr(envconf, propname)
    # see if val is one of the scalar types
    if isinstance(val, str):
        return len(val) > 0  # assume empty string is unset
    if isinstance(val, (int, float, bool)):
        return False  # no way to tell
    # not a simple scalar type - see if empty
    return bool(val)


def merge_prop_values(
    propname: str, envconf: TestenvConfig, def_envconf: TestenvConfig
) -> None:
    """If propname is one of the values we can merge, do the merge."""

    if propname == "setenv":  # merge env vars
        for envvar in def_envconf.setenv.keys():
            if envvar not in envconf.setenv:
                envconf.setenv[envvar] = def_envconf.setenv[envvar]
    elif propname == "deps":
        envconf.deps = list(set(envconf.deps + def_envconf.deps))
    elif propname == "passenv":
        envconf.passenv = envconf.passenv.union(def_envconf.passenv)
    elif propname == "whitelist_externals":
        envconf.deps = list(
            set(envconf.whitelist_externals + def_envconf.whitelist_externals)
        )


def merge_envconf(envconf: TestenvConfig, def_envconf: TestenvConfig) -> None:
    """Merge the default envconfig from def_envconf into the given envconf."""

    # access what was actually set in the customized tox.ini so that
    # we can override the properties which were not set
    for propname in dir(def_envconf):
        if prop_is_set(def_envconf, propname):
            if not prop_is_set(envconf, propname):
                try:
                    setattr(envconf, propname, getattr(def_envconf, propname))
                except AttributeError:  # some props cannot be set
                    pass
            else:
                merge_prop_values(propname, envconf, def_envconf)


def merge_ini(config: Config, default_config: Config) -> None:
    """Merge the parsed ini config values/sections."""

    for def_section_name, def_section in default_config._cfg.sections.items():
        section = config._cfg.sections.setdefault(
            def_section_name, def_section
        )
        if section is not def_section:
            for key, value in def_section.items():
                if key not in section:
                    section[key] = value


def merge_config(config: Config, default_config: Config) -> None:
    """Merge default_config into config."""

    # merge the top level config properties
    for propname in dir(default_config):
        # set in config if not set and it's set in default
        if (
            propname in default_config._cfg.sections["tox"]
            and propname not in config._cfg.sections["tox"]  # noqa: W503
        ):
            setattr(config, propname, getattr(default_config, propname))
    # merge the top level config properties that are set implicitly
    if not config.envlist_explicit:
        config.envlist_default = list(
            set(config.envlist_default + default_config.envlist_default)
        )
        config.envlist = list(set(config.envlist + default_config.envlist))

    # merge the testenvs
    for def_envname, def_envconf in default_config.envconfigs.items():
        if def_envname not in config.envconfigs:
            config.envconfigs[def_envname] = def_envconf
        else:
            merge_envconf(config.envconfigs[def_envname], def_envconf)

    # merge the actual parsed ini file sections
    merge_ini(config, default_config)


# Run this hook *before* any other tox_configure hook,
# especially the tox-travis one, because this plugin sets up the
# environments that tox-travis may use
@hookimpl(tryfirst=True)
def tox_configure(config: Config) -> None:
    """Adjust tox configuration right after it is loaded."""

    tox_lsr_scriptdir = os.environ.get("TOX_LSR_SCRIPTDIR")
    if not tox_lsr_scriptdir:
        tox_lsr_script_filename = pkg_resources.resource_filename(
            __name__, f"{TEST_SCRIPTS_SUBDIR}/runflake8.sh"
        )
        tox_lsr_scriptdir = os.path.dirname(tox_lsr_script_filename)
    tox_lsr_default = pkg_resources.resource_string(
        __name__, "data/tox-default.ini"
    ).decode()
    tox_lsr_default = tox_lsr_default.replace(
        "{tox_lsr_scriptdir}", tox_lsr_scriptdir
    )
    tox_parser = config._parser
    config.option.workdir = config.toxworkdir
    default_config = Config(
        config.pluginmanager,
        config.option,
        config.interpreters,
        tox_parser,
        [],
    )
    ToxParseIni(default_config, config.toxinipath, tox_lsr_default)
    merge_config(config, default_config)
