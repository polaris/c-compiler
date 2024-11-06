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
        context = None
        instructions = self.translate_block(function.block, context)
        instructions.append(Return(Constant(0)))
        return Function(function.name, instructions)
    
    def translate_block(self, block: 'parser.Block', context):
        instructions = []
        for item in block.block_items:
            if isinstance(item, parser.Statement):
                instructions.extend(self.translate_statement(item, context))
            elif isinstance(item, parser.Declaration):
                instructions.extend(self.translate_declaration(item))
        return instructions

    def translate_statement(self, statement: 'parser.Statement', context) -> List[Instruction]:
        if isinstance(statement, parser.Return):
            return self.translate_return(statement)
        elif isinstance(statement, parser.If):
            return self.translate_if(statement, context)
        elif isinstance(statement, parser.Goto):
            return self.translate_goto(statement)
        elif isinstance(statement, parser.Break):
            return self.translate_break(statement, context)
        elif isinstance(statement, parser.Continue):
            return self.translate_continue(statement, context)
        elif isinstance(statement, parser.Switch):
            return self.translate_switch(statement, context)
        elif isinstance(statement, parser.Case):
            return self.translate_case(statement, context)
        elif isinstance(statement, parser.Default):
            return self.translate_default(statement, context)
        elif isinstance(statement, parser.DoWhile):
            return self.translate_do_while(statement, context)
        elif isinstance(statement, parser.While):
            return self.translate_while(statement, context)
        elif isinstance(statement, parser.For):
            return self.translate_for(statement, context)
        elif isinstance(statement, parser.Label):
            return self.translate_label(statement, context)
        elif isinstance(statement, parser.Compound):
            return self.translate_block(statement.block, context)
        elif isinstance(statement, parser.Expression):
            return self.translate_expression(statement)
        elif isinstance(statement, parser.Null):
            return self.translate_null()
        else:
            raise SyntaxError(f'Unexpected statement type: {type(statement)}')

    def translate_null(self):
        return []

    def translate_continue(self, statement, context):
        instructions = []
        if context and 'continue_label' in context:
            instructions.append(Jump(context['continue_label']))
        else:
            raise SyntaxError('Continue statement not inside loop')
        return instructions

    def translate_break(self, statement: 'parser.Break', context):
        instructions = []
        if context and 'break_label' in context:
            instructions.append(Jump(context['break_label']))
        elif context and 'break_label' in context:
            instructions.append(Jump(context['break_label']))
        else:
            raise SyntaxError('Break statement not inside loop or switch')
        return instructions
    
    def translate_case(self, statement: 'parser.Case', context):
        instructions = []
        if context is None:
            raise SyntaxError('Case statement not inside a switch')
        case_label = self.generate_unique_label('case')
        case_value = statement.const.value
        context['cases'].append((case_value, case_label))
        instructions.append(Label(case_label))
        instructions.extend(self.translate_statement(statement.statement, context))
        return instructions
    
    def translate_default(self, statement: 'parser.Default', context):
        instructions = []
        if context is None:
            raise SyntaxError('Default statement not inside a switch')
        if context['default_label'] is not None:
            raise SyntaxError('Multiple default labels in switch')
        default_label = self.generate_unique_label('default')
        context['default_label'] = default_label
        instructions.append(Label(default_label))
        instructions.extend(self.translate_statement(statement.statement, context))
        return instructions

    def translate_expression(self, statement):
        instructions = []
        dst = Variable(utils.make_temporary())
        value = self.emit_tacky(statement, instructions)
        instructions.append(Copy(value, dst))
        return instructions

    def translate_for(self, statement: 'parser.For', context):
        instructions = []
        start_label = self.generate_unique_label("start")
        break_label = f'break_{statement.label}'
        continue_label = f'continue_{statement.label}'
        old_context = context
        context = {
            'cases': (old_context or {}).get('cases'),
            'default_label': (old_context or {}).get('default_label'),
            'break_label': break_label,
            'continue_label': continue_label,
            'switch_value': (old_context or {}).get('switch_value'),
        }
        instructions.extend(self.translate_for_init(statement.for_init))
        instructions.append(Label(start_label))
        if statement.condition is not None:
            c = self.emit_tacky(statement.condition, instructions)
            instructions.append(JumpIfZero(c, break_label))
        instructions.extend(self.translate_statement(statement.body, context))
        instructions.append(Label(continue_label))
        if statement.post is not None:
            self.emit_tacky(statement.post, instructions)
        instructions.append(Jump(start_label))
        instructions.append(Label(break_label))
        context = old_context
        return instructions

    def translate_while(self, statement: 'parser.While', context):
        instructions = []
        break_label = f'break_{statement.label}'
        continue_label = f'continue_{statement.label}'
        old_context = context
        context = {
            'cases': (old_context or {}).get('cases'),
            'default_label': (old_context or {}).get('default_label'),
            'break_label': break_label,
            'continue_label': continue_label,
            'switch_value': (old_context or {}).get('switch_value'),
        }
        instructions.append(Label(continue_label))
        c = self.emit_tacky(statement.condition, instructions)
        instructions.append(JumpIfZero(c, break_label))
        instructions.extend(self.translate_statement(statement.body, context))
        instructions.append(Jump(continue_label))
        instructions.append(Label(break_label))
        context = old_context
        return instructions

    def translate_do_while(self, statement: 'parser.DoWhile', context):
        instructions = []
        start_label = self.generate_unique_label("start")
        break_label = f'break_{statement.label}'
        continue_label = f'continue_{statement.label}'
        old_context = context
        context = {
            'cases': (old_context or {}).get('cases'),
            'default_label': (old_context or {}).get('default_label'),
            'break_label': break_label,
            'continue_label': continue_label,
            'switch_value': (old_context or {}).get('switch_value'),
        }
        instructions.append(Label(start_label))
        instructions.extend(self.translate_statement(statement.body, context))
        instructions.append(Label(continue_label))
        c = self.emit_tacky(statement.condition, instructions)
        instructions.append(JumpIfNotZero(c, start_label))
        instructions.append(Label(break_label))
        context = old_context
        return instructions

    def translate_switch(self, switch_stmt: 'parser.Switch', context) -> List[Instruction]:
        instructions = []
        switch_value = self.emit_tacky(switch_stmt.expr, instructions)
        break_label = f'break_{switch_stmt.label}'
        old_context = context
        switch_context = {
            'cases': [],
            'default_label': None,
            'break_label': break_label,
            'continue_label': (old_context or {}).get('continue_label'),
            'switch_value': switch_value,
        }
        context = switch_context
        body_instructions = self.translate_statement(switch_stmt.body, context)
        context = old_context
        dispatch_instructions = []
        for case_value, case_label in switch_context['cases']:
            tmp = Variable(utils.make_temporary())
            instructions.append(Binary(common.BinaryOperator.EQUAL_TO, switch_value, Constant(case_value), tmp))
            dispatch_instructions.append(JumpIfNotZero(tmp, case_label))
        if switch_context['default_label'] is not None:
            dispatch_instructions.append(Jump(switch_context['default_label']))
        else:
            dispatch_instructions.append(Jump(break_label))
        instructions.extend(dispatch_instructions)
        instructions.extend(body_instructions)
        instructions.append(Label(break_label))
        return instructions

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
    
    def translate_if(self, if_stmt: 'parser.If', context) -> List[Instruction]:
        instructions = []
        if not if_stmt.else_:
            end_label = self.generate_unique_label("end")
            c = self.emit_tacky(if_stmt.condition, instructions)
            instructions.append(JumpIfZero(c, end_label))
            instructions.extend(self.translate_statement(if_stmt.then, context))
            instructions.append(Label(end_label))
        else:
            else_label = self.generate_unique_label("else")
            end_label = self.generate_unique_label("end")
            c = self.emit_tacky(if_stmt.condition, instructions)
            instructions.append(JumpIfZero(c, else_label))
            instructions.extend(self.translate_statement(if_stmt.then, context))
            instructions.append(Jump(end_label))
            instructions.append(Label(else_label))
            instructions.extend(self.translate_statement(if_stmt.else_, context))
            instructions.append(Label(end_label))
        return instructions
    
    def translate_goto(self, goto_stmt: 'parser.Goto') -> List[Instruction]:
        instructions = [Jump(goto_stmt.label)]
        return instructions
    
    def translate_label(self, label_stmt: 'parser.Label', context):
        instructions = [Label(label_stmt.label)]
        instructions.extend(self.translate_statement(label_stmt.statement, context))
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


    def translate_for_init(self, for_init: 'parser.ForInit'):
        instructions = []
        if isinstance(for_init, parser.InitDeclaration):
            instructions.extend(self.translate_declaration(for_init.declaration))
        elif isinstance(for_init, parser.InitExpression):
            self.emit_tacky(for_init.expression, instructions)
        return instructions
