#                                                         -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
"""Tests for tox_lsr hooks."""

import json
import os
import pkg_resources
import sys
import shutil
import tempfile
import textwrap
import py.iniconfig
from copy import deepcopy
from collections import OrderedDict
from unittest.mock import patch, Mock, PropertyMock, MagicMock

import unittest2

from tox_lsr.hooks import tox_configure, merge_ini, prop_is_set, merge_prop_values, merge_envconf

from .utils import MockConfig, MockToxParseIni


class HooksTestCase(unittest2.TestCase):

    def setUp(self):
        self.toxworkdir = tempfile.mkdtemp()
        patch("pkg_resources.resource_filename", return_value=self.toxworkdir + "/runflake8.sh").start()
        self.default_tox_ini_b = pkg_resources.resource_string("tox_lsr", "data/tox-default.ini")
        self.default_tox_ini_raw = self.default_tox_ini_b.decode()
        self.default_tox_ini = self.default_tox_ini_raw.replace(
            "{tox_lsr_scriptdir}", self.toxworkdir
        )
        # e.g. __file__ is tests/unit/something.py - fixture_path is tests/fixtures
        self.tests_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.fixture_path = os.path.join(self.tests_path, "fixtures", self.id().split(".")[-1])

    def tearDown(self):
        shutil.rmtree(self.toxworkdir)
        patch.stopall()

    def test_tox_configure_resources(self):
        """Test that resources are looked up correctly from the package."""

        config = MockConfig(toxworkdir=self.toxworkdir)
        default_config = MockConfig(toxworkdir=self.toxworkdir)

        with patch("pkg_resources.resource_string", return_value=self.default_tox_ini_b):
            with patch("tox_lsr.hooks.Config", return_value=default_config):
                with patch("tox_lsr.hooks.ToxParseIni") as parseini:
                    tox_configure(config)
                    parseini.assert_called_once_with(default_config, config.toxinipath, self.default_tox_ini)

    def test_tox_merge_ini(self):
        """Test that given config is merged with default config ini."""

        tox_ini_file = os.path.join(self.fixture_path, "tox.ini")
        tox_ini = ""
        with open(tox_ini_file) as tif:
            tox_ini = tif.read()
        result_file = os.path.join(self.fixture_path, "result.json")
        result = {}
        with open(result_file) as rf:
            result = json.load(rf)
        config = MockConfig(toxworkdir=self.toxworkdir)
        config._cfg = py.iniconfig.IniConfig(self.toxworkdir, tox_ini)
        default_config = MockConfig(toxworkdir=self.toxworkdir)
        default_config._cfg = py.iniconfig.IniConfig(self.toxworkdir, self.default_tox_ini_raw)
        merge_ini(config, default_config)
        self.assertEquals(result, config._cfg.sections)

    def test_tox_prop_is_set(self):
        """Test prop_is_set."""

        tec = Mock(envname="prop")
        tec._reader = Mock()
        tec._reader._cfg = Mock()
        cfgdict = {
            "empty_str_prop": "",
            "str_prop": "str_prop",
            "int_prop": 0,
            "bool_prop": False,
            "float_prop": 0.0,
            "list_prop": [1, 2, 3],
            "empty_list_prop": [],
            "dict_prop": {"a": "a"},
            "empty_dict_prop": {},
            "obj_prop": object(),
            "none_prop": None
        }
        cfgdict_result = {
            "empty_str_prop": False,
            "str_prop": True,
            "int_prop": False,
            "bool_prop": False,
            "float_prop": False,
            "list_prop": True,
            "empty_list_prop": False,
            "dict_prop": True,
            "empty_dict_prop": False,
            "obj_prop": True,
            "none_prop": False
        }
        tec._reader._cfg.sections = OrderedDict(deepcopy({
            "testenv": deepcopy(cfgdict)
        }))
        for prop in cfgdict.keys():
            self.assertTrue(prop_is_set(tec, prop))
        tec._reader._cfg.sections["testenv:prop"] = deepcopy(cfgdict)
        for prop in cfgdict.keys():
            self.assertTrue(prop_is_set(tec, prop))
        del tec._reader._cfg.sections["testenv"]
        del tec._reader._cfg.sections["testenv:prop"]
        tec.configure_mock(**deepcopy(cfgdict))
        for prop in cfgdict.keys():
            self.assertEqual(prop_is_set(tec, prop), cfgdict_result[prop])

    def test_tox_merge_prop_values(self):
        """Test merge_prop_values."""

        tec = MagicMock()
        def_tec = MagicMock()
        merge_prop_values("nosuchprop", tec, def_tec)
        self.assertFalse(tec.mock_calls)
        self.assertFalse(def_tec.mock_calls)
        # test empty tec
        tec = MagicMock()
        def_tec = MagicMock()
        propnames = ["setenv", "deps", "passenv", "whitelist_externals"]
        empty_attrs = {
            "setenv": {},
            "deps": [],
            "passenv": set(),
            "whitelist_externals": []
        }
        tec.configure_mock(**deepcopy(empty_attrs))
        full_attrs = {
            "setenv": {"a": "a", "b": "b"},
            "deps": ["a", "b"],
            "passenv": set(["a", "b"]),
            "whitelist_externals": ["a", "b"]
        }
        def_tec.configure_mock(**deepcopy(full_attrs))
        for prop in propnames:
            merge_prop_values(prop, tec, def_tec)
        for prop in propnames:
            val = getattr(tec, prop)
            exp_val = full_attrs[prop]
            if isinstance(val, list):
                self.assertEqual(set(exp_val), set(val))
            else:
                self.assertEqual(exp_val, val)
        # test empty def_tec
        tec = MagicMock()
        def_tec = MagicMock()
        tec.configure_mock(**deepcopy(full_attrs))
        def_tec.configure_mock(**deepcopy(empty_attrs))
        for prop in propnames:
            merge_prop_values(prop, tec, def_tec)
        for prop in propnames:
            val = getattr(tec, prop)
            exp_val = full_attrs[prop]
            if isinstance(val, list):
                self.assertEqual(set(exp_val), set(val))
            else:
                self.assertEqual(exp_val, val)
        # test merging
        more_attrs = {
            "setenv": {"a": "a", "c": "c"},
            "deps": ["a", "c"],
            "passenv": set(["a", "c"]),
            "whitelist_externals": ["a", "c"]
        }
        result_attrs = {
            "setenv": {"a": "a", "b": "b", "c": "c"},
            "deps": ["a", "b", "c"],
            "passenv": set(["a", "b", "c"]),
            "whitelist_externals": ["a", "b", "c"]
        }
        tec = MagicMock()
        def_tec = MagicMock()
        tec.configure_mock(**deepcopy(full_attrs))
        def_tec.configure_mock(**deepcopy(more_attrs))
        for prop in propnames:
            merge_prop_values(prop, tec, def_tec)
        for prop in propnames:
            val = getattr(tec, prop)
            exp_val = result_attrs[prop]
            if isinstance(val, list):
                self.assertEqual(set(exp_val), set(val))
            else:
                self.assertEqual(exp_val, val)

    def test_tox_merge_envconf(self):
        """Test the merge_envconf method."""

        # test setting an unset property
        prop = "propa"
        def mock_prop_is_set(envconf, propname):
            if propname != prop:
                return False
            if envconf == def_tec:
                return True
            return False
        def_tec = Mock(spec=[prop], propa=prop)
        tec = Mock(spec=[prop])
        with patch("tox_lsr.hooks.prop_is_set", side_effect=mock_prop_is_set):
            merge_envconf(tec, def_tec)
        self.assertEqual(prop, tec.propa)
        # test that it tries to merge if both props are set
        def mock_prop_is_set(envconf, propname):
            if propname != prop:
                return False
            return True
        def_tec = Mock(spec=[prop], propa=prop)
        tec = Mock(spec=[prop], propa="someothervalue")
        with patch("tox_lsr.hooks.prop_is_set", side_effect=mock_prop_is_set):
            with patch("tox_lsr.hooks.merge_prop_values") as mock_mpv:
                merge_envconf(tec, def_tec)
                mock_mpv.assert_called_once()
        self.assertEqual("someothervalue", tec.propa)
