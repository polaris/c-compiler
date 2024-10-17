import common
import parser
import utils
from dataclasses import dataclass
from typing import List, Union


class Node:
    pass


@dataclass
class Program(Node):
    functions: List['Function']


@dataclass
class Function(Node):
    identifier: str
    instructions: List['Instruction']


class Instruction(Node):
    pass


@dataclass
class Return(Instruction):
    value: 'Value'


@dataclass
class Unary(Instruction):
    operator: 'common.UnaryOperator'
    src: 'Value'
    dst: 'Variable'


@dataclass
class Binary(Instruction):
    operator: 'common.BinaryOperator'
    src1: 'Value'
    src2: 'Value'
    dst: 'Variable'


@dataclass
class Copy(Instruction):
    src: 'Value'
    dst: 'Variable'


@dataclass
class Jump(Instruction):
    target: str


@dataclass
class JumpIfZero(Instruction):
    condition: 'Value'
    target: str


@dataclass
class JumpIfNotZero(Instruction):
    condition: 'Value'
    target: str


@dataclass
class Label(Instruction):
    identifier: str


class Value(Node):
    pass


@dataclass
class Constant(Value):
    value: Union[int, float, str]


@dataclass
class Variable(Value):
    identifier: str


class Translator:
    def __init__(self):
        self.label_count = 0

    def translate(self, program: 'parser.Program') -> Program:
        functions = [self.translate_function(function) for function in program.functions]
        return Program(functions)

    def translate_function(self, function: 'parser.Function') -> Function:
        instructions = []
        for item in function.body:
            if isinstance(item, parser.Statement):
                instructions.extend(self.translate_statement(item))
            elif isinstance(item, parser.Declaration):
                instructions.extend(self.translate_declaration(item))
        instructions.append(Return(Constant(0)))
        return Function(function.name, instructions)

    def translate_statement(self, statement: 'parser.Statement') -> List[Instruction]:
        if isinstance(statement, parser.Return):
            return self.translate_return(statement)
        elif isinstance(statement, parser.If):
            return self.translate_if(statement)
        elif isinstance(statement, parser.Goto):
            return self.translate_goto(statement)
        elif isinstance(statement, parser.Label):
            return self.translate_label(statement)
        elif isinstance(statement, parser.Expression):
            instructions = []
            dst = Variable(utils.make_temporary())
            value = self.emit_tacky(statement, instructions)
            instructions.append(Copy(value, dst))
            return instructions
        elif isinstance(statement, parser.Null):
            return []
        else:
            raise SyntaxError(f'Unexpected statement type: {type(statement)}')

    def translate_declaration(self, declaration: 'parser.Declaration') -> List[Instruction]:
        instructions = []
        if declaration.init is not None:
            value = self.emit_tacky(declaration.init, instructions)
            var = Variable(declaration.name)
            instructions.append(Copy(value, var))
        return instructions

    def translate_return(self, return_stmt: 'parser.Return') -> List[Instruction]:
        instructions = []
        val = self.emit_tacky(return_stmt.exp, instructions)
        instructions.append(Return(val))
        return instructions
    
    def translate_if(self, if_stmt: 'parser.If') -> List[Instruction]:
        instructions = []
        if not if_stmt.else_:
            end_label = self.generate_unique_label("end")
            c = self.emit_tacky(if_stmt.condition,instructions)
            instructions.append(JumpIfZero(c, end_label))
            instructions.extend(self.translate_statement(if_stmt.then))
            instructions.append(Label(end_label))
        else:
            else_label = self.generate_unique_label("else")
            end_label = self.generate_unique_label("end")
            c = self.emit_tacky(if_stmt.condition, instructions)
            instructions.append(JumpIfZero(c, else_label))
            instructions.extend(self.translate_statement(if_stmt.then))
            instructions.append(Jump(end_label))
            instructions.append(Label(else_label))
            instructions.extend(self.translate_statement(if_stmt.else_))
            instructions.append(Label(end_label))
        return instructions
    
    def translate_goto(self, goto_stmt: 'parser.Goto') -> List[Instruction]:
        instructions = []
        instructions.append(Jump(goto_stmt.label))
        return instructions
    
    def translate_label(self, label_stmt: 'parser.Label'):
        instructions = []
        instructions.append(Label(label_stmt.label))
        instructions.extend(self.translate_statement(label_stmt.statement))
        return instructions

    def emit_tacky(self, exp: 'parser.Expression', instructions: List[Instruction]) -> Value:
        if isinstance(exp, parser.Constant):
            return Constant(exp.value)
        elif isinstance(exp, parser.Conditional):
            result = Variable(utils.make_temporary())
            else_label = self.generate_unique_label("else")
            end_label = self.generate_unique_label("end")
            c = self.emit_tacky(exp.condition, instructions)
            instructions.append(JumpIfZero(c, else_label))
            v1 = self.emit_tacky(exp.then, instructions)
            instructions.append(Copy(v1, result))
            instructions.append(Jump(end_label))
            instructions.append(Label(else_label))
            v2 = self.emit_tacky(exp.else_, instructions)
            instructions.append(Copy(v2, result))
            instructions.append(Label(end_label))
            return result
        elif isinstance(exp, parser.Unary):
            if exp.operator == common.UnaryOperator.PRE_INCREMENT:
                src = self.emit_tacky(exp.inner, instructions)
                dst = Variable(utils.make_temporary())
                instructions.append(Binary(common.BinaryOperator.ADD, src, Constant(1), src))
                instructions.append(Copy(src, dst))
                return dst
            elif exp.operator == common.UnaryOperator.PRE_DECREMENT:
                src = self.emit_tacky(exp.inner, instructions)
                dst = Variable(utils.make_temporary())
                instructions.append(Binary(common.BinaryOperator.SUBTRACT, src, Constant(1), src))
                instructions.append(Copy(src, dst))
                return dst
            elif exp.operator == common.UnaryOperator.POST_INCREMENT:
                src = self.emit_tacky(exp.inner, instructions)
                dst = Variable(utils.make_temporary())
                instructions.append(Copy(src, dst))
                instructions.append(Binary(common.BinaryOperator.ADD, src, Constant(1), src))
                return dst
            elif exp.operator == common.UnaryOperator.POST_DECREMENT:
                src = self.emit_tacky(exp.inner, instructions)
                dst = Variable(utils.make_temporary())
                instructions.append(Copy(src, dst))
                instructions.append(Binary(common.BinaryOperator.SUBTRACT, src, Constant(1), src))
                return dst
            else:
                src = self.emit_tacky(exp.inner, instructions)
                dst = Variable(utils.make_temporary())
                instructions.append(Unary(exp.operator, src, dst))
                return dst
        elif isinstance(exp, parser.Binary):
            if exp.operator == common.BinaryOperator.LOGICAL_AND:
                result = Variable(utils.make_temporary())
                false_label = self.generate_unique_label("false_label")
                end = self.generate_unique_label("end")
                v1 = self.emit_tacky(exp.left, instructions)
                instructions.append(JumpIfZero(v1, false_label))
                v2 = self.emit_tacky(exp.right, instructions)
                instructions.append(JumpIfZero(v2, false_label))
                instructions.append(Copy(Constant(1), result))
                instructions.append(Jump(end))
                instructions.append(Label(false_label))
                instructions.append(Copy(Constant(0), result))
                instructions.append(Label(end))
                return result
            elif exp.operator == common.BinaryOperator.LOGICAL_OR:
                result = Variable(utils.make_temporary())
                v1 = self.emit_tacky(exp.left, instructions)
                true_label = self.generate_unique_label("true_label")
                end = self.generate_unique_label("end")
                instructions.append(JumpIfNotZero(v1, true_label))
                v2 = self.emit_tacky(exp.right, instructions)
                instructions.append(JumpIfNotZero(v2, true_label))
                instructions.append(Copy(Constant(0), result))
                instructions.append(Jump(end))
                instructions.append(Label(true_label))
                instructions.append(Copy(Constant(1), result))
                instructions.append(Label(end))
                return result
            else:
                v1 = self.emit_tacky(exp.left, instructions)
                v2 = self.emit_tacky(exp.right, instructions)
                dst = Variable(utils.make_temporary())
                instructions.append(Binary(exp.operator, v1, v2, dst))
                return dst
        elif isinstance(exp, parser.Var):
            return Variable(exp.identifier)
        elif isinstance(exp, parser.Assignment) and isinstance(exp.left, parser.Var):
            v = Variable(exp.left.identifier)
            result = self.emit_tacky(exp.right, instructions)
            instructions.append(Copy(result, v))
            return result
        else:
            raise SyntaxError(f'Unexpected expression type: {type(exp)}')


    def generate_unique_label(self, prefix):
        unique_label = f"{prefix}_{self.label_count}"
        self.label_count += 1
        return unique_label
