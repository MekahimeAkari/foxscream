# foxscream

## Intro

Foxscream is a language mostly for hacking/scripting language inspired by [Python](https://www.python.org/)
but with syntax closer to [Swift](https://www.swift.org/) with a inspiration from
[Zig](https://ziglang.org/) and [Rust](https://www.rust-lang.org/). The intention is to produce an easy
to use, easy to read language that can replace Python for hacking out small programs. It is not intended
to be fast, but one of the goals is a cannonical compiled form.

A description of the syntax can be found at [SYNTAX.md](SYNTAX.md). When finished, an discussion of the
type system will be in [TYPES.md](TYPES.md).

Foxscream scripts use ".ff" as the extension as ".fs" is used by [F#](https://fsharp.org/) and I
have no desire to compete! "ff" stands for "Fuwa Fuwa" which is "fluffy" in Japanese (like my tail!).

## Example

There are examples in the [ex/](ex/) directory (also used at the moment for testing the language
implementation) but a simple example of a foxscream script:

```text
# comment

fn func(a, b)
{
    while a > b
    {
        print(a)
        a = a - 1
    }
}

fn func2(a)
{
    for i in [a] print(a) # will just print a but illustrates for loop
}

fn func3(a, b)
{
    do
    {
        print(b) # prints the value of b, then continues until b == a
        b = b - 1
    } while b > a
}

a = 3
b = 1
if a > b
{
    func(a, b) # prints "3", "2"
}
elif a == b
{
    func2(a) # prints a if a == b
}
else
{
    func3(a, b)
}
```

More information can be found in [SYNTAX.md](SYNTAX.md).

## Usage

Use `interp.py` to try out the language. If you run it without any arguments, you'll get the REPL.
Otherwise, you can write a script and provide it as the first argument (try out `ex/ex8.ff` as an
example!)

## Example status
- [ ] [ex1](ex/ex1.ff) (from an older rewrite)
- [x] [ex2](ex/ex2.ff)
- [x] [ex3](ex/ex3.ff)
- [ ] [ex4](ex/ex4.ff) (waiting on defer, match, and to)
- [x] [ex5](ex/ex5.ff)
- [x] [ex6](ex/ex6.ff)
- [x] [ex7](ex/ex7.ff)
- [x] [ex8](ex/ex8.ff)
- [ ] Actually good examples

## Progress

### Basic language structure

- [x] comments
- [x] basic arithmetic
- [x] basic comparisons
- [x] assignment
- [x] if expressions
- [x] while loops
- [x] for loops
- [x] functions
- [x] basic classes
- [x] basic inheritance
- [x] return
- [x] break
- [ ] continue
- [ ] defer
- [ ] leave
- [ ] control expressions to labels
- [ ] closures
- [ ] functions or classes returned/assigned
- [ ] match expressions
- [ ] elfor/elwhile (works with if/else)
- [ ] exceptions/error handling syntax
- [ ] tuples
- [ ] import
- [ ] namespaces
- [ ] using
- [ ] augmented assignment
- [ ] array operators
- [ ] operator overloading
- [ ] string formatting
- [ ] regex syntax
- [ ] grammar syntax
- [ ] complex numbers?
- [ ] vectors/matrices?
- [ ] typing system
    - [ ] type syntax
- [ ] user input
- [ ] ffi
    - [ ] C ffi
    - [ ] C++ ffi
    - [ ] Python ffi
    - [ ] others?
- [ ] shell interaction
- [ ] multiline comments?
- [ ] docstrings/help?

### Standard library
- [ ] A standard library
    - [ ] Actually write down what needs to be in the standard library

### Interpreter
- [ ] [Python implementation](interp.py)
    - [x] REPL
    - [x] Run scripts
    - [ ] package correctly
    - [ ] help
    - [ ] import system
    - [ ] ffi
    - [ ] bytecode
    - [ ] compliation?
    - [ ] comment better
- [ ] C implementation
- [ ] remove old/
