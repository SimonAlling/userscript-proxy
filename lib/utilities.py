from typing import Optional, Iterable, List, Callable, Any, TypeVar, Tuple

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')


def first(tuple: Tuple[A, B]) -> A:
    (a, b) = tuple
    return a


def second(tuple: Tuple[A, B]) -> B:
    (a, b) = tuple
    return b


def isSomething(x: Optional[A]) -> bool:
    return x is not None


def strs(xs: Any) -> List[str]:
    return list(map(str, xs))


def compose2(f: Callable[[B], C], g: Callable[[A], B]) -> Callable[[A], C]:
    return lambda x: f(g(x))


def fromOptional(value: Optional[A], fallback: A) -> A:
    return value if value is not None else fallback


def itemList(prefix: str, strs: Iterable[str]) -> str:
    return "\n".join(map(lambda s: prefix + s, strs))
