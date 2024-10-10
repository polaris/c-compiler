import tacky
from typing import List, Dict


class AssemblyNode:
    pass


class AssemblyProgram(AssemblyNode):
    def __init__(self, functions: List['AssemblyFunction']):
        self.functions = functions

    def emit(self) -> str:
        """Generate the assembly code for the entire program."""
        return "\n".join(function.emit() for function in self.functions)


class AssemblyFunction(AssemblyNode):
    def __init__(self, name: str, instructions: List['AssemblyInstruction']):
        self.name = name
        self.instructions = instructions
        self.stack_size = 0
        self.pseudo_register_map: Dict[str, int] = {}
        self.current_stack_index = -4

    def emit(self) -> str:
        header = (
            f"\t.globl _{self.name}\n"
            f"_{self.name}:\n"
            "\tpushq\t%rbp\n"
            "\tmovq\t%rsp, %rbp\n"
        )
        instructions = ''.join(str(inst.emit()) for inst in self.instructions)
        return header + instructions

    def process_function(self):
        for inst in self.instructions:
            if isinstance(inst, Mov):
                self.process_mov(inst)
            elif isinstance(inst, Unary):
                self.process_unary(inst)
            elif isinstance(inst, Binary):
                self.process_binary(inst)
            elif isinstance(inst, Cmp):
                self.process_cmp(inst)
            elif isinstance(inst, SetCC):
                self.process_setcc(inst)
            elif isinstance(inst, Idiv):
                self.process_idiv(inst)

        self.stack_size = -self.current_stack_index - 4

    def get_stack_index(self, identifier: str) -> int:
        if identifier not in self.pseudo_register_map:
            self.pseudo_register_map[identifier] = self.current_stack_index
            self.current_stack_index -= 4
        return self.pseudo_register_map[identifier]

    def process_mov(self, inst: 'Mov'):
        if isinstance(inst.src, Pseudo):
            index = self.get_stack_index(inst.src.identifier)
            inst.src = Stack(index)
        if isinstance(inst.dst, Pseudo):
            index = self.get_stack_index(inst.dst.identifier)
            inst.dst = Stack(index)

    def process_unary(self, inst: 'Unary'):
        if isinstance(inst.operand, Pseudo):
            index = self.get_stack_index(inst.operand.identifier)
            inst.operand = Stack(index)

    def process_binary(self, inst: 'Binary'):
        if isinstance(inst.src, Pseudo):
            index = self.get_stack_index(inst.src.identifier)
            inst.src = Stack(index)
        if isinstance(inst.dst, Pseudo):
            index = self.get_stack_index(inst.dst.identifier)
            inst.dst = Stack(index)

    def process_cmp(self, inst: 'Cmp'):
        if isinstance(inst.operand1, Pseudo):
            index = self.get_stack_index(inst.operand1.identifier)
            inst.operand1 = Stack(index)
        if isinstance(inst.operand2, Pseudo):
            index = self.get_stack_index(inst.operand2.identifier)
            inst.operand2 = Stack(index)


    def process_setcc(self, inst: 'SetCC'):
        if isinstance(inst.operand, Pseudo):
            index = self.get_stack_index(inst.operand.identifier)
            inst.operand = Stack(index)


    def process_idiv(self, inst: 'Idiv'):
        if isinstance(inst.src, Pseudo):
            index = self.get_stack_index(inst.src.identifier)
            inst.src = Stack(index)

    def fixing_up_instructions(self):
        self.instructions.insert(0, AllocStack(self.stack_size))
        i = 0
        while i < len(self.instructions):
            inst = self.instructions[i]
            if (
                isinstance(inst, Mov) and
                isinstance(inst.src, Stack) and
                isinstance(inst.dst, Stack)
            ):
                self.instructions[i:i+1] = [
                    Mov(inst.src, Register("r10d")),
                    Mov(Register("r10d"), inst.dst)
                ]
                i += 2
            elif isinstance(inst, Idiv) and isinstance(inst.src, Stack):
                self.instructions[i:i+1] = [
                    Mov(inst.src, Register("r10d")),
                    Idiv(Register("r10d"))
                ]
                i += 2
            elif (
                isinstance(inst, Binary) and
                isinstance(inst.binary_operator, (Add, Sub)) and
                isinstance(inst.src, Stack) and
                isinstance(inst.dst, Stack)
            ):
                self.instructions[i:i+1] = [
                    Mov(inst.src, Register("r10d")),
                    Binary(inst.binary_operator, Register("r10d"), inst.dst)
                ]
                i += 2
            elif (
                isinstance(inst, Binary) and
                isinstance(inst.binary_operator, Mult) and
                isinstance(inst.dst, Stack)
            ):
                self.instructions[i:i+1] = [
                    Mov(inst.dst, Register("r11d")),
                    Binary(Mult(), inst.src, Register("r11d")),
                    Mov(Register("r11d"), inst.dst)
                ]
                i += 3
            elif (isinstance(inst, Cmp) and
                 isinstance(inst.operand1, Stack) and
                 isinstance(inst.operand2, Stack)
            ):
                self.instructions[i:i+1] = [
                    Mov(inst.operand1, Register("r10d")),
                    Cmp(Register("r10d"), inst.operand2)
                ]
            elif (isinstance(inst, Cmp) and
                  isinstance(inst.operand2, Imm)
            ):
                self.instructions[i:i+1] = [
                    Mov(inst.operand2, Register("r11d")),
                    Cmp(inst.operand1, Register("r11d"))
                ]
            else:
                i += 1


