#                                                         -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
"""Test utilities."""
import py
from collections import OrderedDict
from unittest.mock import MagicMock


# mocks the tox.config.Config class
class MockConfig(object):

    __slots__ = (
        "_parser", "pluginmanager", "option", "interpreters", "toxworkdir",
        "args", "toxinipath", "toxinidir", "_cfg", "envlist_explicit",
        "envconfigs"
    )

    def __init__(self, *args, **kwargs):
        """Mocks tox.config.Config constructor."""

        if len(args) > 0:
            self.option = args[0]
        else:
            self.option = MagicMock()
        if len(args) > 1:
            self.pluginmanager = args[1]
        else:
            self.pluginmanager = MagicMock()
        if len(args) > 2:
            self.interpreters = args[2]
        else:
            self.interpreters = MagicMock()
        if len(args) > 3:
            self._parser = args[3]
        else:
            self._parser = MagicMock()
        if len(args) > 4:
            self.args = args[4]
        else:
            self.args = MagicMock()
        self.toxworkdir = "/tmp"
        self.toxinipath = py.path.local("/tmp")
        self._cfg = MagicMock()
        self._cfg.sections = OrderedDict()
        self._cfg.sections["tox"] = OrderedDict()
        self.envlist_explicit = MagicMock()
        self.envconfigs = OrderedDict()


class MockToxParseIni(object):

    def __init__(self, config, ini_path, ini_data):
        """Mocks tox.config.ParseIni constructor."""
        pass
