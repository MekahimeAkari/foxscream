#!/usr/bin/env python
from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field

@dataclass(frozen=True, eq=True)
class FieldAddress:
    name: str
    steps: int = 0

def add_fa_unique(ret_dict, fa, value, steps=0):
    if ret_dict is None:
        return None
    new_fa = FieldAddress(fa.name, fa.steps+steps)
    already_in_dict = False
    for existing_fa in ret_dict.keys():
        if existing_fa.name == new_fa.name:
            if existing_fa.steps > new_fa.steps:
                del ret_dict[existing_fa]
            else:
                already_in_dict = True
            break
    if not already_in_dict:
        ret_dict[new_fa] = value
    return ret_dict

@dataclass
class Type:
    name: str | None = None
    parents: dict[FieldAddress, Type] | None = None
    fields: dict[FieldAddress, Type] | None = None
    variants: list[Type] | None = None
    exclusions: list[Type] | None = None
    union: list[Type] | None = None

    def __post_init__(self):
        self.resolve_fields()

    def add_field(self, name, field_type):
        if self.fields is None:
            self.fields = {}
        self.fields[FieldAddress(name, 0)] = field_type
        self.resolve_fields()

    def add_parent(self, parent_type):
        if self.parents is None:
            self.parents = {}
        self.parents[FieldAddress(parent_type.name, 1)] = parent_type
        self.resolve_fields()

    def add_variant(self, variant_type):
        if self.variants is None:
            self.variants = []
        self.variants.append(variant_type)

    def add_union(self, union_type):
        if self.union is None:
            self.union = []
        self.union.append(union_type)

    def get_parents(self, steps=0):
        if self.parents is None:
            return None
        ret_parents = {}
        for parent_addr, parent in self.parents.items():
            ret_parents = add_fa_unique(ret_parents, parent_addr, parent, steps=steps)
            parent_parents = parent.get_parents(steps=steps+1)
            if parent_parents is not None:
                for parent_parent_addr, parent_parent in parent_parents.items():
                    ret_parents = add_fa_unique(ret_parents, parent_parent_addr, parent_parent, steps=steps)
        return ret_parents

    def resolve_parents(self):
        if self.parents is None:
            return
        self.parents = self.get_parents()

    def resolve_fields(self):
        self.resolve_parents()
        if self.parents is None:
            return
        for parent_addr, parent in self.parents.items():
            if parent.fields is None:
                continue
            for parent_field_addr, parent_field in parent.fields.items():
                new_field_addr = FieldAddress(parent_field_addr.name, parent_field_addr.steps + parent_addr.steps)
                if self.fields is None:
                    self.fields = {}
                if new_field_addr not in self.fields:
                    self.fields[new_field_addr] = parent_field

    def type_match(self, other, difference=0):
        has_matched = False
        min_difference = None
        if self == other:
            return (True, difference)
        if self.exclusions is not None:
            for exclusion in self.exclusions:
                matched, _ = exclusion.type_match(other, difference)
                if matched:
                    return (False, None)
        if other.exclusions is not None:
            for exclusion in other.exclusions:
                matched, _ = exclusion.type_match(self, difference)
                if matched:
                    return (False, None)
        if self.union is not None:
            all_matched = True
            total_diff = 0
            for union_type in self.union:
                matched, difference = union_type.type_match(other, difference)
                if matched is False:
                    all_matched = False
                    break
                total_diff = max(difference, total_diff)
                if other.union is not None:
                    for other_union_type in other.union:
                        matched, difference = union_type.match(other_union_type, difference)
                        if matched is False:
                            all_matched = False
                            break
                        total_diff = max(difference, total_diff)
            if all_matched is True:
                has_matched = True
                if min_difference is None:
                    min_difference = total_diff
                min_difference = min(min_difference, total_diff)
        if self.variants is not None:
            for variant_type in self.variants:
                matched, difference = variant_type.type_match(other, difference)
                if matched is True:
                    has_matched = True
                    if min_difference is None:
                        min_difference = difference
                    min_difference = min(min_difference, difference)
                if other.variants is not None:
                    for other_variant in other.variants:
                        matched, difference = variant_type.type_match(other_variant, difference)
                        if matched is True:
                            has_matched = True
                            if min_difference is None:
                                min_difference = difference
                            min_difference = min(min_difference, difference)
        if other.parents is not None:
            for parent_addr, parent in other.parents.items():
                matched, difference = self.type_match(parent, parent_addr.steps)
                if matched:
                    has_matched = True
                    if min_difference is None:
                        min_difference = difference
                    min_difference = min(min_difference, difference)
        if self.fields is not None and other.fields is not None:
            all_matched = True
            total_diff = 0
            for struct_field in other.fields:
                matched, difference = self.fields[struct_field.name].type_match(other.fields[struct_field.name], difference + struct_field.steps)
                if matched is False:
                    all_matched = False
                    break
                total_diff = max(total_diff, difference)
            if all_matched is True:
                has_matched = True
                if min_difference is None:
                    min_difference = difference
                min_difference = min(min_difference, difference)
        return (has_matched, min_difference)

    def get_all_field(self, name):
        self.resolve_fields()
        if self.fields is None or name not in self.fields:
            return None
        ret_dict = {}
        for field_addr, field_val in self.fields:
            if field_addr.name == name:
                ret_dict[field_addr] = field_val
        return ret_dict

    def get_field_with_addr(self, name):
        ret_fields = self.get_all_field(name)
        if ret_fields is None:
            return None
        ret_field = None
        ret_field_addr = None
        min_steps = None
        for field_addr, field_val in ret_fields:
            if min_steps is None:
                min_steps = field_addr.steps
                ret_field = field_val
                ret_field_addr = field_addr
            else:
                if field_addr.steps < min_steps:
                    min_steps = field_addr.steps
                    ret_field = field_val
                    ret_field_addr = field_addr
        return ret_field, ret_field_addr

    def get_field(self, name):
        ret_field, _ = self.get_field_with_addr(name)
        return ret_field

    def assign_field(self, name, new_value):
        changed_field, changed_field_addr = self.get_field_with_addr(name)
        if changed_field is None:
            self.add_field(name, new_value)
        else:
            self.fields[changed_field_addr] = new_value
        return self.get_field(name)

    def remove_field(self, name):
        changed_field, changed_field_addr = self.get_field_with_addr(name)
        if changed_field is None:
            return
        del self.fields[changed_field_addr]
        self.resolve_fields()

