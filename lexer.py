import re


INT = 'INT'
VOID = 'VOID'
RETURN = 'RETURN'
IDENTIFIER = 'IDENTIFIER'
CONSTANT = 'CONSTANT'

OPEN_PAREN = 'OPEN_PAREN'
CLOSE_PAREN = 'CLOSE_PAREN'
OPEN_BRACE = 'OPEN_BRACE'
CLOSE_BRACE = 'CLOSE_BRACE'

COLON = 'COLON'
ASTERISK = 'ASTERISK'
APOSTROPHE = 'APOSTROPHE'
SEMICOLON = 'SEMICOLON'
COMMA = 'COMMA'

WHITESPACE = 'WHITESPACE'
PRECOMPILER_DIRECTIVE = 'HASH'
COMMENT = 'COMMENT'

SLASH = 'SLASH'

ADDITION_ASSIGNMENT_OP = 'ADDITION_ASSIGNMENT_OP'
SUBTRACTION_ASSIGNMENT_OP = 'SUBTRACTION_ASSIGNMENT_OP'
MULTIPLICATION_ASSIGNMENT_OP = 'MULTIPLICATION_ASSIGNMENT_OP'
DIVISION_ASSIGNMENT_OP = 'DIVISION_ASSIGNMENT_OP'
REMAINDER_ASSIGNMENT_OP = 'REMAINDER_ASSIGNMENT_OP'

TWO_HYPHEN = 'TWO_HYPHEN'
HYPHEN = 'HYPHEN'
TILDE = 'TILDE'
PLUS_SIGN = 'PLUS'
PERCENT_SIGN = 'PERCENT_SIGN'

LOGICAL_NOT_OP = 'LOGICAL_NOT_OP'
LOGICAL_AND_OP = 'LOGICAL_AND_OP'
BITWISE_AND_OP = 'BITWISE_AND_OP'
LOGICAL_OR_OP = 'LOGICAL_OR_OP'
BITWISE_OR_OP = 'BITWISE_OR_OP'
BITWISE_XOR_OP = 'LOGICAL_XOR_OP'

BITWISE_AND_ASSIGNMENT_OP = 'BITWISE_AND_ASSIGNMENT_OP'
BITWISE_OR_ASSIGNMENT_OP = 'BITWISE_OR_ASSIGNMENT_OP'
BITWISE_XOR_ASSIGNMENT_OP = 'BITWISE_XOR_ASSIGNMENT_OP'
BITWISE_LEFT_SHIFT_ASSIGNMENT_OP = 'BITWISE_LEFT_SHIFT_ASSIGNMENT_OP'
BITWISE_RIGHT_SHIFT_ASSIGNMENT_OP = 'BITWISE_RIGHT_SHIFT_ASSIGNMENT_OP'

EQUAL_TO_OP = 'EQUAL_TO_OP'
ASSIGNMENT_OP = 'ASSIGNMENT_OP'
NOT_EQUAL_TO_OP = 'NOT_EQUAL_TO_OP'

LEFT_SHIFT_OP = 'LEFT_SHIFT_OP'
LESS_THAN_OP = 'LESS_THAN_OP'
RIGHT_SHIFT_OP = 'RIGHT_SHIFT_OP'
GREATER_THAN_OP = 'GREATER_THAN_OP'
LESS_THAN_OR_EQUAL_TO_OP = 'LESS_THAN_OR_EQUAL_TO_OP'
GREATER_THAN_OR_EQUAL_TO_OP = 'GREATER_THAN_OR_EQUAL_TO_OP'


token_specification = [
    (INT, r'int\b'),
    (VOID, r'void\b'),
    (RETURN, r'return\b'),
    (IDENTIFIER, r'[a-zA-Z]\w*\b'),
    (CONSTANT, r'\b\d+\b'),
    (OPEN_PAREN, r'\('),
    (CLOSE_PAREN, r'\)'),
    (OPEN_BRACE, r'\{'),
    (CLOSE_BRACE, r'\}'),
    (COLON, r':'),
    (ASTERISK, r'\*'),
    (APOSTROPHE, r'\''),
    (SEMICOLON, r';'),
    (COMMA, r','),
    (COMMENT, r'//.*|/\*[\s\S]*?\*/'),
    (PRECOMPILER_DIRECTIVE, r'#.*'),
    (SLASH, r'/'),

    (ADDITION_ASSIGNMENT_OP, '\+='),
    (SUBTRACTION_ASSIGNMENT_OP, '-='),
    (MULTIPLICATION_ASSIGNMENT_OP, '\*='),
    (DIVISION_ASSIGNMENT_OP, '/='),
    (REMAINDER_ASSIGNMENT_OP, '%='),

    (TWO_HYPHEN, r'--'),
    (HYPHEN, r'-'),
    (TILDE, r'~'),
    (PLUS_SIGN, r'\+'),
    (PERCENT_SIGN, r'%'),
    (WHITESPACE, r'\s+'),

    (EQUAL_TO_OP, r'=='),
    (ASSIGNMENT_OP, r'='),
    (NOT_EQUAL_TO_OP, r'!='),

    (LOGICAL_NOT_OP, r'!'),
    (LOGICAL_AND_OP, r'&&'),
    (BITWISE_AND_OP, r'&'),
    (LOGICAL_OR_OP, r'\|\|'),
    (BITWISE_OR_OP, r'\|'),
    (BITWISE_XOR_OP, r'\^'),

    (LEFT_SHIFT_OP, r'<<'),
    (LESS_THAN_OR_EQUAL_TO_OP, r'<='),
    (LESS_THAN_OP, r'<'),
    (RIGHT_SHIFT_OP, r'>>'),
    (GREATER_THAN_OR_EQUAL_TO_OP, r'>='),
    (GREATER_THAN_OP, r'>')
]


token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
get_token = re.compile(token_regex).match


ignored_tokens = {WHITESPACE, COMMENT, PRECOMPILER_DIRECTIVE}


def tokenize(code):
    pos = 0
    while pos < len(code):
        match = get_token(code, pos)
        if match is not None:
            type_ = match.lastgroup
            value = match.group(type_)
            if type_ not in ignored_tokens:
                yield type_, value
            pos = match.end()
        else:
            line_number = code.count('\n', 0, pos) + 1
            column_number = pos - code.rfind('\n', 0, pos)
            raise SyntaxError(f'Unexpected character at line {line_number}, column {column_number}: {code[pos]}')
