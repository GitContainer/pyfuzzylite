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

import copy
import math
import operator
import typing

from .activation import Activation, First, General, Highest, Last, Lowest, Proportional, Threshold
from .defuzzifier import (Defuzzifier, Bisector, Centroid, LargestOfMaximum, MeanOfMaximum,
                          SmallestOfMaximum, WeightedAverage, WeightedSum)
from .hedge import Hedge, Any, Extremely, Not, Seldom, Somewhat, Very
from .norm import (TNorm, AlgebraicProduct, BoundedDifference, DrasticProduct, EinsteinProduct,
                   HamacherProduct, Minimum, NilpotentMinimum,
                   SNorm, AlgebraicSum, BoundedSum, DrasticSum, EinsteinSum, HamacherSum,
                   Maximum, NilpotentMaximum, NormalizedSum, UnboundedSum)
from .operation import Op
from .rule import Rule
from .term import (Term, Bell, Binary, Concave, Constant, Cosine, Discrete,
                   Function, Gaussian, GaussianProduct, Linear, PiShape, Ramp,
                   Rectangle, Sigmoid, SigmoidDifference, SigmoidProduct,
                   Spike, SShape, Trapezoid, Triangle, ZShape)

# TODO: Not too keen on having classes extending Generic[T]
T = typing.TypeVar('T')


class ConstructionFactory(typing.Generic[T]):
    __slots__ = ("constructors",)

    def __init__(self) -> None:
        self.constructors: typing.Dict[str, typing.Callable[[], typing.Optional[T]]] = {}

    @property
    def class_name(self) -> str:
        return self.__class__.__name__

    def construct(self, key: str) -> typing.Optional[T]:
        if key in self.constructors:
            if self.constructors[key]:
                return self.constructors[key]()
        raise ValueError(f"constructor of '{key}' not found in {self.class_name}")


class CloningFactory(typing.Generic[T]):
    __slots__ = ("objects",)

    def __init__(self) -> None:
        self.objects: typing.Dict[str, T] = {}

    @property
    def class_name(self) -> str:
        return self.__class__.__name__

    def copy(self, key: str) -> T:
        if key in self.objects:
            return copy.deepcopy(self.objects[key])
        raise ValueError(f"object with key '{key}' not found in {self.class_name}")


class ActivationFactory(ConstructionFactory[Activation]):
    def __init__(self) -> None:
        super().__init__()
        self.constructors[""] = type(None)

        for activation in [First, General, Highest, Last, Lowest, Proportional, Threshold]:
            self.constructors[activation().class_name] = activation


class DefuzzifierFactory(ConstructionFactory[Defuzzifier]):
    def __init__(self) -> None:
        super().__init__()
        self.constructors[""] = type(None)

        for defuzzifier in [Bisector, Centroid, LargestOfMaximum, MeanOfMaximum, SmallestOfMaximum,
                            WeightedAverage, WeightedSum]:
            self.constructors[defuzzifier().class_name] = defuzzifier

            # # TODO: Implement?
            # def construct(self, key: str, parameter: Union[int, str]):
            #     raise NotImplementedError()


