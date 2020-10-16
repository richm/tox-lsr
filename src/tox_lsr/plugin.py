import pluggy
import pkg_resources
from tox.reporter import verbosity0
from tox.config import parse_cli as tox_parse_cli
from tox.config import propose_configs as tox_propose_configs
from tox.config import Config as ToxConfig
from tox.config import Parser as ToxParser
try:
    from tox.config import ParseIni as ToxParseIni # tox 3.4.0+
except ImportError:
    from tox.config import parseini as ToxParseIni

hookimpl = pluggy.HookimplMarker("tox")


def merge_config(config, default_config):
    """Use the default_config, and override/replace the defaults
       with the given config"""
    for def_envname, def_envconf in default_config.envconfigs.items():
        if not def_envname in config.envconfigs:
            config.envconfigs[def_envname] = def_envconf
        else:
            envconf = config.envconfigs[def_envname]
            for propname in dir(def_envconf):
                if propname.startswith("_"):
                    continue  # skip protected attrs
                if not hasattr(envconf, propname):
                    setattr(envconf, propname, getattr(def_envconf, propname))
    if not config.envlist_explicit:
        config.envlist = list(config.envconfigs.keys())
        config.envlist_default = config.envlist


@hookimpl
def tox_addoption(parser):
    """Add a command line option for later use"""
    parser.add_argument("--magic", action="store", help="this is a magical option")
    parser.add_testenv_attribute(
        name="cinderella",
        type="string",
        default="not here",
        help="an argument pulled from the tox.ini",
    )


@hookimpl
def tox_configure(config):
    """Access your option during configuration"""
    tox_default = pkg_resources.resource_filename(__name__, "data/tox-default.ini")
    #tox_parser = ToxParser()
    tox_parser = config._parser
    #args = ["--workdir", str(config.toxworkdir)]
    args = []
    config.option.workdir = config.toxworkdir
    default_config = ToxConfig(config.pluginmanager, config.option, config.interpreters, tox_parser, args)
    for conf_file in tox_propose_configs(tox_default):
        ToxParseIni(default_config, conf_file, None)
    #default_config, option = tox_parse_cli(["-c", tox_default], config.pluginmanager)
    merge_config(config, default_config)
    verbosity0("config is {} flag magic is: {} tox_default.ini {} default_config {}".format(config, config.option.magic, tox_default, default_config))


@hookimpl
def tox_runtest_post(venv):
    verbosity0("cinderella is {}".format(venv.envconfig.cinderella))