class AssemblyInstruction(AssemblyNode):
    def emit(self):
        pass


class Mov(AssemblyInstruction):
    def __init__(self, src: 'Operand', dst: 'Operand'):
        self.src = src
        self.dst = dst

    def emit(self) -> str:
        return f"\tmovl\t{self.src.emit()}, {self.dst.emit()}\n"


class Unary(AssemblyInstruction):
    def __init__(self, operator: 'UnaryOperator', operand: 'Operand'):
        self.operator = operator
        self.operand = operand

    def emit(self) -> str:
        return f"\t{self.operator.emit()}\t{self.operand.emit()}\n"


class Binary(AssemblyInstruction):
    def __init__(self, binary_operator: 'BinaryOperator', src: 'Operand', dst: 'Operand'):
        self.binary_operator = binary_operator
        self.src = src
        self.dst = dst

    def emit(self) -> str:
        return f"\t{self.binary_operator.emit()}\t{self.src.emit()}, {self.dst.emit()}\n"


class Cmp(AssemblyInstruction):
    def __init__(self, operand1: 'Operand', operand2: 'Operand'):
        self.operand1 = operand1
        self.operand2 = operand2

    def emit(self) -> str:
        return f"\tcmpl\t{self.operand1.emit()}, {self.operand2.emit()}\n"


class Idiv(AssemblyInstruction):
    def __init__(self, src: 'Operand'):
        self.src = src

    def emit(self) -> str:
        return f"\tidivl\t{self.src.emit()}\n"


class Cdq(AssemblyInstruction):
    def emit(self) -> str:
        return "\tcdq\n"


class Jmp(AssemblyInstruction):
    def __init__(self, identifier: str):
        self.identifier = identifier

    def emit(self) -> str:
        return f"\tjmp\t.L{self.identifier}\n"


class JmpCC(AssemblyInstruction):
    def __init__(self, cond_code: 'ConditionCode', identifier: str):
        self.cond_code = cond_code
        self.identifier = identifier

    def emit(self) -> str:
        return f"\tj{self.cond_code.emit()}\t.L{self.identifier}\n"


class SetCC(AssemblyInstruction):
    def __init__(self, cond_code: 'ConditionCode', operand: 'Operand'):
        self.cond_code = cond_code
        self.operand = operand

    def emit(self) -> str:
        return f"\tset{self.cond_code.emit()}\t{self.operand.emit()}\n"


class Label(AssemblyInstruction):
    def __init__(self, identifier: str):
        self.identifier = identifier

    def emit(self) -> str:
        return f".L{self.identifier}:\n"


class AllocStack(AssemblyInstruction):
    def __init__(self, size: int):
        self.size = size

    def emit(self) -> str:
        return f"\tsubq\t${self.size}, %rsp\n"


class Ret(AssemblyInstruction):
    def emit(self) -> str:
        return "\tmovq\t%rbp, %rsp\n\tpopq\t%rbp\n\tret\n"


class UnaryOperator(AssemblyNode):
    def emit(self):
        pass


class Neg(UnaryOperator):
    def emit(self) -> str:
        return "negl"


