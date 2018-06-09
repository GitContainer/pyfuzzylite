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
import typing
from math import nan

from .exporter import FllExporter
from .hedge import Any
from .norm import SNorm, TNorm
from .operation import Op
from .variable import InputVariable, OutputVariable

if typing.TYPE_CHECKING:
    from .activation import Activation
    from .engine import Engine
    from .hedge import Hedge
    from .term import Term
    from .variable import Variable


class Expression(object):
    pass


class Proposition(Expression):
    __slots__ = ("variable", "hedges", "term")

    def __init__(self) -> None:
        self.variable: typing.Optional[Variable] = None
        self.hedges: typing.List[Hedge] = []
        self.term: typing.Optional[Term] = None

    def __str__(self) -> str:
        result = []

        result.append(self.variable.name if self.variable else "?")

        result.append(Rule.IS)

        if self.hedges:
            for hedge in self.hedges:
                result.append(hedge.name)

        result.append(self.term.name if self.term else "?")

        return " ".join(result)


class Operator(Expression):
    __slots__ = ("name", "left", "right")

    def __init__(self) -> None:
        self.name: str = ""
        self.left: typing.Optional[Expression] = None
        self.right: typing.Optional[Expression] = None

    def __str__(self) -> str:
        return self.name


class Antecedent(object):
    __slots__ = ("text", "expression")

    def __init__(self) -> None:
        self.text: str = ""
        self.expression: typing.Optional[Expression] = None

    def is_loaded(self) -> bool:
        return bool(self.expression)

    def unload(self) -> None:
        self.expression = None

    def load(self, engine: 'Engine') -> None:
        # if fuzzylite.library().debugging:
        #     fuzzylite.library().logger.debug(f"Antecedent: {antecedent}")
        self.unload()
        if not self.text:
            raise ValueError("expected the antecedent of a rule, but found none")

    def activation_degree(self, conjunction: TNorm, disjunction: SNorm) -> float:
        if not self.is_loaded():
            raise ValueError(f"antecedent <{self.text}> is not loaded")

        return self._activation_degree(conjunction, disjunction, self.expression)

    def _activation_degree(self, conjunction: TNorm, disjunction: SNorm,
                           node: typing.Optional[Expression]) -> float:
        if not node:
            raise ValueError("expected an expression node, but found none")

        if isinstance(node, Proposition):
            if not node.variable:
                raise ValueError(f"expected a variable in proposition {node}, but found none")
            if not node.variable.enabled:
                return 0.0

            if node.hedges:
                # if last hedge is "Any", apply hedges in reverse order and return degree
                if isinstance(node.hedges[-1], Any):
                    result = nan
                    for hedge in reversed(node.hedges):
                        result = hedge.hedge(result)
                    return result

            if not node.term:
                raise ValueError(f"expected a term in proposition {node}, but found none")

            result = nan
            if isinstance(node.variable, InputVariable):
                result = node.term.membership(node.variable.value)
            elif isinstance(node.variable, OutputVariable):
                result = node.variable.fuzzy.activation_degree(node.term)

            if node.hedges:
                for hedge in reversed(node.hedges):
                    result = hedge.hedge(result)

            return result

        if isinstance(node, Operator):
            if not (node.left and node.right):
                raise ValueError("expected left and right operands")

            if node.name == Rule.AND:
                if not conjunction:
                    raise ValueError(f"rule requires a conjunction operator: '{self.text}'")
                return conjunction.compute(
                    self._activation_degree(conjunction, disjunction, node.left),
                    self._activation_degree(conjunction, disjunction, node.right))

            if node.name == Rule.OR:
                if not disjunction:
                    raise ValueError(f"rule requires a disjunction operator: '{self.text}'")
                return disjunction.compute(
                    self._activation_degree(conjunction, disjunction, node.left),
                    self._activation_degree(conjunction, disjunction, node.right))

            raise ValueError(f"operator <{node.name}> not recognized")

        raise ValueError(f"expected a Proposition or an Operator, but found <{str(node)}>")


class Consequent(object):
    __slots__ = ("text", "conclusions")

    def __init__(self) -> None:
        self.text: str = ""
        self.conclusions: typing.List[Proposition] = []

    def is_loaded(self) -> bool:
        return bool(self.conclusions)

    def unload(self) -> None:
        self.conclusions.clear()

    def load(self, engine: 'Engine') -> None:
        pass

    def modify(self, activation_degree: float, implication: typing.Optional[TNorm]) -> None:
        pass


