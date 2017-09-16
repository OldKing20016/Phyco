################################################################################
# This file is part of ATOM
# Copyright (c) 2017 by Yifei Zheng
# Unauthorized copy, distribution and modification of this file is prohibited.
#
# This file contains structures to store data from source code, and useful
# processing routines for code generation.
#
# WARNING ## DATA CORRUPTION MAY OCCUR ## CAUTION
# DO NOT RUN COMPILER IN PARALLEL IN CURRENT RELEASE
# THE FILE CONTAINS BAD USAGE PATTERN OF GLOBAL VARIABLE USED FOR TESTING.
################################################################################
from collections import OrderedDict as odict
from . import warning
from . import templating
from . import resolver
from .support import cSrcLocation as src_tracker, cTypes, cVariable as Var
from itertools import chain
from contextlib import contextmanager
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from parser import expr


class Flag:
    def __init__(self, val):
        self.flag = val

    def __bool__(self):
        return self.flag


class RuleType:
    def __init__(self, src, dom, rule):
        self.src = src
        self.domain = dom
        self.rule = Expr(expr.stringToExpr(rule[0])), Expr(
            expr.stringToExpr(rule[1]))
        self.diffs = set(
            chain(self.rule[0].findDerivatives(),
                  self.rule[1].findDerivatives()))

    def list_vars(self):
        return chain(self.rules[0].listVars(), self.rules[1].listVars())

    def __repr__(self):
        return f'Rule at {self.src}: {self.rule}'


class ObjType:
    def __init__(self, src, obj, vals):
        self.src = src
        self.name = obj
        self.vals = vals

    def getWatch(self, watch):
        return writers.WatchWriter(watch)

    def writer(self):
        return self

    def write(self):
        return f'object {self.name} {self.vals};'

    def __repr__(self):
        return f'Object at {self.src}: {self.vals}'


class DeclType:
    def __init__(self, src, types):
        self.src = src
        self.types = types


class Op:
    def __init__(self, name, argc=1, writer=None):
        self.name = name
        self.argc = argc
        self.writer = writer

    def __repr__(self):
        return 'Op:' + self.name


def diff_writer(args, default_writer: 'StepWriter'):
    expr, *wrt = args
    if wrt:
        raise NotImplementedError
    all_vars = set(resolver.cNVar(i.name, i.order[0]+1) for i in expr.findDerivatives())
    solving = {var for var in default_writer.state[-1] if var in all_vars}
    if not solving:
        return f'math::calculus::fdiff({default_writer.write_lambda("&", "double t", "return " + default_writer.write_expr(expr) + ";")}, t)'
    else:
        override_dict = {}
        var = solving.pop()
        write = default_writer.write_arg(var)
        override_dict[var] = write
        # When using chain-rule we have to adjust writing scheme for base
        # variables as well
        var_base = resolver.cNVar(var.name, var.order[0] - 1)
        write_base = default_writer.write_arg(var_base)
        if var.order[0] > 1:
            override_dict[var_base] = write_base
        else:
            override_dict[var.name] = write_base
        original_write = default_writer.VarWriter.write(var_base)
        with default_writer.VarWriter.tmp_override(override_dict):
            text = f'math::calculus::fdiff({default_writer.write_lambda("&", f"double {write_base}", "return " + default_writer.write_expr(expr) + ";")}, {original_write})'
        return text + f' * {write}'

OP = {
    '+': Op('math::op::add', 2),
    '-': Op('math::op::sub', 2),
    '*': Op('math::op::mul', 2),
    '/': Op('math::op::div', 2),
    'pow': Op('std::pow', 2),
    'sin': Op('std::sin', 1),
    'cos': Op('std::cos', 1),
    'tan': Op('std::tan', 1),
    'sqrt': Op('math::sqrt', 1),
    'diff': Op('diff', 1, diff_writer),
}