class Not(UnaryOperator):
    def emit(self) -> str:
        return "notl"


class BinaryOperator(AssemblyNode):
    def emit(self):
        pass


class Add(BinaryOperator):
    def emit(self) -> str:
        return "addl"


class Sub(BinaryOperator):
    def emit(self) -> str:
        return "subl"


class Mult(BinaryOperator):
    def emit(self) -> str:
        return "imull"


class ShiftLeft(BinaryOperator):
    def emit(self) -> str:
        return "shll"


class ShiftRight(BinaryOperator):
    def emit(self) -> str:
        return "shrl"


class BitwiseAnd(BinaryOperator):
    def emit(self) -> str:
        return "andl"


class BitwiseOr(BinaryOperator):
    def emit(self) -> str:
        return "orl"


class BitwiseXor(BinaryOperator):
    def emit(self) -> str:
        return "xorl"


class Operand(AssemblyNode):
    def emit(self):
        pass


class Imm(Operand):
    def __init__(self, value: int):
        self.value = value

    def emit(self) -> str:
        return f"${self.value}"


class Register(Operand):
    def __init__(self, name: str):
        self.name = name

    def emit(self) -> str:
        return f"%{self.name}"


class Pseudo(Operand):
    def __init__(self, identifier: str):
        self.identifier = identifier

    def emit(self) -> str:
        return f"${self.identifier}"


class Stack(Operand):
    def __init__(self, position: int):
        self.position = position

    def emit(self) -> str:
        return f"{self.position}(%rbp)"


class ConditionCode(AssemblyNode):
    def emit(self):
        pass


class E(ConditionCode):
    def emit(self) -> str:
        return "e"


class NE(ConditionCode):
    def emit(self) -> str:
        return "ne"


class G(ConditionCode):
    def emit(self) -> str:
        return "g"


class GE(ConditionCode):
    def emit(self) -> str:
        return "ge"


class L(ConditionCode):
    def emit(self) -> str:
        return "l"


class LE(ConditionCode):
    def emit(self) -> str:
        return "le"


def translate_program(program: tacky.Program) -> AssemblyProgram:
    assembly_program = convert_to_assembly(program)
    for function in assembly_program.functions:
        function.process_function()
        function.fixing_up_instructions()
    return assembly_program


def convert_to_assembly(program: tacky.Program) -> AssemblyProgram:
    functions = [translate_function(function) for function in program.functions]
    return AssemblyProgram(functions)


def translate_function(function: tacky.Function) -> AssemblyFunction:
    instructions = []
    for instruction in function.instructions:
        instructions.extend(translate_instruction(instruction))
    return AssemblyFunction(function.identifier, instructions)


def translate_instruction(instruction: tacky.Instruction) -> List[AssemblyInstruction]:
    if isinstance(instruction, tacky.Return):
        return translate_return(instruction)
    elif isinstance(instruction, tacky.Unary):
        return translate_unary(instruction)
    elif isinstance(instruction, tacky.Binary):
        return translate_binary(instruction)
    elif isinstance(instruction, tacky.Jump):
        return translate_jump(instruction)
    elif isinstance(instruction, tacky.JumpIfZero):
        return translate_jump_if_zero(instruction)
    elif isinstance(instruction, tacky.JumpIfNotZero):
        return translate_jump_if_not_zero(instruction)
    elif isinstance(instruction, tacky.Copy):
        return translate_copy(instruction)
    elif isinstance(instruction, tacky.Label):
        return translate_label(instruction)
    else:
        raise SyntaxError(f'Unexpected instruction type: {type(instruction)}')


def translate_return(_return: tacky.Return) -> List[AssemblyInstruction]:
    value = translate_value(_return.value)
    return [Mov(value, Register('eax')), Ret()]


def translate_unary(unary: tacky.Unary) -> List[AssemblyInstruction]:
    if isinstance(unary.operator, tacky.Not):
        src_value = translate_value(unary.src)
        dst_value = translate_value(unary.dst)
        return [Cmp(Imm(0), src_value), Mov(Imm(0), dst_value), SetCC(E(), dst_value)]
    else:
        src_value = translate_value(unary.src)
        dst_value = translate_value(unary.dst)
        op = translate_operator(unary.operator)
        return [Mov(src_value, dst_value), Unary(op, dst_value)]


