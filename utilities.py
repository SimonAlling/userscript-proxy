from typing import Any, TypeVar, Tuple

A = TypeVar('A')
B = TypeVar('B')

def first(tuple: Tuple[A, B]) -> A:
    (a, b) = tuple
    return a


def second(tuple: Tuple[A, B]) -> B:
    (a, b) = tuple
    return b


def isSomething(x: Any) -> bool:
    return x != None
