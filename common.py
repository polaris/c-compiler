from enum import Enum, auto


class UnaryOperator(Enum):
    NEGATE = auto()
    COMPLEMENT = auto()
    NOT = auto()
    PRE_INCREMENT = auto()
    PRE_DECREMENT = auto()
    POST_INCREMENT = auto()
    POST_DECREMENT = auto()


class BinaryOperator(Enum):
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    REMAINDER = auto()
    BITWISE_LEFTSHIFT = auto()
    BITWISE_RIGHTSHIFT = auto()
    BITWISE_AND = auto()
    BITWISE_OR = auto()
    BITWISE_XOR = auto()
    LOGICAL_AND = auto()
    LOGICAL_OR = auto()
    EQUAL_TO = auto()
    NOT_EQUAL_TO = auto()
    LESS_THAN = auto()
    LESS_THAN_OR_EQUAL = auto()
    GREATER_THAN = auto()
    GREATER_THAN_OR_EQUAL_TO = auto()


relational_ops = {BinaryOperator.EQUAL_TO,
                  BinaryOperator.NOT_EQUAL_TO,
                  BinaryOperator.GREATER_THAN,
                  BinaryOperator.GREATER_THAN_OR_EQUAL_TO,
                  BinaryOperator.LESS_THAN,
                  BinaryOperator.LESS_THAN_OR_EQUAL}