def translate_binary(binary: tacky.Binary) -> List[AssemblyInstruction]:
    src1_value = translate_value(binary.src1)
    src2_value = translate_value(binary.src2)
    dst_value = translate_value(binary.dst)
    instructions = []

    if isinstance(binary.operator, tacky.Divide):
        instructions.extend([
            Mov(src1_value, Register('eax')),
            Cdq(),
            Idiv(src2_value),
            Mov(Register('eax'), dst_value)
        ])
    elif isinstance(binary.operator, tacky.Remainder):
        instructions.extend([
            Mov(src1_value, Register('eax')),
            Cdq(),
            Idiv(src2_value),
            Mov(Register('edx'), dst_value)
        ])
    elif isinstance(binary.operator, tacky.RelationalOperator):
        cond_code = translate_relational_operator(binary.operator)
        instructions.extend([
            Cmp(src2_value, src1_value),
            Mov(Imm(0), dst_value),
            SetCC(cond_code, dst_value),
        ])
    else:
        op = translate_binary_operator(binary.operator)
        instructions.extend([
            Mov(src1_value, dst_value),
            Binary(op, src2_value, dst_value)
        ])
    return instructions


def translate_jump(jump: tacky.Jump) -> List[AssemblyInstruction]:
    return [Jmp(jump.target)]


def translate_jump_if_zero(jump: tacky.JumpIfZero) -> List[AssemblyInstruction]:
    value = translate_value(jump.condition)
    return [Cmp(Imm(0), value), JmpCC(E(), jump.target)]


def translate_jump_if_not_zero(jump: tacky.JumpIfNotZero) -> List[AssemblyInstruction]:
    value = translate_value(jump.condition)
    return [Cmp(Imm(0), value), JmpCC(NE(), jump.target)]


def translate_copy(copy: tacky.Copy) -> List[AssemblyInstruction]:
    src_value = translate_value(copy.src)
    dst_value = translate_value(copy.dst)
    return [Mov(src_value, dst_value)]


def translate_label(label: tacky.Label) -> List[AssemblyInstruction]:
    return [Label(label.identifier)]


def translate_value(value: tacky.Value) -> Operand:
    if isinstance(value, tacky.Constant):
        return Imm(int(value.value))
    elif isinstance(value, tacky.Variable):
        return Pseudo(value.identifier)
    else:
        raise SyntaxError(f'Unexpected value type: {type(value)}')


def translate_operator(operator: tacky.UnaryOperator) -> UnaryOperator:
    if isinstance(operator, tacky.Negate):
        return Neg()
    elif isinstance(operator, tacky.Complement):
        return Not()
    else:
        raise SyntaxError(f'Unexpected operator type: {type(operator)}')


def translate_binary_operator(binary_operator: tacky.BinaryOperator) -> BinaryOperator:
    if isinstance(binary_operator, tacky.Add):
        return Add()
    elif isinstance(binary_operator, tacky.Subtract):
        return Sub()
    elif isinstance(binary_operator, tacky.Multiply):
        return Mult()
    elif isinstance(binary_operator, tacky.LeftShift):
        return ShiftLeft()
    elif isinstance(binary_operator, tacky.RightShift):
        return ShiftRight()
    elif isinstance(binary_operator, tacky.BitwiseAnd):
        return BitwiseAnd()
    elif isinstance(binary_operator, tacky.BitwiseOr):
        return BitwiseOr()
    elif isinstance(binary_operator, tacky.BitwiseXor):
        return BitwiseXor()
    else:
        raise SyntaxError(f'Unexpected binary operator type: {type(binary_operator)}')


def translate_relational_operator(relational_operator: tacky.RelationalOperator) -> ConditionCode:
    if isinstance(relational_operator, tacky.Equal):
        return E()
    elif isinstance(relational_operator, tacky.NotEqual):
        return NE()
    elif isinstance(relational_operator, tacky.GreaterThan):
        return G()
    elif isinstance(relational_operator, tacky.GreaterThanOrEqual):
        return GE()
    elif isinstance(relational_operator, tacky.LessThan):
        return L()
    elif isinstance(relational_operator, tacky.LessThanOrEqual):
        return LE()
    else:
        raise SyntaxError(f'Unexpected relational operator type: {type(relational_operator)}')


def emit_code(assembly_program: AssemblyProgram) -> str:
    return assembly_program.emit()
