import parser
import utils
from typing import Dict
from collections import namedtuple

from utils import make_label

Variable = namedtuple('Variable', 'name from_current_block')


inc_dec_operators = {parser.UnaryOperator.PRE_INCREMENT,
                     parser.UnaryOperator.PRE_DECREMENT,
                     parser.UnaryOperator.POST_INCREMENT,
                     parser.UnaryOperator.POST_DECREMENT}


def run(ast_program: parser.Program):
    variable_map = {}
    variable_resolution(ast_program, variable_map)
    loop_labeling(ast_program)


def variable_resolution(ast_program: parser.Program, variable_map: Dict):
    for function in ast_program.functions:
        process_function(function, variable_map)


def process_function(function: parser.Function, variable_map: Dict):
    labels = {}
    function.block = resolve_block(function.block, variable_map, labels)
    for key in labels:
        if not labels[key]:
            raise SyntaxError(f'Use of undeclared label \'{key}\'')


def resolve_declaration(declaration: parser.VarDecl, variable_map: Dict):
    if declaration.name in variable_map and variable_map[declaration.name].from_current_block:
        raise SyntaxError(f'Variable {declaration.name} already defined in current scope')
    unique_name = utils.make_temporary()
    variable_map[declaration.name] = Variable(unique_name, True)
    init = None
    if declaration.init is not None:
        init = resolve_exp(declaration.init, variable_map)
    return parser.VarDecl(unique_name, init)


def resolve_statement(statement: parser.Statement, variable_map: Dict, labels: Dict):
    if isinstance(statement, parser.Return):
        return parser.Return(resolve_exp(statement.exp, variable_map))
    elif isinstance(statement, parser.If):
        return parser.If(resolve_exp(statement.condition, variable_map),
                         resolve_statement(statement.then, variable_map, labels),
                         resolve_statement(statement.else_, variable_map, labels))
    elif isinstance(statement, parser.Expression):
        return resolve_exp(statement, variable_map)
    elif isinstance(statement, parser.Goto):
        if statement.label not in labels:
            labels[statement.label] = False
        return statement
    elif isinstance(statement, parser.While):
        return parser.While(resolve_exp(statement.condition, variable_map),
                            resolve_statement(statement.body, variable_map, labels))
    elif isinstance(statement, parser.DoWhile):
        return parser.DoWhile(resolve_exp(statement.condition, variable_map),
                              resolve_statement(statement.body, variable_map, labels))
    elif isinstance(statement, parser.For):
        return resolve_for_statement(statement, variable_map, labels)
    elif isinstance(statement, parser.Label):
        if statement.label in labels and labels[statement.label] == True:
            raise SyntaxError(f'Redefinition of label \'{statement.label}\'')
        labels[statement.label] = True
        return parser.Label(statement.label, resolve_statement(statement.statement, variable_map, labels))
    elif isinstance(statement, parser.Compound):
        return resolve_compound(statement, variable_map, labels)
    elif isinstance(statement, parser.Switch):
        return parser.Switch(resolve_exp(statement.expr, variable_map),
                             resolve_statement(statement.body, variable_map, labels))
    elif isinstance(statement, parser.Default):
        return parser.Default(resolve_statement(statement.statement, variable_map, labels))
    elif isinstance(statement, parser.Case):
        return parser.Case(resolve_exp(statement.const, variable_map),
                           resolve_statement(statement.statement, variable_map, labels))
    else:
        return statement


def resolve_for_statement(statement: parser.For, variable_map: Dict, labels: Dict):
    new_variable_map = copy_variable_map(variable_map)
    for_init = resolve_for_init(statement.for_init, new_variable_map, labels)
    cond = None
    if statement.condition is not None:
        cond = resolve_exp(statement.condition, new_variable_map)
    post = None
    if statement.post is not None:
        post = resolve_exp(statement.post, new_variable_map)
    body = resolve_statement(statement.body, new_variable_map, labels)
    return parser.For(for_init, cond, post, body)


def resolve_for_init(for_init: parser.ForInit, variable_map: Dict, labels: Dict):
    if for_init is None:
        return None
    elif isinstance(for_init, parser.InitExpression):
        return parser.InitExpression(resolve_exp(for_init.expression, variable_map))
    elif isinstance(for_init, parser.InitDeclaration):
        return parser.InitDeclaration(resolve_declaration(for_init.declaration, variable_map))
    else:
        raise SyntaxError(f'Undeclared init expression \'{for_init}\'')


def resolve_compound(statement: parser.Compound, variable_map: Dict, labels: Dict):
    new_variable_map = copy_variable_map(variable_map)
    block = resolve_block(statement.block, new_variable_map, labels)
    return parser.Compound(block)


def copy_variable_map(variable_map: Dict):
    new_variable_map = {}
    for key in variable_map:
        new_variable_map[key] = Variable(variable_map[key].name, False)
    return new_variable_map


def resolve_block(statement: parser.Block, variable_map: Dict, labels: Dict):
    block_items = []
    for item in statement.block_items:
        if isinstance(item, parser.VarDecl):
            block_items.append(resolve_declaration(item, variable_map))
        elif isinstance(item, parser.Statement):
            block_items.append(resolve_statement(item, variable_map, labels))
    return parser.Block(block_items)


