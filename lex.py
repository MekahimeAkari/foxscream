#!/usr/bin/env python3

import sys
from enum import Enum, auto
from dataclasses import dataclass
import string

class TokenType(Enum):
    NEWLINE = auto()
    SEMICOLON = auto()
    COLON = auto()
    DOT = auto()
    COMMA = auto()
    UNDERSCORE = auto()
    OPEN_PAREN = auto()
    CLOSE_PAREN = auto()
    OPEN_BRACE = auto()
    CLOSE_BRACE = auto()
    OPEN_SQUARE = auto()
    CLOSE_SQUARE = auto()
    NAME = auto()
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    EQUAL = auto()
    EQUALEQUAL = auto()
    PLUS = auto()
    PLUSEQUAL = auto()
    MINUS = auto()
    MINUSEQUAL = auto()
    TILDE = auto()
    TILDEEQUAL = auto()
    STAR = auto()
    STAREQUAL = auto()
    STARSTAR = auto()
    STARSTAREQUAL = auto()
    SLASH = auto()
    SLASHEQUAL = auto()
    SLASHSLASH = auto()
    SLASHSLASHEQUAL = auto()
    PERCENT = auto()
    PERCENTEQUAL = auto()
    LSHIFT = auto()
    LSHIFTEQUAL = auto()
    RSHIFT = auto()
    RSHIFTEQUAL = auto()
    AMP = auto()
    AMPEQUAL = auto()
    AMPAMP = auto()
    AND = auto()
    PIPE = auto()
    PIPEEQUAL = auto()
    PIPEPIPE = auto()
    OR = auto()
    CARET = auto()
    CARETEQUAL = auto()
    BANG = auto()
    BANGEQUAL = auto()
    GT = auto()
    LT = auto()
    GE = auto()
    LE = auto()
    IN = auto()
    HAS = auto()
    OF = auto()
    IS = auto()
    NOT = auto()
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    WHILE = auto()
    DO = auto()
    FOR = auto()
    MATCH = auto()
    FN = auto()
    RETURN = auto()
    BREAK = auto()
    CONTINUE = auto()
    LEAVE = auto()
    DEFER = auto()
    YIELD = auto()
    TO = auto()
    CLASS = auto()
    STATIC = auto()
    TRAIT = auto()
    CLASSVAR = auto()
    FIXED = auto()
    PRIVATE = auto()
    NOINHERIT = auto()
    FINAL = auto()
    TERMINAL = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()

    EOF = auto()

@dataclass
class Token:
    ttype: TokenType
    lexeme: str
    col: int
    line: int

    def is_op(self, *ttypes):
        for ttype in ttypes:
            if self.ttype == ttype:
                return True
        return False

    def is_primary(self):
        return self.is_op(TokenType.NAME, TokenType.INT, TokenType.FLOAT, TokenType.STRING, TokenType.TRUE, TokenType.FALSE, TokenType.NULL)

    def is_end(self):
        return self.is_op(TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.EOF)

    def is_class(self):
        return self.is_op(TokenType.CLASS, TokenType.STATIC, TokenType.TRAIT)

    def is_assign(self):
        return self.is_op(TokenType.EQUAL)

    def is_unop(self):
        return self.is_op(TokenType.NOT)

    def is_singlekw(self):
        return self.is_op(TokenType.RETURN, TokenType.BREAK, TokenType.CONTINUE, TokenType.LEAVE)

    def is_compop(self):
        return self.is_op(TokenType.GT, TokenType.LT, TokenType.GE, TokenType.LE, TokenType.EQUALEQUAL)

    def is_sumop(self):
        return self.is_op(TokenType.PLUS, TokenType.MINUS)

    def is_termop(self):
        return self.is_op(TokenType.STAR, TokenType.SLASH, TokenType.SLASHSLASH)

    def is_factorop(self):
        return self.is_op(TokenType.MINUS, TokenType.TILDE, TokenType.PLUS)


