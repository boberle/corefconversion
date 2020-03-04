"""
This module defines a ColorManager.
"""

# 2020 Bruno Oberle, MPL 2.0, see the LICENSE file.

__version__ = '1.1.0'


class ColorManager:
    """Generate colors based on HSL.

    The hue is the main iterator, so that colors are significantly different from
    each others.

    Example:
    --------

        >>> cm = ColorManager(50, 20, 20)
        >>> for i in range(5):
        ...     color = cm.get_next_color()
        ...     print(color)
        hsl(0, 100%, 80%)
        hsl(50, 100%, 80%)
        hsl(100, 100%, 80%)
        hsl(150, 100%, 80%)
        hsl(200, 100%, 80%)

    Class Attributes
    ----------------
    gray: str
        The gray color.

    Attributes
    ----------
    hue_step: `int` (default: 25)
        Hue step.
    saturation_step: `int` (default: 25)
        Saturation step.
    lightness_step: `int` (default: 10)
        Lightness step.
    gray: `str` (default `rgb(125, 125, 125)`)
        Value returned when there is no more color available, and `repeat` is
        `False`.
    repeat: bool (default: `True`)
        When no more available color, repeat.

    Note
    ----
    Use `len(cm)` to get the number of available colors.
    """

    gray = "rgb(125, 125, 125)"

    def __init__(self, hue_step=25, saturation_step=25, lightness_step=10,
            repeat=True):
        self.hue_step = hue_step
        self.saturation_step = saturation_step
        self.lightness_step = lightness_step
        self.gray = "rgb(125, 125, 125)"
        self.reset_iterator()
        self.repeat = repeat

    def __len__(self):
        """Return the number of available colors."""
        hue = 360 // self.hue_step + 1
        saturation = 100 // self.saturation_step
        lightness = 70 // self.lightness_step # because ]10;80]
        return hue * saturation * lightness

    def reset_iterator(self):
        """Reset the iterator."""
        self._iter = self.iter_color()

    def get_next_color(self):
        """Return the next color."""
        return next(self._iter)

    def iter_color(self):
        """Generator that goes through all the colors.

        It is use as the iterator.
        
        When there is no more color, yield the `gray` instance attribute.
        Never raises StopIteration.
        """
        while True:
            for s in range(100, -1, -self.saturation_step):
                for l in range(80, 9, -self.lightness_step):
                    for h in range (0, 361, self.hue_step):
                        yield "hsl(%d, %d%%, %d%%)" % (h, s, l)
            if not self.repeat:
                while True:
                    yield self.gray



class CommonColorManager:
    """Generate colors based on named html colors.
    """

    gray = "gray"

    colors = [
        "red",
        "maroon",
        "yellow",
        "olive",
        "lime",
        "green",
        "aqua",
        "teal",
        "blue",
        "navy",
        "fuchsia",
        "purple",
    ]

    def __init__(self, remove_yellow=True, repeat=True):
        self.repeat = True
        self.colors = self.__class__.colors.copy()
        if remove_yellow:
            self.colors.remove("yellow")
        self.reset_iterator()

    def __len__(self):
        """Return the number of available colors."""
        return len(self.colors)

    def reset_iterator(self):
        """Reset the iterator."""
        self._iter = self.iter_color()

    def get_next_color(self):
        """Return the next color."""
        return next(self._iter)

    def iter_color(self):
        """Generator that goes through all the colors."""
        while True:
            for color in self.colors:
                yield color
            if not self.repeat:
                while True:
                    yield self.__class__.gray


