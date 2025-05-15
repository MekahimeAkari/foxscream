# Foxscream Syntax

## TODO

- Implement a lot
- match syntax
- exceptions?
- import
- namespaces
- using
- augmented assignment
- array ops?
- operator overloading
- string formatting
- regex syntax
- grammar syntax
- typing syntax

## Basic syntax

Foxscream is a curly-brace, semi-whitespace sensitive language. The overall syntax is a mix
of largely C and Python, with influence from lots of other stuff.
It is semi-whitespace sensitive in that a newline can end an expression. Otherwise, a
semicolon can be used.

```text
a = 2
a = 2;
```

These are both valid. A semicolon is required if more than one full expression is on the same
line, like so:

```text
a = 2; b = 1

```

Expressions may be concatinated with commas into a tuple expression, like so:

```text
a = 2, b = 1
```

The difference is that the previous example itself evaluates to `1`, as `b = 1` is the last
expression, whereas the second evaluates to `(2, 1)`.

## Aggregate types

### Tuples NOT IMPLEMENTED

Tuples are largely based on Python:

```text
a = (2, 3)
```

They share immutability in terms of member count and type but each value may be mutated:

```text
a = (2, 3)
a[1] = 4
```

Is legal.

### Lists/Dictionaries

Lists and Dictionaries are similar to their Python counterparts, use largely the same
syntax. However, since curly braces are used for blocks, dictionaries now use square brackets.
The determination of whether something is a list or a dictionary is down to whether colons are
used to express keys.

```text
list = [1, 2, 3]
dict = [0:1, 1:2, 2:3]
```

## Expressions

All "statements" in Foxscream are expressions, and thus evaluate to some value.

## block

Foxscream is a standard braces language, so the block is the classic compound expression:

```text
{
    a = 1
    b = 2
}

```

Blocks are expressions themselves, so they can used in assignment and access:

```text
a = {
    b = 1
    b + 2
}
```
Assigns `a = 3`

```
a = {
    b = [1, 2]
    b
}[0]
```
Assigns `a = 1`

## control expressions

Foxscream is a little different in that `if`, `for`, and `while` all have analogous control
words and can be used together. `if` has `elif`, `for` has `elfor`, and `while` has `elwhile`.
These can all be used in a single control block and will flow in order based on on
whether the guarded expression if ever run - so a single time for `if`, or at least one
time for `for` and `while`. They can all be used interchangably, and all can have a
terminating `else` if no expressions are run.

## if

`if` expressions are straightforward:

```text
if a == 2 a + 2
```

And can use blocks:

```text
if a == 2
{
    a + 2
}
```

`if` can also be assigned:

```text
b = 2
a = if b == 2 3
c = if b == 1 2
```

Here, `a = 3`, and `c` is `unbound`.

## elif

`elif` is the else if:

```text
b = 2
a = if b == 1 3 elif b == 2 4
c = if a == 3
{
    1
}
elif a == 4
{
    2
}
```

Here, `a = 4` and `c = 2`.

It can also be used with `for` and `while` interchangably with `elfor` and `elwhile`:

```text
fn test(a)
{
    while a > 0
    {
        a = a - 1
        print(a)
    }
    elif a < 0
    {
        print("negative")
    }
    else
    {
        print("a == 0")
    }
}

test(2) # prints "1", "0"
test(-1) # prints "negative"
test(0) # prints "a == 0"
```

## else

`else` is a normal else for `if`, `while`, `for`, and `elif`, `elwhile`, and `elfor`.

```text
b = 1
a = if b == 2 3 else 2
c = if a == 3
{
    1
}
else
{
    a
}
```

Here, `a = 2` and `c = 2`.

## while

`while` is a standard loop, evaluating the second expression while the first is true.

```text
a = 0
while a != 2 a += 1
```

`while` can be used in assignment as well:

```text
b = 0
a = while b < 2 { b += 3; b; }
```

Here, `a` gets assigned to 3 as `b` is the last expression in the while loop.

## elwhile

`elwhile` is `while`'s `elif` counterpart. It is run if the previous `if`, `while`, `for`,
or `elif`, `elwhile`, `elfor` is false or not run:

```text
fn test(a)
{
    if a == 2
    {
        print(":)")
    }
    elwhile a > 2
    {
        a = a - 1
        print(a)
    }
    elwhile a < 2
    {
        a = a + 1
        print(a)
    }
}
test(2) # prints ":)"
test(4) # prints "3", "2"
test(0) # prints "1", "2"
```

## do-while

`do-while` is the classic C-style compare-after loop.

```text
a = 0
do a += 1 while a < 4
```

`do-while` can also be used in assignment, which makes it easy for linear searches:

```text
a = [
    "henlo",
    "goodbyeh",
    "mornin",
    "nighto"
]
i = 0
b = do { a[i]; i += 1; } while a[i][0] != "m"
```

This will assign the first string starting with `"m"` to `a`.

## for

`for` is modelled on python/shell, with `for VAR in ITERABLE`:

```text
for i in 1...3 print(i)
```

This prints `1`, `2`, and `3`.

`for` can be used in assignment as well:

```text
b = [
    "cheese",
    "fries",
    "apples",
    "chicken
]
a = for i in 1..4 { if b[i][0] == "a" break b[i]; "not found"; }
```

Here, were iterate from `1` to `3` over `b`, looking for a string with the first letter `a`.
If we find one (`i == 3`, `"apple"`) we break and the value is that string. Otherwise, the
last expression will be `"not found"`.

