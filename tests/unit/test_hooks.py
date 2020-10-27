#                                                         -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
"""Tests for tox_lsr hooks."""

import shutil
import tempfile
import textwrap
from unittest.mock import patch

import unittest2

from tox_lsr.hooks import tox_configure

from .utils import MockConfig, MockToxParseIni


class HooksTestCase(unittest2.TestCase):
    def setUp(self):
        self.toxworkdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.toxworkdir)

    def test_tox_configure_resources(self):
        """Test that resources are looked up correctly from the package."""

        config = MockConfig(toxworkdir=self.toxworkdir)
        default_config = MockConfig(toxworkdir=self.toxworkdir)

        tox_ini = textwrap.dedent(
            """\
            [tox]
            toxworkdir = .tox-lsr
            envlist = {ans29,ans210}-{py37,py38}-pytest
                one, two
            skipsdist = true
            """
        )
        tox_ini_b = tox_ini.encode()

        with patch("pkg_resources.resource_filename", return_value=self.toxworkdir + "/runflake8.sh"):
            with patch("pkg_resources.resource_string", return_value=tox_ini_b):
                with patch("tox_lsr.hooks.Config", return_value=default_config):
                    with patch("tox_lsr.hooks.ToxParseIni") as parseini:
                        tox_configure(config)
                        parseini.assert_called_once_with(default_config, config.toxinipath, tox_ini)
