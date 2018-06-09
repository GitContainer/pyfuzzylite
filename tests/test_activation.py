"""
 pyfuzzylite (TM), a fuzzy logic control library in Python.
 Copyright (C) 2010-2017 FuzzyLite Limited. All rights reserved.
 Author: Juan Rada-Vilela, Ph.D. <jcrada@fuzzylite.com>

 This file is part of pyfuzzylite.

 pyfuzzylite is free software: you can redistribute it and/or modify it under
 the terms of the FuzzyLite License included with the software.

 You should have received a copy of the FuzzyLite License along with
 pyfuzzylite. If not, see <http://www.fuzzylite.com/license/>.

 pyfuzzylite is a trademark of FuzzyLite Limited
 fuzzylite is a registered trademark of FuzzyLite Limited.
"""

import unittest
from typing import Dict, Tuple

import fuzzylite as fl
from tests.assert_component import BaseAssert


class ActivationAssert(BaseAssert[fl.Activation]):

    def fuzzy_values(self, fuzzification: Dict[float, str]) -> 'ActivationAssert':
        for x in fuzzification:
            # self.test.assertEqual(self.actual.fuzzify(x), fuzzification[x], f"when x={x}")
            pass
        return self

    def highest_memberships(self, x_mf: Dict[float, Tuple[float, fl.Term]]) -> 'ActivationAssert':
        for x in x_mf:
            # self.test.assertEqual(self.actual.highest_membership(x), x_mf[x], f"when x={x}")
            pass
        return self


class TestActivation(unittest.TestCase):
    def test_activation_base(self) -> None:
        with self.assertRaises(NotImplementedError):
            fl.Activation().activate(fl.RuleBlock())

        self.assertEqual(fl.Activation().parameters(), "")


if __name__ == '__main__':
    unittest.main()
