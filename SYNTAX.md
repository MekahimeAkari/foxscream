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
init: can only be assigned once then acts const (not sure if will keep)
classvar: makes the member be part of the class, rather than the constructed object (ugly?)
noinherit: derived classes will not have this member (also... ugly?)
fixed: derived classes cannot replace this member
private: access from outside the class/object or derived objects is disallowed
terminal: derived classes cannot override nor inherit this member (not sure if useful) but can replace
final: derived classes cannot replace or override this member

```

note: I cannot remember what I meant with the difference between overriding and replacing a member **FIXME**

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
+=: add-assign
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
