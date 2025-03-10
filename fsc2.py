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

parser = Lark.open('foxscream2.lark', rel_to=__file__)
print(parser.parse("cheese = \"sjd\\\"k;s\n'd'j\"\n + 2\na;").pretty())
print(parser.parse("cheese = if a 2 elif 2 2 else if b 3 else 6\n").pretty())
print(parser.parse("cheese = if a {2;3;} else {a; return a+2;}\n").pretty())
print(parser.parse("cheese = label cheezos: for i in z {a = a + 1; defer return a;}\n").pretty())
print(parser.parse("cheese: [int] = fn (a, b): [int] {return a + b}\n").pretty())
print(parser.parse("ns cheese; nee = ns {cheese = fn (a, b): [int] {return a + b}}\n").pretty())
print(parser.parse("a: class[cheese] = static class cheese: fries, chicken {private noinherit fn superchiken() { super.class.hello()}}\n").pretty())
print(parser.parse("a, b, c = fries() \n ").pretty())
