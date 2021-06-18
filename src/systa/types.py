from dataclasses import dataclass
from itertools import chain


@dataclass
class Point:
    x: int
    y: int

    def __iter__(self):
        return iter((self.x, self.y))


@dataclass
class Rect:
    origin: Point
    end: Point

    @property
    def width(self) -> int:
        return self.end.x - self.origin.x

    @property
    def height(self) -> int:
        return self.end.y - self.origin.y

    @property
    def left_edge(self) -> int:
        return self.origin.x

    @property
    def right_edge(self) -> int:
        return self.end.x

    @property
    def top_edge(self) -> int:
        return self.origin.y

    @property
    def bottom_edge(self) -> int:
        return self.end.y

    def contains_point(self, point: Point) -> bool:
        return (
            self.origin.x <= point.x <= self.end.x
            and self.origin.y <= point.y <= self.end.y
        )

    def contains_rect(self, rect: "Rect") -> bool:
        return self.contains_point(rect.origin) and self.contains_point(rect.end)

    def above_rect(self, rect: "Rect") -> bool:
        return self.bottom_edge < rect.top_edge

    def below_rect(self, rect: "Rect") -> bool:
        return self.top_edge > rect.bottom_edge

    def left_of_rect(self, rect: "Rect") -> bool:
        return self.right_edge < rect.left_edge

    def right_of_rect(self, rect: "Rect") -> bool:
        return self.left_edge > rect.right_edge

    def intersects_rect(self, rect: "Rect") -> bool:
        return not (
            self.above_rect(rect)
            or self.below_rect(rect)
            or self.left_of_rect(rect)
            or self.right_of_rect(rect)
        )

    def __iter__(self):
        return chain(self.origin, self.end)
