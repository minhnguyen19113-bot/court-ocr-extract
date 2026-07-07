from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import TypeVar


T = TypeVar("T")


def track(items: Iterable[T], description: str, *, total: int | None = None) -> Iterator[T]:
    """Progress wrapper that never needs to expose source filenames."""
    try:
        from tqdm import tqdm

        yield from tqdm(items, total=total, desc=description, unit="item")
    except Exception:
        for item in items:
            yield item
