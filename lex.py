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
    OPEN_PAREN = auto()
    CLOSE_PAREN = auto()
    OPEN_BRACE = auto()
    CLOSE_BRACE = auto()
    OPEN_SQAURE = auto()
    CLOSE_SQUARE = auto()
    NAME = auto()
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    EQUAL = auto()
    EQUALEQUAL = auto()
    PLUS = auto()
    MINUS = auto()
    TILDE = auto()
    STAR = auto()
    STARSTAR = auto()
    SLASH = auto()
    SLASHSLASH = auto()
    PERCENT = auto()
    LSHIFT = auto()
    RSHIFT = auto()
    AMP = auto()
    AMPAMP = auto()
    AND = auto()
    PIPE = auto()
    PIPEPIPE = auto()
    OR = auto()
    CARET = auto()
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
    FOR = auto()
    FN = auto()
    RETURN = auto()
    BREAK = auto()
    CONTINUE = auto()
    LEAVE = auto()
    CLASS = auto()
    STATIC = auto()
    TRAIT = auto()

    EOF = auto()

@dataclass
class Token:
    ttype: TokenType
    lexeme: str
    col: int
    line: int

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
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "leave": TokenType.LEAVE,
    "class": TokenType.CLASS,
    "static": TokenType.STATIC,
    "trait": TokenType.TRAIT
}

class Lexer:
    def __init__(self):
        self.reset()
        self.cur_token_pos = 0

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

    def lex(self, text):
        self.text = text
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
                if self.match_char("0"):
                    if self.match_char("x") or self.match_char("X"):
                        while self.match(lambda x: x in string.hexdigits or x == "_"):
                            pass
                        pop = True
                    elif self.match_char("o") or self.match_char("O"):
                        while self.match(lambda x: x in list(range(0, 8)) or x == "_"):
                            pass
                        pop = True
                    elif self.match_char("b") or self.match_char("B"):
                        while self.match(lambda x: x in list(range(0, 2)) or x == "_"):
                            pass
                        pop = True
                if not pop:
                    while self.match(lambda x: x in list(range(0, 10)) or x == "_"):
                        pass
                    if self.match_char(".", False) and self.match(lambda x: x in list(range(0, 10)), False):
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

    def next_token(self):
        ret_token = self.peek()
        self.cur_token_pos = min(self.cur_token_pos + 1, len(self.token_list)-1)
        return ret_token

    def peek(self, num=0):
        return self.token_list[self.cur_token_pos+num]

if __name__ == "__main__":
    token_list = []
    source_text = ""
    with open(sys.argv[1]) as source_file:
        source_text = source_file.read()
    lexer = Lexer()
    token_list = lexer.lex(source_text)
    print("\n".join([str(x) for x in token_list]))
