import lexer
from dataclasses import dataclass
from typing import List, Optional

from common import UnaryOperator, BinaryOperator

precedence = {
    lexer.MULTIPLICATION_OP: 50,
    lexer.DIVISION_OP: 50,
    lexer.MODULO_OP: 50,
    lexer.ADDITION_OP: 45,
    lexer.SUBTRACTION_OP: 45,
    lexer.BITWISE_LEFT_SHIFT_OP: 40,
    lexer.BITWISE_RIGHT_SHIFT_OP: 40,
    lexer.LESS_THAN_OP: 38,
    lexer.LESS_THAN_OR_EQUAL_TO_OP: 38,
    lexer.GREATER_THAN_OP: 38,
    lexer.GREATER_THAN_OR_EQUAL_TO_OP: 38,
    lexer.EQUAL_TO_OP: 37,
    lexer.NOT_EQUAL_TO_OP: 37,
    lexer.BITWISE_AND_OP: 30,
    lexer.BITWISE_XOR_OP: 25,
    lexer.BITWISE_OR_OP: 20,
    lexer.LOGICAL_AND_OP: 15,
    lexer.LOGICAL_OR_OP: 10,
    lexer.ASSIGNMENT_OP: 1,
    lexer.ADDITION_ASSIGNMENT_OP: 1,
    lexer.SUBTRACTION_ASSIGNMENT_OP: 1,
    lexer.MULTIPLICATION_ASSIGNMENT_OP: 1,
    lexer.DIVISION_ASSIGNMENT_OP: 1,
    lexer.REMAINDER_ASSIGNMENT_OP: 1,
    lexer.BITWISE_OR_ASSIGNMENT_OP: 1,
    lexer.BITWISE_AND_ASSIGNMENT_OP: 1,
    lexer.BITWISE_XOR_ASSIGNMENT_OP: 1,
    lexer.BITWISE_LEFT_SHIFT_ASSIGNMENT_OP: 1,
    lexer.BITWISE_RIGHT_SHIFT_ASSIGNMENT_OP: 1
}


binary_ops = {
    lexer.ADDITION_OP,
    lexer.SUBTRACTION_OP,
    lexer.MODULO_OP,
    lexer.DIVISION_OP,
    lexer.MULTIPLICATION_OP,
    lexer.BITWISE_LEFT_SHIFT_OP,
    lexer.BITWISE_RIGHT_SHIFT_OP,
    lexer.BITWISE_AND_OP,
    lexer.BITWISE_XOR_OP,
    lexer.BITWISE_OR_OP,
    lexer.LESS_THAN_OP,
    lexer.LESS_THAN_OR_EQUAL_TO_OP,
    lexer.GREATER_THAN_OP,
    lexer.GREATER_THAN_OR_EQUAL_TO_OP,
    lexer.EQUAL_TO_OP,
    lexer.NOT_EQUAL_TO_OP,
    lexer.LOGICAL_AND_OP,
    lexer.LOGICAL_OR_OP,
    lexer.ASSIGNMENT_OP,
    lexer.ADDITION_ASSIGNMENT_OP,
    lexer.SUBTRACTION_ASSIGNMENT_OP,
    lexer.MULTIPLICATION_ASSIGNMENT_OP,
    lexer.DIVISION_ASSIGNMENT_OP,
    lexer.REMAINDER_ASSIGNMENT_OP,
    lexer.BITWISE_OR_ASSIGNMENT_OP,
    lexer.BITWISE_AND_ASSIGNMENT_OP,
    lexer.BITWISE_XOR_ASSIGNMENT_OP,
    lexer.BITWISE_LEFT_SHIFT_ASSIGNMENT_OP,
    lexer.BITWISE_RIGHT_SHIFT_ASSIGNMENT_OP
}


assignment_ops = {
    lexer.ASSIGNMENT_OP,
    lexer.ADDITION_ASSIGNMENT_OP,
    lexer.SUBTRACTION_ASSIGNMENT_OP,
    lexer.MULTIPLICATION_ASSIGNMENT_OP,
    lexer.DIVISION_ASSIGNMENT_OP,
    lexer.REMAINDER_ASSIGNMENT_OP,
    lexer.BITWISE_OR_ASSIGNMENT_OP,
    lexer.BITWISE_AND_ASSIGNMENT_OP,
    lexer.BITWISE_XOR_ASSIGNMENT_OP,
    lexer.BITWISE_LEFT_SHIFT_ASSIGNMENT_OP,
    lexer.BITWISE_RIGHT_SHIFT_ASSIGNMENT_OP
}


class Node:
    pass


@dataclass
class Program(Node):
    functions: List['Function']


@dataclass
class Function(Node):
    name: str
    body: List['BlockItem']


class BlockItem(Node):
    pass


@dataclass
class Declaration(BlockItem):
    name: str
    init: Optional['Expression'] = None


class Statement(BlockItem):
    pass


@dataclass
class Return(Statement):
    exp: 'Expression'