@dataclass
class CallSig:
    return_type: Type
    arguments: dict[str, Type] = field(default_factory=dict)
    posargs: list[str] = field(default_factory=list)
    vargs: Type | None = None
    kwargs: (Type, Type) | None = None

    def call_match(self, call):
        total_difference = 0
        matched_args = 0
        match, difference = self.return_type.type_match(call.return_type)
        total_difference += difference
        if match is False:
            return (False, None, None)
        call_vargs = []
        if len(call.posargs) > len(self.posargs):
            call_vargs = call.posargs[len(self.posargs):]
            if self.vargs is None:
                return (False, None, None)
        call_args = {}
        for i in range(0, min(call.posargs, self.posargs)):
            call_args[self.posargs[i]] = call.posargs[i]
        call_kwargs = {}
        for k, v in call.kwargs.items():
            if k not in self.arguments:
                call_kwargs[k] = v
                if self.kwargs is None:
                    return (False, None, None)
                continue
            call_args[k] = v
        matched_posargs = []
        for posarg in self.posargs:
            if posarg not in call_args:
                return (False, None, None)
            match, difference = self.arguments[posarg].type_match(call_args[posarg])
            if match is False:
                return (False, None, None)
            total_difference += difference
            matched_args += 1
            matched_posargs.append(posarg)
        for kwarg in self.kwargs:
            if kwarg in matched_posargs:
                continue
            if kwarg not in call_args:
                continue
            match, difference = self.arguments[kwarg].type_match(call_args[kwarg])
            if match is False:
                return (False, None, None)
            total_difference += difference
            matched_args += 1
        for extra_arg in call_vargs:
            match, difference = self.vargs.type_match(extra_arg)
            if match is False:
                return (False, None, None)
            total_difference += difference
        for extra_k, extra_v in call_kwargs:
            k_match, k_difference = self.kwargs[0].type_match(extra_arg)
            if k_match is False:
                return (False, None, None)
            v_match, v_difference = self.kwargs[1].type_match(extra_arg)
            if v_match is False:
                return (False, None, None)
            total_difference += k_difference + v_difference
        return (True, total_difference, matched_args)