class Expr:
    def __init__(self, expr):
        if isinstance(expr, tuple):
            self.content = (expr[0], [Expr(i) for i in expr[1]])
        else:
            self.content = expr

    def listVars(self):
        if isinstance(self.content, tuple):
            for i in self.content[1]:
                yield from i.listVars()
        elif isinstance(self.content, str):
            yield self.content

    def findDerivatives(self, DIFF=0):
        if isinstance(self.content, tuple):
            if self.content[0] == 'diff':
                DIFF += 1
            for i in self.content[1]:
                yield from i.findDerivatives(DIFF)
            if self.content[0] == 'diff':
                DIFF -= 1
        elif isinstance(self.content, str):
            yield resolver.cNVar(self.content, DIFF)

    def __repr__(self):
        return repr(self.content)


def resolve(offset, rules, unknowns):
    for i in rules:
        i.diffs.intersection_update(unknowns)
    steps = resolver.resolve(rules, unknowns)
    return [(offset + i, j) for i, j in steps]


class StepWriter:
    def __init__(self, space: 'Space'):
        self.space = space
        self.state = []
        self.VarWriter = StepWriter.VarWriter(self.space.locate_var)
        self.noBind = Flag(False)

    @staticmethod
    @contextmanager
    def tmp_flag(flag, a):
        old = flag.flag
        flag.flag = a
        yield
        flag.flag = old

    def write(self, step):
        use, update = step
        if self.noBind:
            bind = ''
            end = ''
        else:
            bind = f'{self.VarWriter.write(update)} = '
            end = ';'
        if isinstance(use, int):
            return bind + self.write_alg(
                self.write_lambda('&',
                                  f'double {self.write_arg(update)}',
                                  f'return {self.write_rule(self.space.rules[use])};'),
                self.write_expr(update)) + end
        elif isinstance(use, tuple):
            update_intermediate = use[1]
            self.state.append([update_intermediate])
            with self.tmp_flag(self.noBind, True), self.tmp_flag(self.VarWriter.UnrecordedAsConst, True):
                return bind + self.write_diff(
                    self.write_lambda('&', 'double t, double x', f'return {self.write(use)};'),
                    't', self.write_expr(update),
                    'step') + '.first' + end

    @staticmethod
    def write_alg(rule, seed):
        return f'math::solver::algebraic({rule}, {seed})'

    @staticmethod
    def write_diff(gen, wrt, seed, step):
        return f'math::solver::differential({gen}, {wrt}, {seed}, {step})'

    def write_rule(self, rule: RuleType):
        return f'math::op::sub({self.write_expr(rule.rule[0])}, {self.write_expr(rule.rule[1])})'

    def write_expr(self, expr):
        if isinstance(expr, Expr):
            expr = expr.content
        if isinstance(expr, tuple):
            op = OP[expr[0]]
            if op.writer:
                return op.writer(expr[1], self)
            else:
                return f'{op.name}({", ".join(self.write_expr(i) for i in expr[1])})'
        elif isinstance(expr, str) or isinstance(expr, resolver.cNVar):
            return self.VarWriter.write(expr)
        else:
            return str(expr)

    class VarWriter:
        def __init__(self, parent):
            # controls writing of unrecorded variable
            # i.e. the variables computed on demand
            self.look_up = parent
            self.UnrecordedAsConst = Flag(False)
            self.override = {}

        @contextmanager
        def tmp_override(self, iter):
            old = self.override.copy()
            self.override.update(iter)
            yield
            self.override = old

        def write(self, var):
            if var in self.override:
                return self.override[var]
            elif isinstance(var, resolver.cNVar):
                if sum(var.order) != 0:
                    if not self.UnrecordedAsConst:
                        return f'{self.write(var.name)}_{var.order[0]}'
                    else:
                        return '0'
                else:
                    return self.write(var.name)
            else:
                lookup_result = self.look_up(var)
                if isinstance(lookup_result, tuple):
                    return self.write_watch(lookup_result[0], lookup_result[1])
                else:
                    return var

        @staticmethod
        def write_watch(num, var):
            return f'srd_.get({num}).{var}'

    @staticmethod
    def write_lambda(capture, sig, body):
        return f'[{capture}]({sig}){{{body}}}'

    def write_arg(self, var):
        if isinstance(var, resolver.cNVar):
            if sum(var.order) != 0:
                return f'{var.name.split(".", 1)[1]}_{var.order[0]}'
            else:
                var = var.name

        lookup_result = self.space.locate_var(var)
        if isinstance(lookup_result, tuple):
            return lookup_result[1]
        else:
            return var

    def __iter__(self):
        for step in self.space.steps:
            yield self.write(step)