class Null(Statement):
    pass


class Expression(Statement):
    pass


@dataclass
class Constant(Expression):
    value: str


@dataclass
class Var(Expression):
    identifier: str


@dataclass
class Unary(Expression):
    operator: 'UnaryOperator'
    inner: 'Expression'


@dataclass
class Binary(Expression):
    operator: 'BinaryOperator'
    left: 'Expression'
    right: 'Expression'


@dataclass
class Assignment(Expression):
    left: 'Expression'
    right: 'Expression'


@dataclass
class Identifier(Node):
    name: str


def parse(tokens):
    functions = []
    while tokens:
        func = parse_function(tokens)
        functions.append(func)
    return Program(functions)


def parse_function(tokens):
    expect(lexer.INT, tokens)
    name = expect(lexer.IDENTIFIER, tokens)[1]
    expect(lexer.OPEN_PAREN, tokens)
    expect(lexer.VOID, tokens)
    expect(lexer.CLOSE_PAREN, tokens)
    expect(lexer.OPEN_BRACE, tokens)

    function_body = []
    next_token = peek(tokens)
    while next_token[0] != lexer.CLOSE_BRACE:
        next_block_item = parse_block_item(tokens)
        function_body.append(next_block_item)
        next_token = peek(tokens)

    pop(tokens)

    return Function(name, function_body)


def parse_block_item(tokens):
    next_token = peek(tokens)
    if next_token[0] == lexer.INT:
        return parse_declaration(tokens)
    else:
        return parse_statement(tokens)


def parse_statement(tokens):
    next_token = peek(tokens)
    if next_token[0] == lexer.RETURN:
        return parse_return(tokens)
    elif next_token[0] == lexer.SEMICOLON:
        pop(tokens)
        return Null()
    else:
        exp = parse_expression(tokens, 0)
        expect(lexer.SEMICOLON, tokens)
        return exp


def parse_declaration(tokens):
    expect(lexer.INT, tokens)
    identifier = expect(lexer.IDENTIFIER, tokens)[1]
    next_token = peek(tokens)
    exp = None
    if next_token[0] == lexer.ASSIGNMENT_OP:
        pop(tokens)
        exp = parse_expression(tokens, 0)
    expect(lexer.SEMICOLON, tokens)
    return Declaration(identifier, exp)


def parse_return(tokens):
    expect(lexer.RETURN, tokens)
    val = parse_expression(tokens, 0)
    expect(lexer.SEMICOLON, tokens)
    return Return(val)


def parse_expression(tokens, min_precedence):
    left = parse_prefix_expression(tokens)
    next_token = peek(tokens)
    while next_token[0] in binary_ops and precedence[next_token[0]] >= min_precedence:
        if next_token[0] in assignment_ops:
            pop(tokens)
            right = parse_expression(tokens, precedence[next_token[0]])
            if next_token[0] != lexer.ASSIGNMENT_OP:
                right = Binary(parse_assignment_operator(next_token[0]), left, right)
            left = Assignment(left, right)
        else:
            bin_op = parse_binary_operator(tokens)
            right = parse_expression(tokens, precedence[next_token[0]] + 1)
            left = Binary(bin_op, left, right)
        next_token = peek(tokens)
    return parse_postfix(tokens, left)


def parse_prefix_expression(tokens):
    next_token = peek(tokens)
    if next_token[0] in {lexer.BITWISE_COMPLEMENT_OP, lexer.SUBTRACTION_OP, lexer.LOGICAL_NOT_OP, lexer.INCREMENT_OP, lexer.DECREMENT_OP}:
        return parse_prefix(tokens)
    else:
        return parse_postfix(tokens, parse_factor(tokens))


def parse_factor(tokens):
    next_token = peek(tokens)
    if next_token[0] == lexer.CONSTANT:
        return parse_constant(tokens)
    elif next_token[0] == lexer.OPEN_PAREN:
        pop(tokens)  # Consume '('
        inner_exp = parse_expression(tokens, 0)
        expect(lexer.CLOSE_PAREN, tokens)
        return inner_exp
    else:
        identifier = expect(lexer.IDENTIFIER, tokens)[1]
        return Var(identifier)


def parse_prefix(tokens):
    operator = parse_unary_operator(tokens)
    inner_exp = parse_prefix_expression(tokens)
    return Unary(operator, inner_exp)


def parse_postfix(tokens, left):
    next_token = peek(tokens)
    while next_token[0] in {lexer.INCREMENT_OP, lexer.DECREMENT_OP}:
        operator = pop(tokens)[0]
        if operator == lexer.INCREMENT_OP:
            left = Unary(UnaryOperator.POST_INCREMENT, left)
        elif operator == lexer.DECREMENT_OP:
            left = Unary(UnaryOperator.POST_DECREMENT, left)
        next_token = peek(tokens)
    return left


def parse_constant(tokens):
    value = expect(lexer.CONSTANT, tokens)[1]
    return Constant(value)


