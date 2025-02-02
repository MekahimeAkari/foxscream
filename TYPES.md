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


Both fields and contained types effect the overall type (refinement types, woo!) so for a list:
    `list of (any) by (int) where .length: int > 0` is a type

Using refinement type matching in fuctions seems cool, like:
    `fn append(in: list[any as inner_type, int as index_type] as in_array_t where array_length = .length: index_type > 0, appended: inner_type) -> in_array_t where .length: index_type = array_length + 1`
    `fn append(in: list[any as inner_type, int as index_type] where array_length = .length: index_type > 0, appended: any as appended_type) -> list[inner_type + appended_type, index_type] where .length: index_type = array_length + 1`
    `fn append(in: list[any, int as index_type] where .length: index_type == 0, appended: any as new_type) -> list[new_type, index_type] where .length: index_type = 1`
Seems somewhat natural