class Space:

    def __init__(self):
        self.objs = odict()
        self.watches = odict()
        self.globals = {'t': Var(cTypes(cTypes.BaseEnum.DOUBLE, True, 0), 1),
                        'step': Var(cTypes(cTypes.BaseEnum.DOUBLE, False, 0), 0.001)}
        self.tmps = {}
        self.rules = []
        self.loopctl = set()
        self.steps = None

    def addRule(self, rule, dom=None, src=None):
        self.rules.append(
            RuleType(src if src else src_tracker(0, 0), dom, rule))

    def addObj(self, obj, vals, src=None):
        if obj in self.objs:
            if not warning.warn_ask(f'Object named {obj} exists, continue?'):
                return
        self.objs[obj] = ObjType(src if src else src_tracker(0, 0), obj, vals)

    def addTmp(self, var, types, src=None):
        self.tmps[var] = DeclType(src, types)

    def addLoopctl(self, var, src):
        pass

    def addWatch(self, var, types, src=None):
        if var in self.watches:
            if not warning.warn_ask(f'Watch {var} exists, continue?'):
                return
        self.watches[var] = cTypes(types, False, 0)

    def processRules(self):
        def available(NVar):
            v = self.locate_var(NVar.name)
            return NVar.order[0] == 0 and v is not None and not isinstance(v, tuple)
        # WE ASSUMED THAT UPDATING A VARIABLE TWICE IN A CYCLE IS ILLEGAL
        self.steps = []
        idx = 0
        while idx < len(self.rules):
            eqn_count = 0
            needMore = True
            all_vars = set()
            while needMore:
                eqn_count += 1
                all_vars.update(self.rules[idx + eqn_count - 1].diffs)
                unknowns = {var for var in all_vars if not available(var)}
                needMore = len(unknowns) > eqn_count
            self.steps += resolve(idx, self.rules[idx:idx + eqn_count], unknowns)
            idx += eqn_count

        # propagate updates here
        updated = {}
        for i, (_, var) in enumerate(self.steps):
            if var.order[0] < updated.get(var.name, 256): # FIXME: Magic value, shall be inf
                updated[var.name] = i, var.order
        for var, (i, _) in updated.items():
            self.steps[i] = self.steps[i], resolver.cNVar(var, 0)

    def write(self):
        gen = templating.template('codegen/template')
        consume = templating.consume
        yield from consume(gen, (f'{type} {name};' for name, type in self.watches.items()))
        yield from consume(gen, self.objs)
        yield from consume(gen, (f'obj.{var}' for var in self.watches))
        yield from consume(gen,
                           (', '.join(str(i) for i in obj.vals) for obj in self.objs.values()))
        yield from consume(gen, (f'{tv.type} {name} = {tv.val};' for name, tv in self.globals.items()))
        yield from consume(gen, [f'combinations<1> comb_(0, {len(self.objs)});'])  # FIXME: insert true value when tested
        writer = StepWriter(self)
        yield from consume(gen, writer)
        yield from gen

    def locate_var(self, var):
        if var.startswith('$'):
            obj, watch = var[1:].split('.', 1)
            base_watch = self.watches[watch]
            if obj.isdigit():
                return int(obj), watch, base_watch
            else:
                return self.objs[obj].get_watch(base_watch)
        elif var in self.tmps:
            return self.tmps[var]
        elif var in self.globals:
            return self.globals[var]
        else:
            return self.objs[var]