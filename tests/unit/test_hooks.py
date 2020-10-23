#                                                         -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
"""Tests for tox_lsr hooks."""

import unittest2
from unittest.mock import patch

from tox_lsr.hooks import tox_configure

from .utils import MockConfig, MockToxParseIni


class HooksTestCase(unittest2.TestCase):
    def setUp(self):
        pass

    @patch('tox_lsr.hooks.ToxParseIni', new=MockToxParseIni)
    @patch('tox.config.ParseIni', new=MockToxParseIni)
    @patch('tox_lsr.hooks.Config', new=MockConfig)
    @patch('tox.config.Config', new=MockConfig)
    def test_tox_configure_basic(self):
        config = MockConfig()

        tox_configure(config)