class Rule(object):
    __slots__ = ("enabled", "weight", "activation_degree", "triggered", "antecedent", "consequent")

    IF = 'if'
    IS = 'is'
    THEN = 'then'
    AND = 'and'
    OR = 'or'
    WITH = 'with'

    def __init__(self) -> None:
        self.enabled: bool = True
        self.weight: float = 1.0
        self.activation_degree: float = 0.0
        self.triggered: bool = False
        self.antecedent: Antecedent = Antecedent()
        self.consequent: Consequent = Consequent()

    def __str__(self) -> str:
        return FllExporter().rule(self)

    @property
    def text(self) -> str:
        result = [Rule.IF]
        if self.antecedent:
            result.append(self.antecedent.text)
        result.append(Rule.THEN)
        if self.consequent:
            result.append(self.consequent.text)
        if self.weight != 1.0:
            result.append(Rule.WITH)
            result.append(Op.str(self.weight))
        return " ".join(result)

    @text.setter
    def text(self, text: str) -> None:
        comment_index = text.find("#")
        rule = text if comment_index == -1 else text[0:comment_index]

        antecedent = []
        consequent = []
        weight = 1.0
        s_none, s_if, s_then, s_with, s_end = range(5)
        state = s_none
        for token in rule.split():
            if state == s_none:
                if token == Rule.IF:
                    state = s_if
                else:
                    raise SyntaxError(
                        f"expected keyword '{Rule.IF}', but found '{token}' in rule: {text}")
            elif state == s_if:
                if token == Rule.THEN:
                    state = s_then
                else:
                    antecedent.append(token)
            elif state == s_then:
                if token == Rule.WITH:
                    state = s_with
                else:
                    consequent.append(token)
            elif state == s_with:
                weight = float(token)
                state = s_end
            elif state == s_end:
                raise SyntaxError(f"unexpected token '{token}' at the end of rule")
            else:
                raise SyntaxError(f"unexpected state '{state}' in finite state machine")

        if state == s_none:
            raise SyntaxError(f"expected an if-then rule, but found '{text}'")
        if state == s_if:
            raise SyntaxError(f"expected keyword '{Rule.THEN}' in rule '{text}'")
        if state == s_with:
            raise SyntaxError(f"expected the rule weight in rule '{text}'")

        if not antecedent:
            raise SyntaxError(f"expected an antecedent in rule '{text}'")
        if not consequent:
            raise SyntaxError(f"expected a consequent in rule '{text}'")

        self.antecedent.text = " ".join(antecedent)
        self.consequent.text = " ".join(consequent)
        self.weight = weight

    def deactivate(self) -> None:
        self.activation_degree = 0.0
        self.triggered = False

    def activate_with(self, conjunction: typing.Optional[TNorm],
                      disjunction: typing.Optional[SNorm]) -> float:
        pass

    def trigger(self, implication: typing.Optional[TNorm]) -> None:
        if not self.is_loaded():
            raise RuntimeError(
                f"expected to trigger rule, but the rule is not loaded: '{self.text}'")
        if self.enabled and Op.gt(self.activation_degree, 0.0):
            # if fuzzylite.library().debugging:
            #     fuzzylite.library().logger.debug(
            #         f"[triggering with {Op.str(self.activation_degree)}] {str(self)}")
            self.consequent.modify(self.activation_degree, implication)
            self.triggered = True

    def is_loaded(self) -> bool:
        return self.antecedent.is_loaded() and self.consequent.is_loaded()

    def unload(self) -> None:
        self.deactivate()
        self.antecedent.unload()
        self.consequent.unload()

    def load(self, engine: 'Engine') -> None:
        self.deactivate()
        self.antecedent.load(engine)
        self.consequent.load(engine)

    @staticmethod
    def parse(text: str, engine: typing.Optional['Engine'] = None) -> 'Rule':
        rule = Rule()
        rule.text = text
        if engine:
            rule.load(engine)
        return rule


class RuleBlock(object):
    __slots__ = ("name", "description", "enabled", "conjunction", "disjunction", "implication",
                 "activation", "rules")

    def __init__(self, name: str = "", description: str = "", enabled: bool = True,
                 conjunction: typing.Optional[TNorm] = None,
                 disjunction: typing.Optional[SNorm] = None,
                 implication: typing.Optional[TNorm] = None,
                 activation: typing.Optional['Activation'] = None,
                 rules: typing.Optional[typing.Iterable[Rule]] = None) -> None:
        self.name = name
        self.description = description
        self.enabled = enabled
        self.conjunction = conjunction
        self.disjunction = disjunction
        self.implication = implication
        self.activation = activation
        self.rules: typing.List[Rule] = []
        if rules:
            self.rules.extend(rules)

    def __str__(self) -> str:
        return FllExporter().rule_block(self)

    def unload_rules(self) -> None:
        pass

    def load_rules(self) -> None:
        pass

    def reload_rules(self) -> None:
        pass