def parse_unary(tokens):
    operator = parse_unary_operator(tokens)
    inner_exp = parse_factor(tokens)
    return Unary(operator, inner_exp)


def parse_assignment_operator(op):
    match op:
        case lexer.ADDITION_ASSIGNMENT_OP:
            return BinaryOperator.ADD
        case lexer.SUBTRACTION_ASSIGNMENT_OP:
            return BinaryOperator.SUBTRACT
        case lexer.MULTIPLICATION_ASSIGNMENT_OP:
            return BinaryOperator.MULTIPLY
        case lexer.DIVISION_ASSIGNMENT_OP:
            return BinaryOperator.DIVIDE
        case lexer.REMAINDER_ASSIGNMENT_OP:
            return BinaryOperator.REMAINDER
        case lexer.BITWISE_OR_ASSIGNMENT_OP:
            return BinaryOperator.BITWISE_OR
        case lexer.BITWISE_AND_ASSIGNMENT_OP:
            return BinaryOperator.BITWISE_AND
        case lexer.BITWISE_XOR_ASSIGNMENT_OP:
            return BinaryOperator.BITWISE_XOR
        case lexer.BITWISE_LEFT_SHIFT_ASSIGNMENT_OP:
            return BinaryOperator.BITWISE_LEFTSHIFT
        case lexer.BITWISE_RIGHT_SHIFT_ASSIGNMENT_OP:
            return BinaryOperator.BITWISE_RIGHTSHIFT


def parse_unary_operator(tokens):
    op = pop(tokens)
    if op[0] == lexer.BITWISE_COMPLEMENT_OP:
        return UnaryOperator.COMPLEMENT
    elif op[0] == lexer.SUBTRACTION_OP:
        return UnaryOperator.NEGATE
    elif op[0] == lexer.LOGICAL_NOT_OP:
        return UnaryOperator.NOT
    elif op[0] == lexer.INCREMENT_OP:
        return UnaryOperator.PRE_INCREMENT
    elif op[0] == lexer.DECREMENT_OP:
        return UnaryOperator.PRE_DECREMENT
    else:
        raise SyntaxError(f"Unexpected operator: {op}")


def parse_binary_operator(tokens):
    op = pop(tokens)
    if op[0] == lexer.SUBTRACTION_OP:
        return BinaryOperator.SUBTRACT
    elif op[0] == lexer.ADDITION_OP:
        return BinaryOperator.ADD
    elif op[0] == lexer.DIVISION_OP:
        return BinaryOperator.DIVIDE
    elif op[0] == lexer.MODULO_OP:
        return BinaryOperator.REMAINDER
    elif op[0] == lexer.MULTIPLICATION_OP:
        return BinaryOperator.MULTIPLY
    elif op[0] == lexer.BITWISE_LEFT_SHIFT_OP:
        return BinaryOperator.BITWISE_LEFTSHIFT
    elif op[0] == lexer.BITWISE_RIGHT_SHIFT_OP:
        return BinaryOperator.BITWISE_RIGHTSHIFT
    elif op[0] == lexer.BITWISE_AND_OP:
        return BinaryOperator.BITWISE_AND
    elif op[0] == lexer.BITWISE_XOR_OP:
        return BinaryOperator.BITWISE_XOR
    elif op[0] == lexer.BITWISE_OR_OP:
        return BinaryOperator.BITWISE_OR
    elif op[0] == lexer.LOGICAL_AND_OP:
        return BinaryOperator.LOGICAL_AND
    elif op[0] == lexer.LOGICAL_OR_OP:
        return BinaryOperator.LOGICAL_OR
    elif op[0] == lexer.EQUAL_TO_OP:
        return BinaryOperator.EQUAL_TO
    elif op[0] == lexer.NOT_EQUAL_TO_OP:
        return BinaryOperator.NOT_EQUAL_TO
    elif op[0] == lexer.LESS_THAN_OP:
        return BinaryOperator.LESS_THAN
    elif op[0] == lexer.LESS_THAN_OR_EQUAL_TO_OP:
        return BinaryOperator.LESS_THAN_OR_EQUAL
    elif op[0] == lexer.GREATER_THAN_OP:
        return BinaryOperator.GREATER_THAN
    elif op[0] == lexer.GREATER_THAN_OR_EQUAL_TO_OP:
        return BinaryOperator.GREATER_THAN_OR_EQUAL_TO
    else:
        raise SyntaxError(f"Unexpected operator: {op}")


def pop(tokens):
    if not tokens:
        raise SyntaxError("Unexpected end of input")
    return tokens.pop(0)


def peek(tokens):
    if not tokens:
        raise SyntaxError("Unexpected end of input")
    return tokens[0]


def expect(type_, tokens):
    if not tokens:
        raise SyntaxError(f"Expected {type_}, but reached end of input")
    actual = pop(tokens)
    if actual[0] != type_:
        raise SyntaxError(f'Expected {type_}, got {actual}')
    return actual
