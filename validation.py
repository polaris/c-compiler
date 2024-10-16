import parser
import utils
from typing import Dict

from parser import Declaration


def run(ast_program: parser.Program):
    variable_map = {}
    variable_resolution(ast_program, variable_map)


def variable_resolution(ast_program: parser.Program, variable_map: Dict):
    for function in ast_program.functions:
        process_function(function, variable_map)


def process_function(function: parser.Function, variable_map: Dict):
    body = []
    for item in function.body:
        if isinstance(item, parser.Declaration):
            body.append(resolve_declaration(item, variable_map))
        elif isinstance(item, parser.Statement):
            body.append(resolve_statement(item, variable_map))
    function.body = body


def resolve_declaration(declaration: parser.Declaration, variable_map: Dict):
    if declaration.name in variable_map:
        raise SyntaxError(f'Variable {declaration.name} already defined')
    unique_name = utils.make_temporary()
    variable_map[declaration.name] = unique_name
    init = None
    if declaration.init is not None:
        init = resolve_exp(declaration.init, variable_map)
    return Declaration(unique_name, init)


def resolve_statement(statement: parser.Statement, variable_map: Dict):
    if isinstance(statement, parser.Return):
        return parser.Return(resolve_exp(statement.exp, variable_map))
    elif isinstance(statement, parser.Expression):
        return resolve_exp(statement, variable_map)
    else:
        return statement


def resolve_exp(exp: parser.Expression, variable_map: Dict):
    if isinstance(exp, parser.Assignment):
        if not isinstance(exp.left, parser.Var):
            raise SyntaxError("Invalid lvalue!")
        return parser.Assignment(resolve_exp(exp.left, variable_map), resolve_exp(exp.right, variable_map))
    elif isinstance(exp, parser.Var):
        if exp.identifier in variable_map:
            return parser.Var(variable_map[exp.identifier])
        else:
            raise SyntaxError("Undeclared variable!")
    elif isinstance(exp, parser.Unary):
        if exp.operator in {parser.UnaryOperator.PRE_INCREMENT, parser.UnaryOperator.PRE_DECREMENT, parser.UnaryOperator.POST_INCREMENT, parser.UnaryOperator.POST_DECREMENT}:
            if not isinstance(exp.inner, parser.Var):
                raise SyntaxError("Invalid lvalue!")
        return parser.Unary(exp.operator, resolve_exp(exp.inner, variable_map))
    elif isinstance(exp, parser.Binary):
        return parser.Binary(exp.operator, resolve_exp(exp.left, variable_map), resolve_exp(exp.right, variable_map))
    elif isinstance(exp, parser.Constant):
        return parser.Constant(exp.value)
    else:
        raise SyntaxError("Invalid expression!")
