#                                                         -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
"""Type annotations for tox.config."""

from typing import List, Set

from py import iniconfig
from collections import OrderedDict

testenvprefix: str


class TestenvConfig:
    envname: str
    config: Config
    factors: Set[str]
    whitelist_externals: List[str]


class Config:  # noqa: H238
    _cfg: iniconfig.IniConfig
    envlist: List[str]
    envlist_default: List[str]
    envlist_explicit: bool
    envconfigs: OrderedDict[str, TestenvConfig]
    toxworkdir: str


class ParseIni:
    _cfg: iniconfig.IniConfig
    config: Config

class parseini: ParseIni