def resolve_exp(exp: parser.Expression, variable_map: Dict):
    if isinstance(exp, parser.Assignment):
        if not isinstance(exp.left, parser.Var):
            raise SyntaxError("Invalid lvalue!")
        return parser.Assignment(resolve_exp(exp.left, variable_map),
                                 resolve_exp(exp.right, variable_map))
    elif isinstance(exp, parser.Var):
        if exp.identifier in variable_map:
            return parser.Var(variable_map[exp.identifier].name)
        else:
            raise SyntaxError("Undeclared variable!")
    elif isinstance(exp, parser.Unary):
        if exp.operator in inc_dec_operators:
            if not isinstance(exp.inner, parser.Var):
                raise SyntaxError("Invalid lvalue!")
        return parser.Unary(exp.operator, resolve_exp(exp.inner, variable_map))
    elif isinstance(exp, parser.Binary):
        return parser.Binary(exp.operator,
                             resolve_exp(exp.left, variable_map),
                             resolve_exp(exp.right, variable_map))
    elif isinstance(exp, parser.Constant):
        return parser.Constant(exp.value)
    elif isinstance(exp, parser.Conditional):
        return parser.Conditional(resolve_exp(exp.condition, variable_map),
                                  resolve_exp(exp.then, variable_map),
                                  resolve_exp(exp.else_, variable_map))
    else:
        raise SyntaxError("Invalid expression!")


def loop_labeling(ast_program: parser.Program):
    for function in ast_program.functions:
        ll_process_function(function)


def ll_process_function(function: parser.Function):
    context = {'loop_label': '', 'switch_label': '', 'has_default': False, 'cases': []}
    function.block = ll_process_block(function.block, context)


def ll_process_block(block: parser.Block, context):
    block_items = []
    for item in block.block_items:
        if isinstance(item, parser.VarDecl):
            block_items.append(item)
        elif isinstance(item, parser.Statement):
            block_items.append(ll_process_statement(item, context))
    return parser.Block(block_items)


def ll_process_statement(statement: parser.Statement, context):
    if isinstance(statement, parser.Switch):
        old_switch_label = context.get('switch_label', '')
        old_has_default = context.get('has_default', False)
        old_cases = context.get('cases', [])
        new_switch_label = make_label()
        context['switch_label'] = new_switch_label
        context['has_default'] = False
        context['cases'] = []
        body = ll_process_statement(statement.body, context)
        context['switch_label'] = old_switch_label
        context['has_default'] = old_has_default
        context['cases'] = old_cases
        return parser.Switch(statement.expr, body, new_switch_label)
    elif isinstance(statement, parser.Default):
        if context.get('switch_label', '') == '':
            raise SyntaxError("Default statement not within switch!")
        if context['has_default']:
            raise SyntaxError("Multiple default labels in one switch!")
        context['has_default'] = True
        body = ll_process_statement(statement.statement, context)
        return parser.Default(body)
    elif isinstance(statement, parser.Case):
        if context.get('switch_label', '') == '':
            raise SyntaxError("Case statement not within switch!")
        body = ll_process_statement(statement.statement, context)
        if statement.const in context['cases']:
            raise SyntaxError(f'Duplicate case value {statement.const}')
        context['cases'].append(statement.const)
        return parser.Case(statement.const, body)
    elif isinstance(statement, parser.If):
        then = ll_process_statement(statement.then, context)
        else_ = ll_process_statement(statement.else_, context)
        return parser.If(statement.condition, then, else_)
    elif isinstance(statement, parser.While):
        old_loop_label = context.get('loop_label', '')
        new_loop_label = make_label()
        context['loop_label'] = new_loop_label
        body = ll_process_statement(statement.body, context)
        context['loop_label'] = old_loop_label
        return parser.While(statement.condition, body, new_loop_label)
    elif isinstance(statement, parser.DoWhile):
        old_loop_label = context.get('loop_label', '')
        new_loop_label = make_label()
        context['loop_label'] = new_loop_label
        body = ll_process_statement(statement.body, context)
        context['loop_label'] = old_loop_label
        return parser.DoWhile(statement.condition, body, new_loop_label)
    elif isinstance(statement, parser.For):
        old_loop_label = context.get('loop_label', '')
        new_loop_label = make_label()
        context['loop_label'] = new_loop_label
        body = ll_process_statement(statement.body, context)
        context['loop_label'] = old_loop_label
        return parser.For(statement.for_init, statement.condition, statement.post, body, new_loop_label)
    elif isinstance(statement, parser.Break):
        if context.get('switch_label', '') != '':
            statement.label = context['switch_label']
            return statement
        elif context.get('loop_label', '') != '':
            statement.label = context['loop_label']
            return statement
        else:
            raise SyntaxError("Break statement not within loop or switch!")
    elif isinstance(statement, parser.Continue):
        if context.get('loop_label', '') != '':
            statement.label = context['loop_label']
            return statement
        else:
            raise SyntaxError("Continue statement not within loop!")
    elif isinstance(statement, parser.Label):
        body = ll_process_statement(statement.statement, context)
        return parser.Label(statement.label, body)
    elif isinstance(statement, parser.Compound):
        body = ll_process_block(statement.block, context)
        return parser.Compound(body)    
    else:
        return statement


def ll_process_for_statement(statement: parser.For, loop_label: str, switch_label: str):
    body = ll_process_statement(statement.body, loop_label, switch_label)
    return parser.For(statement.for_init, statement.condition, statement.post, body, loop_label)


def ll_process_compound(statement: parser.Compound, loop_label: str, switch_label: str):
    block = ll_process_block(statement.block, loop_label, switch_label)
    return parser.Compound(block)