class FunctionFactory(CloningFactory[Function.Element]):
    def __init__(self) -> None:
        super().__init__()
        self._register_operators()
        self._register_functions()

    def _register_operators(self) -> None:
        operator_type = Function.Element.Type.Operator
        operators = [
            # p = 100  #  priority
            # First order: not, negate
            Function.Element("!", "Logical NOT", operator_type, operator.not_,
                             arity=1, precedence=100, associativity=1),

            Function.Element("~", "Negate", operator_type, operator.neg,
                             arity=1, precedence=100, associativity=1),

            # Second order: power
            # p -= 10
            Function.Element("^", "Power", operator_type, operator.pow,
                             arity=2, precedence=90, associativity=1),

            # Third order: Multiplication, Division, and Modulo
            # p -= 10
            Function.Element("*", "Multiplication",
                             operator_type, operator.mul, arity=2, precedence=80),
            Function.Element("/", "Division",
                             operator_type, operator.truediv, arity=2, precedence=80),
            Function.Element("%", "Modulo",
                             operator_type, operator.mod, arity=2, precedence=80),

            # Fourth order: Addition, Subtraction
            # p -= 10
            Function.Element("+", "Addition",
                             operator_type, operator.add, arity=2, precedence=70),
            Function.Element("-", "Subtraction",
                             operator_type, operator.sub, arity=2, precedence=70),

            # Fifth order: logical and
            # p -= 10
            Function.Element(Rule.AND, "Logical AND", operator_type,
                             Op.logical_and, arity=2, precedence=60),
            # Sixth order: logical or
            # p -= 10
            Function.Element(Rule.OR, "Logical OR", operator_type,
                             Op.logical_or, arity=2, precedence=50)
        ]
        for op in operators:
            self.objects[op.name] = op

    def _register_functions(self) -> None:
        function_type = Function.Element.Type.Function

        functions = [
            Function.Element("gt", "Greater than (>)", function_type, Op.gt, arity=2),
            Function.Element("ge", "Greater than or equal to (>=)", function_type, Op.ge, arity=2),
            Function.Element("eq", "Equal to (==)", function_type, Op.eq, arity=2),
            Function.Element("neq", "Not equal to (!=)", function_type, Op.neq, arity=2),
            Function.Element("le", "Less than or equal to (<=)", function_type, Op.le, arity=2),
            Function.Element("lt", "Less than (>)", function_type, Op.lt, arity=2),

            Function.Element("min", "Minimum", function_type, min, arity=2),
            Function.Element("max", "Maximum", function_type, max, arity=2),

            Function.Element("acos", "Inverse cosine", function_type, math.acos, arity=1),
            Function.Element("asin", "Inverse sine", function_type, math.asin, arity=1),
            Function.Element("atan", "Inverse tangent", function_type, math.atan, arity=1),
            Function.Element("ceil", "Ceiling", function_type, math.ceil, arity=1),
            Function.Element("cos", "Cosine", function_type, math.cos, arity=1),
            Function.Element("cosh", "Hyperbolic cosine", function_type, math.cosh, arity=1),
            Function.Element("exp", "Exponential", function_type, math.exp, arity=1),
            Function.Element("abs", "Absolute", function_type, math.fabs, arity=1),
            Function.Element("fabs", "Absolute", function_type, math.fabs, arity=1),
            Function.Element("floor", "Floor", function_type, math.floor, arity=1),
            Function.Element("log", "Natural logarithm", function_type, math.log, arity=1),
            Function.Element("log10", "Common logarithm", function_type, math.log10, arity=1),
            Function.Element("round", "Round", function_type, round, arity=1),
            Function.Element("sin", "Sine", function_type, math.sin, arity=1),
            Function.Element("sinh", "Hyperbolic sine", function_type, math.sinh, arity=1),
            Function.Element("sqrt", "Square root", function_type, math.sqrt, arity=1),
            Function.Element("tan", "Tangent", function_type, math.tan, arity=1),
            Function.Element("tanh", "Hyperbolic tangent", function_type, math.tanh, arity=1),
            Function.Element("log1p", "Natural logarithm plus one", function_type, math.log1p, 1),
            Function.Element("acosh", "Inverse hyperbolic cosine", function_type, math.acosh, 1),
            Function.Element("asinh", "Inverse hyperbolic sine", function_type, math.asinh, 1),
            Function.Element("atanh", "Inverse hyperbolic tangent", function_type, math.atanh, 1),
            Function.Element("pow", "Power", function_type, math.pow, arity=2),
            Function.Element("atan2", "Inverse tangent (y,x)", function_type, math.atan2, arity=2),
            Function.Element("fmod", "Floating-point remainder", function_type, math.fmod, arity=2),
        ]

        for f in functions:
            self.objects[f.name] = f

    def operators(self) -> typing.Set[str]:
        result = set(key for key, prototype in self.objects.items() if
                     prototype.element_type == Function.Element.Type.Operator)
        return result

    def functions(self) -> typing.Set[str]:
        result = set(key for key, prototype in self.objects.items() if
                     prototype.element_type == Function.Element.Type.Function)
        return result


class HedgeFactory(ConstructionFactory[Hedge]):
    def __init__(self) -> None:
        super().__init__()
        self.constructors[""] = type(None)

        hedges = [Any, Extremely, Not, Seldom, Somewhat, Very]
        for hedge in hedges:
            self.constructors[hedge().name] = hedge


class SNormFactory(ConstructionFactory[SNorm]):
    def __init__(self) -> None:
        super().__init__()
        self.constructors[""] = type(None)

        snorms = [AlgebraicSum, BoundedSum, DrasticSum, EinsteinSum, HamacherSum,
                  Maximum, NilpotentMaximum, NormalizedSum, UnboundedSum]
        for snorm in snorms:
            self.constructors[snorm().class_name] = snorm


class TNormFactory(ConstructionFactory[TNorm]):
    def __init__(self) -> None:
        super().__init__()
        self.constructors[""] = type(None)

        tnorms = [AlgebraicProduct, BoundedDifference, DrasticProduct, EinsteinProduct,
                  HamacherProduct, Minimum, NilpotentMinimum]
        for tnorm in tnorms:
            self.constructors[tnorm().class_name] = tnorm


class TermFactory(ConstructionFactory[Term]):
    def __init__(self) -> None:
        super().__init__()
        self.constructors[""] = type(None)

        terms = [Bell, Binary, Concave, Constant, Cosine, Discrete,
                 Function, Gaussian, GaussianProduct, Linear, PiShape, Ramp,
                 Rectangle, Sigmoid, SigmoidDifference, SigmoidProduct,
                 Spike, SShape, Trapezoid, Triangle, ZShape]
        for term in terms:
            self.constructors[term().class_name] = term


class FactoryManager(object):
    __slots__ = ("tnorm_factory", "snorm_factory", "activation_factory", "defuzzifier_factory",
                 "term_factory", "hedge_factory", "function_factory")

    def __init__(self,
                 tnorm_factory: TNormFactory = TNormFactory(),
                 snorm_factory: SNormFactory = SNormFactory(),
                 activation_factory: ActivationFactory = ActivationFactory(),
                 defuzzifier_factory: DefuzzifierFactory = DefuzzifierFactory(),
                 term_factory: TermFactory = TermFactory(),
                 hedge_factory: HedgeFactory = HedgeFactory(),
                 function_factory: FunctionFactory = FunctionFactory()) -> None:
        self.tnorm_factory = tnorm_factory
        self.snorm_factory = snorm_factory
        self.activation_factory = activation_factory
        self.defuzzifier_factory = defuzzifier_factory
        self.term_factory = term_factory
        self.hedge_factory = hedge_factory
        self.function_factory = function_factory