RESERVED_WORDS = {
    "and": TokenType.AND,
    "or": TokenType.OR,
    "in": TokenType.IN,
    "has": TokenType.HAS,
    "of": TokenType.OF,
    "is": TokenType.IS,
    "not": TokenType.NOT,
    "if": TokenType.IF,
    "elif": TokenType.ELIF,
    "else": TokenType.ELSE,
    "do": TokenType.DO,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "match": TokenType.MATCH,
    "fn": TokenType.FN,
    "to": TokenType.TO,
    "return": TokenType.RETURN,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "leave": TokenType.LEAVE,
    "defer": TokenType.DEFER,
    "yield": TokenType.YIELD,
    "class": TokenType.CLASS,
    "static": TokenType.STATIC,
    "trait": TokenType.TRAIT,
    "classvar": TokenType.CLASSVAR,
    "fixed": TokenType.FIXED,
    "private": TokenType.PRIVATE,
    "noinherit": TokenType.NOINHERIT,
    "final": TokenType.FINAL,
    "terminal": TokenType.TERMINAL,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
    "_": TokenType.UNDERSCORE
}

class Lexer:
    def __init__(self, source):
        self.reset()
        self.cur_token_pos = 0
        self.text = source
        self.backtrack_stack = []

    def reset(self):
        self.start = 0
        self.start_col = 1
        self.start_line = 1
        self.cur = 0
        self.col = 1
        self.line = 1
        self.text = ""
        self.token_list = []

    def new_lexeme(self):
        self.start = self.cur
        self.start_col = self.col
        self.start_line = self.line

    def get_lexeme(self):
        return self.text[self.start:self.cur]

    def add_token(self, token_type):
        self.token_list.append(Token(token_type, self.get_lexeme(), self.start_col, self.start_line))
        self.new_lexeme()

    def advance(self, length=1):
        for i in range(length):
            ret_c = self.text[self.cur]
            self.col += 1
            if ret_c == '\n':
                self.col = 1
                self.line += 1
            self.cur += 1
        return ret_c

    def match(self, match_func, eat=True):
        if self.cur + 1 >= len(self.text):
            return False
        elif match_func(self.text[self.cur]) is False:
            return False
        if eat:
            self.cur += 1
        return True

    def match_char(self, char, eat=True):
        for in_char in str(char):
            if not self.match(lambda x: x == in_char, False):
                return False
        if eat:
            self.advance(len(str(char)))
        return True

    def cur_input(self, advance=0):
        return self.text[self.cur+advance]

    def end_of_source(self):
        return self.cur >= len(self.text) - 1

    def lex(self):
        while self.cur < len(self.text):
            char = self.advance()
            if char in [' ', '\t']:
                self.new_lexeme()
            elif char == '#':
                while self.match(lambda x: x != '\n'):
                    pass
                self.new_lexeme()
            elif char == "\n":
                self.add_token(TokenType.NEWLINE)
            elif char == ";":
                self.add_token(TokenType.SEMICOLON)
            elif char == ":":
                self.add_token(TokenType.COLON)
            elif char == ".":
                self.add_token(TokenType.DOT)
            elif char == ",":
                self.add_token(TokenType.COMMA)
            elif char == "(":
                self.add_token(TokenType.OPEN_PAREN)
            elif char == ")":
                self.add_token(TokenType.CLOSE_PAREN)
            elif char == "{":
                self.add_token(TokenType.OPEN_BRACE)
            elif char == "}":
                self.add_token(TokenType.CLOSE_BRACE)
            elif char == "[":
                self.add_token(TokenType.OPEN_SQUARE)
            elif char == "]":
                self.add_token(TokenType.CLOSE_SQUARE)
            elif char == "+":
                self.add_token(TokenType.PLUS)
            elif char == "-":
                self.add_token(TokenType.MINUS)
            elif char == "~":
                self.add_token(TokenType.TILDE)
            elif char == "%":
                self.add_token(TokenType.PERCENT)
            elif char == "^":
                self.add_token(TokenType.CARET)
            elif char == "=":
                if self.match_char("="):
                    self.add_token(TokenType.EQUALEQUAL)
                else:
                    self.add_token(TokenType.EQUAL)
            elif char == "*":
                if self.match_char("*"):
                    self.add_token(TokenType.STARSTAR)
                else:
                    self.add_token(TokenType.STAR)
            elif char == "/":
                if self.match_char("/"):
                    self.add_token(TokenType.SLASHSLASH)
                else:
                    self.add_token(TokenType.SLASH)
            elif char == "&":
                if self.match_char("&"):
                    self.add_token(TokenType.AMPAMP)
                else:
                    self.add_token(TokenType.AMP)
            elif char == "!":
                if self.match_char("="):
                    self.add_token(TokenType.BANGEQUAL)
                else:
                    self.add_token(TokenType.EQUAL)
            elif char == "|":
                if self.match_char("|"):
                    self.add_token(TokenType.PIPEPIPE)
                else:
                    self.add_token(TokenType.PIPE)
            elif char == "<":
                if self.match_char("="):
                    self.add_token(TokenType.LE)
                elif self.match_char("<"):
                    self.add_token(TokenType.LSHIFT)
                else:
                    self.add_token(TokenType.LT)
            elif char == ">":
                if self.match_char("="):
                    self.add_token(TokenType.GE)
                elif self.match_char(">"):
                    self.add_token(TokenType.RSHIFT)
                else:
                    self.add_token(TokenType.GT)
            elif char.isdigit():
                pop = False
                ttype = TokenType.INT
                if char == "0":
                    if self.match_char("x") or self.match_char("X"):
                        while self.match(lambda x: x in string.hexdigits or x == "_"):
                            pass
                        pop = True
                    elif self.match_char("o") or self.match_char("O"):
                        while self.match(lambda x: x in [str(x) for x in list(range(0, 8))] or x == "_"):
                            pass
                        pop = True
                    elif self.match_char("b") or self.match_char("B"):
                        while self.match(lambda x: x in [str(x) for x in list(range(0, 2))] or x == "_"):
                            pass
                        pop = True
                if not pop:
                    while self.match(lambda x: x in list(range(0, 10)) or x == "_"):
                        pass
                    if not self.end_of_source() and self.cur_input() == ".":
                        if self.cur_input(1).isdigit():
                            self.advance()
                            self.advance()
                            while self.match(lambda x: x in list(range(0, 10)) or x == "_"):
                                pass
                            ttype = TokenType.FLOAT
                self.add_token(ttype)
            elif char == "'" or char == '"':
                start_quote = char
                self.advance()
                while self.match(lambda x: x != start_quote) or self.match_char("\\" + start_quote):
                    pass
                self.advance()
                self.add_token(TokenType.STRING)
            elif char in string.ascii_letters or char in ["_"]:
                ttype = TokenType.NAME
                while self.match(lambda x: x in string.ascii_letters or x in string.digits or x in ["_"]):
                    pass
                if self.get_lexeme() in RESERVED_WORDS:
                    ttype = RESERVED_WORDS[self.get_lexeme()]
                self.add_token(ttype)
            else:
                raise Exception("Unhandled char " + char)
        self.new_lexeme()
        self.add_token(TokenType.EOF)
        self.cur_token_pos = 0
        return self.token_list

    def next_token(self, num=1):
        ret_token = self.peek(num-1)
        self.cur_token_pos = min(self.cur_token_pos + num, len(self.token_list) - 1)
        return ret_token

    def peek(self, num=0):
        return self.token_list[min(self.cur_token_pos + num, len(self.token_list) - 1)]

    def print_current(self):
        print("<{}>, {}".format(self.peek(), [str(self.token_list[x]) for x in range(self.cur_token_pos+1, len(self.token_list))]))

    def token_check(self, *ttypes):
        for ttype in ttypes:
            if self.peek().ttype == ttype:
                return True
        return False

    def mark_backtrack(self):
        self.backtrack_stack.append(self.cur_token_pos)

    def backtrack(self):
        self.cur_token_pos = self.backtrack_stack.pop()

if __name__ == "__main__":
    token_list = []
    source_text = ""
    with open(sys.argv[1]) as source_file:
        source_text = source_file.read()
    lexer = Lexer(source_text)
    token_list = lexer.lex()
    print("\n".join([str(x) for x in token_list]))
