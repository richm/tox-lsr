#                                                         -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
"""Tests for tox_lsr hooks."""

import shutil
import tempfile
from unittest.mock import patch

import unittest2

from tox_lsr.hooks import tox_configure

from .utils import MockConfig, MockToxParseIni


class HooksTestCase(unittest2.TestCase):
    def setUp(self):
        self.toxworkdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.toxworkdir)

    @patch("tox_lsr.hooks.ToxParseIni", new=MockToxParseIni)
    @patch("tox.config.ParseIni", new=MockToxParseIni)
    @patch("tox_lsr.hooks.Config", new=MockConfig)
    @patch("tox.config.Config", new=MockConfig)
    def test_tox_configure_basic(self):
        config = MockConfig(toxworkdir=self.toxworkdir)

        tox_configure(config)
