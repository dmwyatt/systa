import math
from dataclasses import dataclass
from itertools import chain
from typing import Tuple


@dataclass
class Point:
    """Represents an X, Y coordinate."""

    x: int
    y: int

    def __iter__(self):
        """You can iterate across a ``Point``.

        This allows you to to unpack a point into a function call that takes an x and a
        y.
        """
        return iter((self.x, self.y))


@dataclass
class Rect:
    origin: Point
    end: Point

    @staticmethod
    def from_coords(
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ) -> "Rect":
        """Create an instance with the provided dimensions.

        >>> from systa.types import Rect
        >>> Rect.from_coords(0, 0, 10, 10)
        Rect(origin=Point(x=0, y=0), end=Point(x=10, y=10))

        :param x1: Top left x value.
        :param y1: Top left y value.
        :param x2: Bottom right x value.
        :param y2: Bottom right y value.
        """
        return Rect(Point(x1, y1), Point(x2, y2))

    @property
    def upper_rect(self) -> "Rect":
        """
        Get a ``Rect`` encompassing the top half of this instance.

        >>> from systa.types import Point, Rect
        >>> Rect(origin=Point(0, 0), end=Point(10, 10)).upper_rect
        Rect(origin=Point(x=0, y=0), end=Point(x=10, y=5))
        """
        return Rect(
            origin=self.origin,
            end=Point(x=self.right_edge, y=self.top_edge + self.half_height[0]),
        )

    @property
    def lower_rect(self) -> "Rect":
        """
         Get a ``Rect`` encompassing the bottom half of this instance.

        >>> from systa.types import Point, Rect
        >>> Rect(origin=Point(0, 0), end=Point(10, 10)).lower_rect
        Rect(origin=Point(x=0, y=6), end=Point(x=10, y=10))
        """

        return Rect(
            origin=Point(x=self.left_edge, y=self.top_edge + self.half_height[1]),
            end=self.end,
        )

    @property
    def left_rect(self) -> "Rect":
        """
        Get a ``Rect`` encompassing the left half of this instance.

        >>> from systa.types import Point, Rect
        >>> Rect(origin=Point(0, 0), end=Point(10, 10)).left_rect
        Rect(origin=Point(x=0, y=0), end=Point(x=5, y=10))
        """
        return Rect(
            origin=self.origin,
            end=Point(x=self.half_width[0], y=self.bottom_edge),
        )

    @property
    def right_rect(self) -> "Rect":
        """
         Get a ``Rect`` encompassing the right half of this instance.

        >>> from systa.types import Point, Rect
        >>> Rect(origin=Point(0, 0), end=Point(10, 10)).right_rect
        Rect(origin=Point(x=6, y=0), end=Point(x=10, y=10))
        """
        return Rect(origin=Point(x=self.half_width[1], y=self.top_edge), end=self.end)

    @property
    def half_width(self) -> Tuple[int, int]:
        """
        Get tuple splitting width in have.

        Returns a two-tuple such that each element represents a coordinate on
        left/right off vertical center line. Handles even and odd widths.

        .. seealso:: :meth:`split_value`
        """
        return self.split_value(self.width)

    @property
    def half_height(self) -> Tuple[int, int]:
        """
        Get tuple splitting width in have.

        Returns a two-tuple such that each element represents a coordinate on
        top/bottom off horizontal center line. Handles even and odd widths.

        .. seealso:: :meth:`split_value`
        """
        return self.split_value(self.height)

    @classmethod
    def split_value(cls, val: int) -> Tuple[int, int]:
        """
        Splits a value into two, returning a tuple of (floor, ceil).

        The goal is that the values do not overlap so that, for example, when you
        split the number 10, you get ``(5, 6)`` not ``(5, 5)``

        >>> Rect.split_value(10)
        (5, 6)
        >>> Rect.split_value(11)
        (5, 6)

        :param val:
        :return:
        """
        half = val / 2
        if val % 2 == 0:
            return int(half), int(half + 1)
        else:
            return math.floor(half), math.ceil(half)

    @property
    def width(self) -> int:
        """Width of rectangle."""
        return self.end.x - self.origin.x

    @property
    def height(self) -> int:
        """Height of rectangle."""
        return self.end.y - self.origin.y

    @property
    def left_edge(self) -> int:
        """Left edge of rectangle."""
        return self.origin.x

    @property
    def right_edge(self) -> int:
        """Right edge of rectangle."""
        return self.end.x

    @property
    def top_edge(self) -> int:
        """Top edge of rectangle."""
        return self.origin.y

    @property
    def bottom_edge(self) -> int:
        """Bottom edge of rectangle."""
        return self.end.y

    @property
    def area(self) -> int:
        """Area of rectangle."""
        return self.width * self.height

    def contains_point(self, point: Point) -> bool:
        """Does the rectangle contain the provided ``Point``?

        A ``Point`` on the edge of a rectangle is considered contained in that
        rectangle.

        >>> from systa.types import Point, Rect
        >>> r = Rect.from_coords(0, 0, 10, 10)
        >>> r.contains_point(Point(0, 1))
        True
        >>> r.contains_point(Point(20, 11))
        False
        """
        return (
            self.origin.x <= point.x <= self.end.x
            and self.origin.y <= point.y <= self.end.y
        )

    def contains_rect(self, rect: "Rect") -> bool:
        """Does the rectangle contain the provided ``Rect``?

        The provided ``Rect`` has to be completely within this rectangle to be
        considered contained.

        A ``Rect`` with an edge *on* the edge of this rectangle is considered
        contained in that rectangle.

        >>> from systa.types import Point, Rect
        >>> r = Rect.from_coords(0, 0, 10, 10)
        >>> r.contains_rect(Rect.from_coords(0, 0, 5, 5))
        True
        >>> r.contains_rect(Rect.from_coords(0, 0, 11, 10))
        False

        :param rect: The rectangle you want to compare to.
        """
        return self.contains_point(rect.origin) and self.contains_point(rect.end)

    def above_rect(self, rect: "Rect") -> bool:
        """Is the provided rectangle above this ``Rect``?

        The edges cannot overlap.

        :param rect: The rectangle you want to compare to.
        """
        return self.bottom_edge < rect.top_edge

    def below_rect(self, rect: "Rect") -> bool:
        """Is the provided rectangle below this ``Rect``?

        The edges cannot overlap.

        :param rect: The rectangle you want to compare to.
        """
        return self.top_edge > rect.bottom_edge

    def left_of_rect(self, rect: "Rect") -> bool:
        """Is the provided rectangle to the left of this ``Rect``?

        The edges cannot overlap.

        :param rect: The rectangle you want to compare to.
        """
        return self.right_edge < rect.left_edge

    def right_of_rect(self, rect: "Rect") -> bool:
        """Is the provided rectangle to the right of this ``Rect``?

        The edges cannot overlap.

        :param rect: The rectangle you want to compare to.
        """
        return self.left_edge > rect.right_edge

    def intersects_rect(self, rect: "Rect") -> bool:
        """Does the provided rectangle intersect our rectangle in any way?

        :param rect: The rectangle you want to compare to.
        """
        return not (
            self.above_rect(rect)
            or self.below_rect(rect)
            or self.left_of_rect(rect)
            or self.right_of_rect(rect)
        )

    def intersection_rect(self, rect: "Rect") -> "Rect":
        """
        Representing the area of overlap between the provided rect and this retangle.

        Second rectangle overlaps from bottom right:

        >>> rect_a = Rect(Point(0, 0), Point(10, 10))
        >>> rect_b = Rect(Point(1, 1), Point(11, 11))
        >>> rect_a.intersection_rect(rect_b)
        Rect(origin=Point(x=1, y=1), end=Point(x=10, y=10))

        First rectangle complete contains second rectangle:

        >>> rect_b = Rect(Point(2, 2), Point(5, 5))
        >>> rect_a.intersection_rect(rect_b) == rect_b
        True

        Second rectangle overlaps from top left.

        >>> rect_b = Rect(Point(-1, -1), Point(5, 5))
        >>> rect_a.intersection_rect(rect_b)
        Rect(origin=Point(x=0, y=0), end=Point(x=5, y=5))

        Second rectangle same as first rectangle.

        >>> rect_b = Rect(Point(0, 0), Point(10, 10))
        >>> rect_a.intersection_rect(rect_b) == rect_a == rect_b
        True

        :param rect: Get intersection with this rect.
        """
        if not self.intersects_rect(rect):
            zero = Point(0, 0)
            return Rect(zero, zero)
        left_edge = max((self.left_edge, rect.left_edge))
        right_edge = min((self.right_edge, rect.right_edge))
        top_edge = max((self.top_edge, rect.top_edge))
        bottom_edge = min((self.bottom_edge, rect.bottom_edge))
        return Rect(
            origin=Point(left_edge, top_edge), end=Point(right_edge, bottom_edge)
        )

    def number_pixels_overlapped_by(self, rect: "Rect") -> int:
        """
        Pixels of overlap between this rect and the other rect.

        >>> rect_a = Rect(Point(0, 0), Point(10, 10))
        >>> rect_b = Rect(Point(1, 1), Point(11, 11))
        >>> rect_a.number_pixels_overlapped_by(rect_b)
        81

        :param rect: Rect you want to compare this rect to.
        """
        if not self.intersects_rect(rect):
            return 0
        return (
            max((self.left_edge, rect.left_edge))
            - min((self.right_edge, rect.right_edge))
        ) * (
            max((self.top_edge, rect.top_edge))
            - min((self.bottom_edge, rect.bottom_edge))
        )

    def __iter__(self):
        """You can iterate across a ``Rect``.

        This allows you to to unpack a point into a function call that takes an x1,
        y1, x2, y2.
        """
        return chain(self.origin, self.end)
