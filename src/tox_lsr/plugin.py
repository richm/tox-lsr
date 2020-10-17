import os

import pkg_resources
import pluggy
from tox.config import Config as ToxConfig
from tox.config import testenvprefix as toxtestenvprefix

# from tox.reporter import verbosity0

try:
    from tox.config import ParseIni as ToxParseIni  # tox 3.4.0+
except ImportError:
    from tox.config import parseini as ToxParseIni

hookimpl = pluggy.HookimplMarker("tox")


def is_string(val):
    """Return True if val is a string type"""

    isstring = False
    try:
        isstring = isinstance(val, basestring)
    except NameError:
        isstring = isinstance(val, str)
    return isstring


def prop_is_set(envconf, propname):
    """Return True if the property was explicitly set to a value"""

    section_name = toxtestenvprefix + envconf.envname
    cfg = envconf._reader._cfg.sections.get(section_name, {})
    tecfg = envconf._reader._cfg.sections.get("testenv", {})
    if propname in cfg or propname in tecfg:
        return True
    val = getattr(envconf, propname)
    # see if val is one of the scalar types
    if is_string(val):
        return len(val) > 0  # assume empty string is unset
    if isinstance(val, int):
        return False  # no way to tell
    if isinstance(val, float):
        return False  # no way to tell
    if isinstance(val, bool):
        return False  # no way to tell
    # not a simple scalar type - see if empty
    return bool(val)


def merge_prop_values(propname, envconf, def_envconf):
    """if propname is one of the values we can merge,
    do the merge"""
    if propname == "setenv":  # merge env vars
        for envvar in def_envconf.setenv.keys():
            if envvar not in envconf.setenv:
                envconf.setenv[envvar] = def_envconf.setenv[envvar]
    elif propname == "deps":
        envconf.deps = list(set(envconf.deps + def_envconf.deps))
    elif propname == "passenv":
        envconf.passenv = envconf.passenv.union(def_envconf.passenv)
    elif propname == "whitelist_externals":
        envconf.deps = list(set(envconf.whitelist_externals + def_envconf.whitelist_externals))


def merge_envconf(envconf, def_envconf):
    """Merge the default envconfig from def_envconf into the given
    envconf"""
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


def merge_ini(config, default_config):
    """merge the parsed ini config values/sections"""

    for def_section_name, def_section in default_config._cfg.sections.items():
        section = config._cfg.sections.setdefault(def_section_name, def_section)
        if section is not def_section:
            for key, value in def_section.items():
                if key not in section:
                    section[key] = value


def merge_config(config, default_config):
    """Use the default_config, and override/replace the defaults
    with the given config"""

    # merge the top level config properties
    for propname in dir(default_config):
        # set in config if not set and it's set in default
        if (
            propname in default_config._cfg.sections["tox"]
            and propname not in config._cfg.sections["tox"]
        ):
           setattr(config, propname, getattr(default_config, propname))

    # merge the testenvs
    for def_envname, def_envconf in default_config.envconfigs.items():
        if def_envname not in config.envconfigs:
            config.envconfigs[def_envname] = def_envconf
        else:
            merge_envconf(config.envconfigs[def_envname], def_envconf)

    # merge the actual parsed ini file sections
    merge_ini(config, default_config)

@hookimpl
def tox_addoption(parser):
    """Add a command line option for later use"""
    # parser.add_argument("--magic", action="store", help="this is a magical option")
    # parser.add_testenv_attribute(
    #     name="cinderella",
    #     type="string",
    #     default="not here",
    #     help="an argument pulled from the tox.ini",
    # )
    pass


# Use tryfirst=True so that this is applied before the tox-travis plugin
@hookimpl(tryfirst=True)
def tox_configure(config):
    """Access your option during configuration"""

    tox_lsr_scriptdir = os.environ.get("TOX_LSR_SCRIPTDIR")
    if not tox_lsr_scriptdir:
        tox_lsr_script_filename = pkg_resources.resource_filename(
            __name__, "data/.travis/runflake8.sh"
        )
        tox_lsr_scriptdir = os.path.dirname(tox_lsr_script_filename)
    tox_lsr_default = pkg_resources.resource_string(__name__, "data/tox-default.ini").decode()
    tox_lsr_default = tox_lsr_default.replace("{tox_lsr_scriptdir}", tox_lsr_scriptdir)
    tox_parser = config._parser
    args = []
    config.option.workdir = config.toxworkdir
    default_config = ToxConfig(
        config.pluginmanager, config.option, config.interpreters, tox_parser, args
    )
    ToxParseIni(default_config, config.toxinipath, tox_lsr_default)
    merge_config(config, default_config)


@hookimpl
def tox_runtest_post(venv):
    # verbosity0("cinderella is {}".format(venv.envconfig.cinderella))
    pass
