NOTE: all just thinking right now

Types are split primary into two - realisable and non-realisable
Realisable: All types (Any) including the empty type (nil, null, none?)
Non-realisable: A type that can never be referenced - unbound name (unbound, undefined, etc?)
Realisable (Any), again two main groups:
    Some: anything (!None)
    None/Null/Nil: empty (singleton)

Some, split into two main groups (again):
    Composite: Contains some other type
    Primitive: Contains no other types

Primitive:
    Must just be of one immutable type. `int32, uint32, fp32, fp64,` etc
    is `nil` primitive?

Composite:
    Basically everything else. `int: contains int32 or int64`

Types can also be boolean expressions of other types. `num = int | float, some = !nil`

Container types:
    Types which explictily contain another type. See:
        int of (int32 | int64)
        class of (some)
        indexable types are a subset, see
        `list of (any) by (int)`
        `dict of (any) by (any)`
    Value types are simple(plex?) containers, see: `some of any`

Types can also have fields:
    `list where .length: int`


Both fields and contained types effect the overall type (dependent typing, woo!) so for a list:
    `list of (any) by (int) where .length: int > 0` is a type
    Probably need to restrict what can effect dependent typing, or it will get silly

The boolean restriction of a type is itself a type, but the concrete type of the object matched is likely different. See:
    `list of (any) by (int) where .length: int > 0` matches `[2, 3, 4]` which has concrete type `list of (int of int32) by (int) where .length: int of int32 == 3 and .empty: bool == false` or something like that
