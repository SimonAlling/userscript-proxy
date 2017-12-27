from typing import List, Callable, Any, TypeVar, Tuple

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')


def not_(x: bool) -> bool:
	return not x


def first(tuple: Tuple[A, B]) -> A:
    (a, b) = tuple
    return a


def second(tuple: Tuple[A, B]) -> B:
    (a, b) = tuple
    return b


def isSomething(x: Any) -> bool:
    return x != None


def strs(xs: Any) -> List[str]:
	return list(map(str, xs))


def compose2(f: Callable[[B], C], g: Callable[[A], B]) -> Callable[[A], C]:
    return lambda x: f(g(x))


def beginsWith(prefix: str) -> Callable[[str], bool]:
	return lambda s: s.startswith(prefix)
