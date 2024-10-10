#!/usr/bin/env python3

import argparse
import lexer
import parser
import validation
import tacky
import codegen

def process(arguments):
    try:
        with open(arguments.file, 'r') as file:
            code = file.read()

            tokens = list(lexer.tokenize(code))
            if arguments.lex:
                return

            ast_program = parser.parse(tokens)
            if arguments.parse:
                return

            validation.run(ast_program)
            if arguments.validate:
                return

            tacky_translator = tacky.Translator()
            tacky_program = tacky_translator.translate(ast_program)
            if arguments.tacky:
                return

            assembly_program = codegen.translate_program(tacky_program)
            if arguments.codegen:
                return

            print(codegen.emit_code(assembly_program))
        return 0
    except SyntaxError as e:
        print(f"An error occurred: {e}")
        return -1

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description="Tokenize a C-like file.")
    arg_parser.add_argument('file', help="The path to the file to tokenize")
    arg_parser.add_argument('--lex', action='store_true', help="Directs the compiler to run the lexer, but stop before parsing")
    arg_parser.add_argument('--parse', action='store_true', help="Directs the compiler to run the parser, but stop before validation")
    arg_parser.add_argument('--validate', action='store_true', help="Directs the compiler to run the validation, but stop before tacky")
    arg_parser.add_argument('--tacky', action='store_true', help="Directs the compiler to run the tacky, but stop before code generation")
    arg_parser.add_argument('--codegen', action='store_true', help="Directs the compiler to run the parser, but stop before code emission")
    args = arg_parser.parse_args()
    exit(process(args))