## elfor

`elfor` is the `elif` or `elwhile` equivalent for `for`, used if the previous `if`, `while`, `for`,
or `elif`, `elwhile`, `elfor` is false or not run:

```text
fn test(a, b)
{
    if a > 2
    {
        print("big")
    }
    elfor i in b
    {
        print(i)
    }
    else
    {
        print("nah")
    }
}

test(5, []) # prints "big"
test(2, [1, 2]) # prints "1", "2"
test(2, []) # prints "nah"
```

## of

`of` is a type-checking statement, to be used similarly to Python's `isinstance` but less ugly.

```text
a = 1
if a of int # true
{
    print(a)
}
```

## has NOT IMPLEMENTED

`has` is for structural typing - to check if something is within a object.

```text
class a
{
    a
    b
}
z = a()

if z has c # false
{
    print("has c")
}
elif z has a # true
{
    print("has a")
}
```

## return

`return` is pretty much what you expect - returns from the most closely enclosing function

ex:
```text
a = 2
return a
```

## defer

`defer` evaluates the expression on leaving the current block. Similarly to Zig,
`defer` expressions are done in reverse order of declaration.

ex:
```text
a = 1
{
    defer a = 2
    defer a = 3
}
```
On block exit, first `a = 3` will be evaluated, then `a = 2`.

Since blocks are expressions in Foxscream, defer can be used to specify the variable used as
the value of a block when it exits:

```
a = {
    b = 1
    defer b
    c = 2
    c
}
```
`a` here will be assigned to `1`.

## break

`break` is again what you expect - exits from the most closely enclosing loop.
`break` can optionally be used with an expression, which is evaluated at the time of exit.
If a loop contains no `defer` expressions, this then is effectively the loop's "`return`".

ex:
```text
a = while true {
    b = 2
    break b
    c = 2
}
```

`a` will be assigned to `2` here, `c = 2` won't be evaluated.

`break` can be used with `to` to break to a specific block:

```text
a = while true lbl: {
    b = 2
    while true {
        while true lbl2: {
            while true {
                c = 2
                break to lbl2
                z = 1
            }
        }
        a + 1
        break b to lbl
        z = c
    }
}
```

Here, `a` will be assigned to `2`. First, `b = 2` is evaluated, then `c = 2`, then a `break` to
the end of the block with `lbl2` (skipping z = 1), then `a + 1`, the break to the block labeled
`lbl` (skipping z = c) with the expression `b` being evaluated.

`defer` will override `break` as it is executed at exit, rather then the last expression in the
block.

```
a = while true {
    b = 2
    c = 3
    defer b
    break c
}
```

Here, `a` will be assigned to `2`, even though `break c` is used.

## leave

`leave` is a superset of `break`, used to escape blocks. With no arguments, `leave` jumps to
expression just after the closest enclosing block. `leave` implies `break` within a loop.
`leave` can be used like `break` with an expression, which is evalutated at time of exit.
If a block contains no `defer` expressions, this then is effectively the 's "`return`".

ex:
```text
a = {
    b = 2
    leave b
    c = 2
}
```

`a` will be assigned to `2` here, `c = 2` won't be evaluated.

`leave` can be used with `to` to break to a specific block:

```text
a = lbl: {
    b = 2
    {
        lbl2: {
            {
                c = 2
                leave to lbl2
                z = 1
            }
        }
        a + 1
        leave b to lbl
        z = c
    }
}
```

Here, `a` will be assigned to `2`. First, `b = 2` is evaluated, then `c = 2`, then a `break` to
the end of the block with `lbl2` (skipping z = 1), then `a + 1`, the break to the block labeled
`lbl` (skipping z = c) with the expression `b` being evaluated.

`defer` will override `leave` as it is executed at exit, rather then the last expression in the
block.

```
a = {
    b = 2
    c = 3
    defer b
    leave c
}
```

Here, `a` will be assigned to `2`, even though `leave c` is used.

## Functions

Functions are declared with the keywork `fn`. They can optionally be given a name, otherwise
the anonymous function can be assigned to a variable and used just like a lambda.

```text
fn cheese(a) print(a)
a = fn (a) print(a)
cheese("hi") # prints "hi"
a("hi") # prints "hi"
```

These are two equivalent ways to declare a function.

Functions can, of course, return functions:

```text
a = fn (c) return fn (b) return c + b
b = a(1)
print(b(2))
```

This will print `3`.

## Classes

classes are declared with one of `class`, `static`, or `trait`.
A `class` is a standard C++/Java/Python style class. If a function is declared with the name
of the class, it is considered to be the constructor:

```text
class a
{
    a
    b
    fn a() { a = 1; b = 2; }
}

print(a().b) # prints 2
```

`static` classes are like Java (NOT IMPLEMENTED) - the class definition itself is a single object. The constructor
in this case is called once the class comes into scope:

```text
static a
{
    a
    b
    fn init() { a = 1; b = 2; }
}
# a() called here
# a() - illegal
print(a.b) # prints 2
```

`trait` is taken from Rust (NOT IMPLEMENTED) - `trait` classes cannot be instantiated (thus have no need for a
constructor) but hold some code that may be shared between otherwise non-related classes:

```text
trait a
{
    a = 2
}

# a() - illegal
# a.a - illegal

class b of a
{
    fn init() { print(a); }
}

class c of a
{
    fn init() { print(a+1); }
}
b() # prints 2
c() # prints 3
```