@dataclass
class Object(Type):
    instance_fields: dict[FieldAddress, Type] | None = None
    instance_constructor: Addressable | None = None
    instance_name: str | None = None
    slots: dict[str, Object] | None = None
    constructor: Addressable | None = None
    value: Any | None = None

    def __post_init__(self):
        self.resolve_fields()
        if self.constructor:
            self.contructor.call()
        if self.value is None:
            self.value = self

    def get_value(self):
        return self.value

    def resolve_fields(self):
        super().resolve_fields()
        if self.parents is None:
            return
        for parent_addr, parent in self.parents.items():
            if not hasattr(parent, "instance_fields") or parent.instance_fields is None:
                continue
            for parent_field_addr, parent_field in parent.instance_fields.items():
                new_field_addr = FieldAddress(parent_field_addr.name, parent_field_addr.steps + parent_addr.steps)
                if new_field_addr not in self.instance_fields:
                    self.instance_fields[new_field_addr] = parent_field

    def decend_parents(self):
        ret_parents = {}
        ret_parents[FieldAddress(name=self.name, steps=1)] = self
        if self.parents is not None:
            for parent_address, parent in self.parents.items():
                new_parent_address = FieldAddress(name=self.name, steps=parent_address.steps+1)
                ret_parents[new_parent_address] = parent
        return ret_parents

    def add_instance_field(self, name, field_type):
        if self.instance_fields is None:
            self.instance_fields = {}
        self.instance_fields[FieldAddress(name, 0)] = field_type
        self.resolve_fields()

    def instantiate(self, call):
        if self.instance_constructor is None:
            return None
        new_obj = Object(name=self.instance_name, parents=self.decend_parents(), fields=self.instance_fields)
        inst_func = self.instance_constructor.call(call, new_obj)
        if inst_func is None:
            return None
        new_obj.constructor = inst_func
        return new_obj

    def call(self, name, call, scope=None):
        if scope is None:
            scope = self
        func_fields = self.get_all_field(name)
        if func_fields is None:
            return None
        ret_funcs = []
        max_matched_args = 0
        for func_field_addr, func_field in func_fields:
            ret_func, difference, matched_args = func_field.call(call)
            if ret_func is None:
                continue
            if matched_args > max_matched_args:
                max_matched_args = matched_args
                ret_funcs = []
            if matched_args == max_matched_args:
                ret_funcs.append((func_field_addr.steps, difference, ret_func))
        min_difference = None
        diff_ret_funcs = []
        for steps, difference, ret_func in ret_funcs:
            if min_difference is None or difference < min_difference:
                min_difference = difference
                diff_ret_funcs = []
            if difference == min_difference:
                diff_ret_funcs.append((steps, ret_func))
        min_steps = None
        step_ret_funcs = []
        ret_func = None
        for steps, ret_func in ret_funcs:
            if min_steps is None or steps < min_steps:
                min_steps = steps
                step_ret_funcs = []
            if steps == min_steps:
                step_ret_funcs.append(ret_func)
            ret_func = step_ret_funcs[0]
        if len(step_ret_funcs) > 1:
            print("Somehow, the call for {} resolved to more than one function: {}.".format(name, step_ret_funcs))
        return FunctionCall(func=ret_func, call_args=call, scope=scope)

@dataclass
class Function(Object):
    args: dict = field(default_factory=dict)
    body: Any | None = None
    def call(self, call_args, scope):
        print("Call in {} with {}".format(scope, call_args))

@dataclass
class Call:
    return_type: Type
    kwargs: dict[str, Object] = field(default_factory=dict)
    posargs: list[Object] = field(default_factory=list)

@dataclass
class FunctionCall:
    func: Function
    call_args: Call
    scope: Any | None = None
    def call(self):
        return self.func.call(self.call_args, self.scope)

@dataclass
class Addressable(Type):
    overloads: dict[CallSig, Function] = field(default_factory=dict)
    def call(self, call):
        matched_overloads = []
        max_matched_args = 0
        for overload in self.overloads:
            match, difference, matched_args = overload.call_match(call)
            if match:
                if matched_args > max_matched_args:
                    max_matched_args = matched_args
                    matched_overloads = []
                if matched_args == max_matched_args:
                    matched_overloads.append((difference, self.overloads[overload]))
        ret_overload = None
        min_difference = None
        for matched_overload in matched_overloads:
            if min_difference is None:
                min_difference = matched_overload[0]
                ret_overload = matched_overload[1]
            else:
                if matched_overload[0] < min_difference:
                    min_difference = matched_overload[0]
                    ret_overload = matched_overload[1]
        return (ret_overload, min_difference, max_matched_args)

@dataclass
class Environment:
    types: dict[str, Type] = field(default_factory=dict)
    objs: dict[str, Object] = field(default_factory=dict)
    names: dict[str, Type] = field(default_factory=dict)
    any_type: Type | None = None
    none_type: Type | None = None
    anon_num: int = 0

    def __post_init__(self):
        self.add_type(Type("Any"))
        self.any_type = self.types["Any"]
        self.add_type(Type("None"))
        self.none_type = self.types["None"]
        self.add_type(Type("Value"))
        self.add_type(Type("bool"), self.types["Value"])
        self.add_type(Type("int"), self.types["Value"])
        self.add_type(Type("float"), self.types["Value"])
        self.add_type(Type("str"), self.types["Value"])

    def add_type(self, new_type, *parents):
        new_type_name = new_type.name
        if len(new_type_name) < 1:
            new_type_name = "anontype_{}".format(self.anon_num)
            self.anon_num += 1
        for parent in parents:
            new_type.add_parent(parent)
        if self.any_type is not None:
            if new_type.parents is None or self.any_type not in new_type.parents.values():
                new_type.add_parent(self.any_type)
        self.types[new_type_name] = new_type
        self.add_name(new_type_name, self.types[new_type_name])

    def new_anon_obj(self, obj_type, value=None):
        new_obj_name = "anon_{}_{}".format(obj_type.name, self.anon_num)
        self.anon_num += 1
        self.objs[new_obj_name] = Object(obj_type)
        if value is not None:
            self.objs[new_obj_name].value = value

    def new_obj(self, name, obj_type):
        self.objs[name] = Object(obj_type)
        self.add_name(name, self.objs[name])

    def add_obj(self, new_obj):
        new_obj_name = new_obj.name
        if len(new_obj_name) < 1:
            new_obj_name = "anonobj_{}".format(self.anon_num)
            self.anon_num += 1
        self.objs[new_obj_name] = new_obj
        self.add_name(new_obj_name, self.objs[new_obj_name])

    def add_name(self, name, reference):
        self.names[name] = reference
