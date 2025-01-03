#!/usr/bin/env python

try:
    import readline
except ModuleNotFoundError:
    pass
import sys
import codecs
import copy
import pprint
from lark import Lark, Token, Tree
from lark.visitors import Interpreter
from resolver import MiniEnvironment
from fsc_exceptions import InterpException
import ast_interp

class FoxScreamInterp(Interpreter):
    def __init__(self, parser, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser
        self.env = MiniEnvironment()
        self.env.add_obj("print", function=print)
        self.env.add_obj("true", value=True)
        self.env.add_obj("false", value=False)
        self.env.add_obj("null", value=None)
        print(self.env)
        self.prog = None

    def visit_child(self, tree, num):
        return self.visit(tree.children[num])

    def visit_or_value(self, tree):
        if isinstance(tree, Tree):
            return self.visit(tree)
        elif isinstance(tree, Token):
            return tree.value

    def get_binop(self, op):
        op = op.strip()
        if len(op.split()) > 1:
            op = op.split()
        if op == "+":
            return ast_interp.BinOp.ADD
        elif op == "-":
            return ast_interp.BinOp.SUB
        elif op == "**":
            return ast_interp.BinOp.EXP
        elif op == "*":
            return ast_interp.BinOp.MUL
        elif op == "/":
            return ast_interp.BinOp.DIV
        elif op == "//":
            return ast_interp.BinOp.INTDIV
        elif op == "%":
            return ast_interp.BinOp.MOD
        elif op == "<<":
            return ast_interp.BinOp.LSHIFT
        elif op == ">>":
            return ast_interp.BinOp.RSHIFT
        elif op == "&":
            return ast_interp.BinOp.BITAND
        elif op == "^":
            return ast_interp.BinOp.BITXOR
        elif op == "|":
            return ast_interp.BinOp.BITOR
        elif op == "==":
            return ast_interp.BinOp.EQ
        elif op == "!=":
            return ast_interp.BinOp.NE
        elif op == ">":
            return ast_interp.BinOp.GT
        elif op == "<":
            return ast_interp.BinOp.LT
        elif op == ">=":
            return ast_interp.BinOp.GE
        elif op == "<=":
            return ast_interp.BinOp.LE
        elif op == "in":
            return ast_interp.BinOp.IN
        elif op == "of":
            return ast_interp.BinOp.OF
        elif op == "has":
            return ast_interp.BinOp.HAS
        elif op == "in":
            return ast_interp.BinOp.IN
        elif op == "is":
            return ast_interp.BinOp.IS
        elif op == "and" or op == "&&":
            return ast_interp.BinOp.AND
        elif op == "or" or op == "||":
            return ast_interp.BinOp.OR
        elif (op[0] == "not" or op[0] == "!"):
            if op[1] == "in":
                return ast_interp.BinOp.NOTIN
            elif op[1] == "has":
                return ast_interp.BinOp.NOTHAS
            elif op[1] == "of":
                return ast_interp.BinOp.NOTOF
            elif op[1] == "is":
                return ast_interp.BinOP.NOTIS
        raise InterpException("Unknown binop {}".format(op))

    def get_assignop(self, op):
        op = op.strip()
        if op == "=":
            return ast_interp.AssignOp.NORMAL
        raise InterpException("Unknown assignop {}".format(op))

    def get_unop(self, op):
        op = op.strip()
        if op == "-":
            return ast_interp.UnOp.NEG
        elif op == "+":
            return ast_interp.UnOp.POS
        elif op == "~":
            return ast_interp.UnOp.INV
        elif op == "!" or op == "not":
            return ast_interp.UnOp.NOT
        raise InterpException("Unknown unnop {}".format(op))

    def get_class_type(self, class_type):
        class_type = class_type.strip()
        if class_type == "class":
            return ast_interp.ClassType.CLASS
        elif class_type == "static":
            return ast_interp.ClassType.STATIC
        elif class_type == "trait":
            return ast_interp.ClassType.TRAIT
        raise InterpException("Unknown class type {}".format(class_type))

    def __default__(self, tree):
        raise InterpException("Unimplemented grammar rule {}, tree: {}".format(tree.data, tree))

    def number(self, tree):
        num_type = tree.children[0].type
        num_val = tree.children[0].value
        constructor = ast_interp.IntLiteral
        if num_type == "INT":
            new_value = int(num_val)
        elif num_type == "FLOAT":
            constructor = ast_interp.FloatLiteral
            new_value = float(num_val)
        elif num_type == "HEX":
            new_value = int(num_val, 16)
        elif num_type == "BIN":
            new_value = int(num_val, 2)
        elif num_type == "OCT":
            new_value = int(num_val, 8)
        return constructor(value=new_value)

    def string(self, tree):
        is_r = False
        is_f = False
        string_val = tree.children[0].value
        while string_val[0] != "'" and string_val[0] != '"':
            if string_val[0].lower() == "r":
                is_r = True
            elif string_val[0].lower() == "f":
                is_f = True
            string_val = string_val[1:]
        if tree.children[0].type == "STRING":
            string_val = string_val[1:-1]
        if tree.children[0].type == "ML_STRING":
            string_val = string_val[3:-3]
        if not is_r:
            string_val = codecs.escape_decode(bytes(string_val, "utf-8"))[0].decode("utf-8")

        return ast_interp.StringLiteral(value=string_val)

    def literal(self, tree):
        return self.visit(tree.children[0])

    def parens(self, tree):
        if len(tree.children) == 1:
            return self.visit_or_value(tree.children[0])
        else:
            return self.visit_or_value(tree.children[1])

    def unop(self, tree):
        return ast_interp.UnExpr(operator=self.get_unop(self.visit_or_value(tree.children[0])),
                                 rhs=self.visit(tree.children[1]))

    def binop(self, tree):
        return ast_interp.BinExpr(lhs=self.visit(tree.children[0]),
                                  operator=self.get_binop(self.visit_or_value(tree.children[1])),
                                  rhs=self.visit(tree.children[2]))

    def logicor(self, tree):
        return self.binop(tree)

    def logicand(self, tree):
        return self.binop(tree)

    def logicnot(self, tree):
        return self.unop(tree)

    def relation(self, tree):
        return self.binop(tree)

    def bitor(self, tree):
        return self.binop(tree)

    def bitxor(self, tree):
        return self.binop(tree)

    def bitand(self, tree):
        return self.binop(tree)

    def shift(self, tree):
        return self.binop(tree)

    def sum(self, tree):
        return self.binop(tree)

    def product(self, tree):
        return self.binop(tree)

    def exponent(self, tree):
        return self.binop(tree)

    def atom(self, tree):
        if isinstance(tree.children[0], Tree):
            return self.visit(tree.children[0])
        else:
            return ast_interp.Name(name=self.visit_or_value(tree.children[0]))

    def classdec(self, tree):
        if len(tree.children) > 3:
            raise InterpException("Do of and has correctly")
        return ast_interp.ClassDeclaration(class_type=self.get_class_type(self.visit_or_value(tree.children[0])),
                                           name=self.visit_or_value(tree.children[1]),
                                           block=self.visit(tree.children[2]))

    def slices(self, tree): #TODO: Actually implement slicing
        return [(self.visit(tree.children[0]))]

    def dotaccess(self, tree):
        return ast_interp.Field(field_name=self.visit_or_value(tree.children[1]))

    def arrayaccess(self, tree):
        return ast_interp.Slice(slice=self.visit(tree.children[1]))

    def arraykeydec(self, tree):
        return self.visit_or_value(tree.children[0])

    def arraydecele(self, tree):
        key = None
        if len(tree.children) > 1:
            key = self.visit_or_value(tree.children[0])
        val = self.visit_or_value(tree.children[-1])
        return (key, val)

    def morearraydec(self, tree):
        ret_decs = [self.visit(tree.children[1])]
        if len(tree.children) > 2:
            ret_decs.extend(self.visit(tree.children[2]))
        return ret_decs

    def arraydeclist(self, tree):
        ret_decs = [self.visit(tree.children[0])]
        if len(tree.children) > 1:
            ret_decs.extend(self.visit(tree.children[1]))
        return ret_decs

    def arraydec(self, tree):
        new_arr = []
        is_dict = True
        if len(tree.children) > 2:
            cur_index = 0
            for key, value in self.visit(tree.children[1]):
                if key is None:
                    key = cur_index
                    cur_index += 1
                new_arr.append((key, value))
        return ast_interp.ArrayDeclaration(is_dict=is_dict, items=new_arr)

    def returnstmt(self, tree):
        ret_expression = None
        if len(tree.children) > 1:
            ret_expression = self.visit_or_value(tree.children[1])
        return ast_interp.ReturnStatement(expression=ret_expression)

    def funcdef(self, tree):
        name = self.visit_or_value(tree.children[1])
        args = []
        block = None
        if len(tree.children) > 5:
            args.extend(self.visit_or_value(tree.children[3]))
            block = self.visit(tree.children[5])
        else:
            block = self.visit(tree.children[4])
        return ast_interp.FunctionDeclaration(name=name, arglist=args, block=block)

    def moreargs(self, tree):
        args = [self.visit_or_value(tree.children[1])]
        if len(tree.children) > 2:
            args.extend(self.visit_or_value(tree.children[2]))
        return args

    def arglist(self, tree):
        args = [self.visit(tree.children[0])]
        if len(tree.children) > 1:
            args.add(self.visit(tree.children[1]))
        return args

    def morearguments(self, tree):
        args = [self.visit(tree.children[1])]
        if len(tree.children) > 2:
            args.extend(self.visit(tree.children[2]))
        return args

    def arguments(self, tree):
        args = [self.visit(tree.children[0])]
        if len(tree.children) > 1:
            args.extend(self.visit(tree.children[1]))
        return args

    def call(self, tree):
        args = []
        if len(tree.children) > 2:
            args.extend(self.visit(tree.children[1]))
        return ast_interp.Call(args=args)

    def subprime(self, tree):
        if len(tree.children) == 1:
            return (self.visit(tree.children[0]), None)
        else:
            target, accessor = self.visit(tree.children[0])
            new_accessor = self.visit(tree.children[1])
            if accessor is None:
                accessor = new_accessor
            else:
                accessor.accessor = new_accessor
            return target, accessor

    def primary(self, tree):
        target, accessor = self.visit(tree.children[0])
        return ast_interp.Primary(target=target, accessor=accessor)

    def whilestmt(self, tree):
        return ast_interp.WhileStatement(condition=self.visit(tree.children[1]), block=self.visit(tree.children[2]))

    def ifstmt(self, tree):
        elifs = None
        else_stmt = None
        if len(tree.children) > 3:
            elifs, else_stmt = self.visit(tree.children[3])
            if len(elifs) == 0:
                elifs = None
        return ast_interp.IfStatement(condition=self.visit(tree.children[1]), block=self.visit(tree.children[2]),
                           elifs=elifs, else_stmt = else_stmt)

    def elifstmt(self, tree):
        elifs = []
        else_stmt = None
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        elifs.append(ast_interp.ElifStatement(condition=self.visit(tree.children[1]), block=self.visit(tree.children[2])))
        if len(tree.children) == 4:
            more_elifs, else_stmt = self.visit(tree.children[3])
            elifs.extend(more_elifs)
        return (elifs, else_stmt)

    def elsestmt(self, tree):
        return ([], ast_interp.ElseStatement(block=self.visit(tree.children[1])))

    def assign(self, tree):
        return ast_interp.Assignment(target=self.visit(tree.children[0]),
                          operator=self.get_assignop(self.visit_or_value(tree.children[1])),
                          expression=self.visit(tree.children[2]))

    def stmt_or_block(self, tree):
        if tree.children[0].data == "block":
            return self.visit(tree.children[0])
        else:
            return ast_interp.Block(statements=[self.visit(tree.children[0])])

    def block(self, tree):
        return ast_interp.Block(statements=self.visit(tree.children[1]))

    def emptystmt(self, tree):
        return None

    def statement(self, tree):
        if len(tree.children) > 1:
            raise InterpException("Handle qualifiers")
        else:
            return ast_interp.Statement(expression=self.visit(tree.children[0]))

    def statements(self, tree):
        stmts = []
        for child in tree.children:
            visited_stmt = self.visit(child)
            if visited_stmt is not None and visited_stmt.expression is not None:
                stmts.append(visited_stmt)
        return stmts

    def start(self, tree):
        self.prog = ast_interp.Program(environment=self.env, statements=self.visit(tree.children[0]))
        #pprint.pp(self.prog)
        return self.prog

    def parse(self, string, print_parse=True, run_parse=True):
        parse_res = self.parser.parse(string)
        if print_parse:
            print(parse_res.pretty())
        prog_res = self.visit(parse_res)
        prog_res.run()

parser = Lark.open('foxscream.lark', rel_to=__file__)
prog_text = ""
interp = FoxScreamInterp(parser)
if len(sys.argv) > 1:
    with open(sys.argv[1]) as prog_file:
        prog_text = prog_file.read()
    interp.parse(prog_text)
else:
    interp_face = "<^.^>"
    print("Welcome to foxscream! This language is silly")
    print("Type 'quit' or 'exit' to leave")
    while True:
        try:
            s = input("{} >>> ".format(interp_face))
            if s == "exit" or s == "quit":
                print()
                break
            try:
                interp.parse(s + ";")
                interp_face = "<^.^>"
            except (InterpException, AttributeError, IndexError, KeyError, ArithmeticError, TypeError) as e:
                print(repr(e))
                interp_face = "<^-^;>"
        except EOFError:
            print()
            break
