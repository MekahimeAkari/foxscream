# Foxscream syntax

This is very much **TODO** but better to list everything out here and start documenting how the language should actually look than just writing EBNF and hoping for the best.

## Introduction

Foxscream is a classic curly brace, semicolon terminated language. Statements can also be terminated by newlines, allowing a slightly cleaner syntax at the expense of slightly higher parsing complexity. Foxscream is not whitespace sensitive *except* for the newline at the end of a statement.
Foxscream is also intended to be almost entirely expression-driven, so even things like loops and if statements can be used as an expression component, allowing a flexible grammar.

## Statments

### Assignment

Foxscream doesn't require any keywords on assignment, so something like:

`a = 3`

Is perfectly acceptable (and normal). By default, assignments represent binding a mutable variable.

#### Assignment qualifiers

Assignments may also accept qualifiers - these go before the variable name, and change the access or inheritability of a variable. An example is:

`const a = 3`

The current list of qualifiers (multiple may be used per assignment) are:

```text
const: constant binding, interior mutability may still be allowed

classvar: makes the member be part of the class, rather than the constructed object (ugly?)

noinherit: derived classes will not have this member (also... ugly?)

fixed: derived classes cannot replace this member
       effectively, fixes the type of this name binding

private: access from outside the class/object or derived objects is disallowed

final: derived classes cannot replace or override this member
       no further overloading can occur, nor can this name be used for anything other than the type specified
```

#### Type specifiers

Assigments also accept type specifiers with a colon after the variable name, like:

`a: int = 3`

The type system will be explained in [TYPES.md](TYPES.md) (also very **TODO**)

#### Assignment operators

The current assignment operators are:

```text
=: normal
:=: force-assign, bypasses overloading of the assignment operator (**TODO**: does this make sense?)
$=: copy-assign? not sure on this one for syntax **TODO**
+=: add-as sign
-=: sub-assign
/=: div-assign
//=: int-div-assign
%=: mod-assign
&=: bit-and-assign
|=: bit-or-assign
^=: xor-assign
**=: power-assign
<<=: left-shift-assign
>>=: right-shift-assign
probably more **TODO**
```

### blocks

being a curly-brace language, the classic compound statement is the braced block:

```text
{
    some
    statements
    here; maybe more
}

```

blocks can be labeled:

```text

```

### if statements

if statements are pretty straightforward:

```text
if <expression>
{
    <statements...>
}
```

else if statements use "elif":

```text
elif <expression>
{
    <statements...>
}
```

and else is just else:

```text
else
{
    <statements...>
}
```
Note that no parathesis are required after the keyword

Single line if/elif/else is also allowed with no braces:
```text
if <expression> <statement> elif <expression> <statement> else <statement>```
```

As if statments are expressions, they can also be use ind assignments:

```text
a = if b > 3
{
    c = d()
    c += f
    c
}
else
{
    2
}

# or

a = if b > 3 d() + f else 2
```

### while statements

while statements are also simple:

```text
while a < 2
{
    a = z()
}
```

**TODO**: do while?

as expressions, they can also be used in assignments:


**FIXME**: wait wut?

```text
c = 0
a = while c < 10
{
    c =+ 2
    c
}
```

### for loops

for loops take from bash/python:

```text
for i in a
{
    print(i)
}
```

for are expressions so they can also... **FIXME** I dunno what this should syntactically look lile

### functions

Functions are declared with "fn":

```text
fn henlo(b)
{
    print(b)
}
```

functions can take positional, default, and splat/doublesplat like python **BIG TODO**:

```text
fn henlo2(b, c, d=2, f=3, *moreargs, **dictargs)
{
    return "wat"
}
```

functions can also be anonymous:

```text
a = fn (b, c) { return b + c }
```

**TODO**: fix syntax for single statement within inline { }

and functions are expressions, so they can be used whereever an expression can be used (and have closures):

```text
fn func_retter(a)
{
    return fn (b) 
    {
        return b + a
    }
}
