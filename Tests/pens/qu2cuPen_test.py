# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import unittest

from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.recordingPen import RecordingPen
from . import CUBIC_GLYPHS, QUAD_GLYPHS
from .utils import DummyGlyph
from .utils import DummyPen
from textwrap import dedent


MAX_ERR = 1.0


class _TestPenMixin(object):
    """Collection of tests that are shared by both the SegmentPen and the
    PointPen test cases, plus some helper methods.
    Note: We currently don't have a PointPen.
    """

    maxDiff = None

    def diff(self, expected, actual):
        import difflib

        expected = str(self.Glyph(expected)).splitlines(True)
        actual = str(self.Glyph(actual)).splitlines(True)
        diff = difflib.unified_diff(
            expected, actual, fromfile="expected", tofile="actual"
        )
        return "".join(diff)

    def convert_glyph(self, glyph, **kwargs):
        # draw source glyph onto a new glyph using a Cu2Qu pen and return it
        converted = self.Glyph()
        pen = getattr(converted, self.pen_getter_name)()
        cubicpen = self.Qu2CuPen(pen, MAX_ERR, all_cubic=True, **kwargs)
        getattr(glyph, self.draw_method_name)(cubicpen)
        return converted

    def expect_glyph(self, source, expected):
        converted = self.convert_glyph(source)
        self.assertNotEqual(converted, source)
        if not converted.approx(expected):
            print(self.diff(expected, converted))
            self.fail("converted glyph is different from expected")

    def test_convert_simple_glyph(self):
        self.expect_glyph(QUAD_GLYPHS["a"], CUBIC_GLYPHS["a"])
        self.expect_glyph(QUAD_GLYPHS["A"], CUBIC_GLYPHS["A"])

    def test_convert_composite_glyph(self):
        source = CUBIC_GLYPHS["Aacute"]
        converted = self.convert_glyph(source)
        # components don't change after quadratic conversion
        self.assertEqual(converted, source)

    def test_reverse_direction(self):
        for name in ("a", "A", "Eacute"):
            source = QUAD_GLYPHS[name]
            normal_glyph = self.convert_glyph(source)
            reversed_glyph = self.convert_glyph(source, reverse_direction=True)

            # the number of commands is the same, just their order is iverted
            self.assertTrue(len(normal_glyph.outline), len(reversed_glyph.outline))
            self.assertNotEqual(normal_glyph, reversed_glyph)

    def test_stats(self):
        stats = {}
        for name in QUAD_GLYPHS.keys():
            source = QUAD_GLYPHS[name]
            self.convert_glyph(source, stats=stats)

        self.assertTrue(stats)
        self.assertTrue("1" in stats)
        self.assertEqual(type(stats["1"]), int)

    def test_addComponent(self):
        pen = self.Pen()
        cubicpen = self.Qu2CuPen(pen, MAX_ERR)
        cubicpen.addComponent("a", (1, 2, 3, 4, 5.0, 6.0))

        # components are passed through without changes
        self.assertEqual(
            str(pen).splitlines(),
            [
                "pen.addComponent('a', (1, 2, 3, 4, 5.0, 6.0))",
            ],
        )


class TestQu2CuPen(unittest.TestCase, _TestPenMixin):
    def __init__(self, *args, **kwargs):
        super(TestQu2CuPen, self).__init__(*args, **kwargs)
        self.Glyph = DummyGlyph
        self.Pen = DummyPen
        self.Qu2CuPen = Qu2CuPen
        self.pen_getter_name = "getPen"
        self.draw_method_name = "draw"

    def test_qCurveTo_1_point(self):
        pen = DummyPen()
        cubicpen = Qu2CuPen(pen, MAX_ERR)
        cubicpen.moveTo((0, 0))
        cubicpen.qCurveTo((1, 1))
        cubicpen.closePath()

        self.assertEqual(
            str(pen).splitlines(),
            [
                "pen.moveTo((0, 0))",
                "pen.qCurveTo((1, 1))",
                "pen.closePath()",
            ],
        )

    def test_qCurveTo_2_points(self):
        pen = DummyPen()
        cubicpen = Qu2CuPen(pen, MAX_ERR)
        cubicpen.moveTo((0, 0))
        cubicpen.qCurveTo((1, 1), (2, 2))
        cubicpen.closePath()

        self.assertEqual(
            str(pen).splitlines(),
            [
                "pen.moveTo((0, 0))",
                "pen.qCurveTo((1, 1), (2, 2))",
                "pen.closePath()",
            ],
        )

    def test_qCurveTo_3_points_no_conversion(self):
        pen = DummyPen()
        cubicpen = Qu2CuPen(pen, MAX_ERR)
        cubicpen.moveTo((0, 0))
        cubicpen.qCurveTo((0, 3), (1, 3), (1, 0))
        cubicpen.closePath()

        self.assertEqual(
            str(pen).splitlines(),
            [
                "pen.moveTo((0, 0))",
                "pen.qCurveTo((0, 3), (1, 3), (1, 0))",
                "pen.closePath()",
            ],
        )

    def test_curveTo_1_point(self):
        pen = DummyPen()
        cubicpen = Qu2CuPen(pen, MAX_ERR)
        cubicpen.moveTo((0, 0))
        cubicpen.curveTo((1, 1))
        cubicpen.closePath()

        self.assertEqual(
            str(pen).splitlines(),
            [
                "pen.moveTo((0, 0))",
                "pen.curveTo((1, 1))",
                "pen.closePath()",
            ],
        )

    def test_curveTo_2_points(self):
        pen = DummyPen()
        cubicpen = Qu2CuPen(pen, MAX_ERR)
        cubicpen.moveTo((0, 0))
        cubicpen.curveTo((1, 1), (2, 2))
        cubicpen.closePath()

        self.assertEqual(
            str(pen).splitlines(),
            [
                "pen.moveTo((0, 0))",
                "pen.curveTo((1, 1), (2, 2))",
                "pen.closePath()",
            ],
        )

    def test_curveTo_3_points(self):
        pen = DummyPen()
        cubicpen = Qu2CuPen(pen, MAX_ERR)
        cubicpen.moveTo((0, 0))
        cubicpen.curveTo((1, 1), (2, 2), (3, 3))
        cubicpen.closePath()

        self.assertEqual(
            str(pen).splitlines(),
            [
                "pen.moveTo((0, 0))",
                "pen.curveTo((1, 1), (2, 2), (3, 3))",
                "pen.closePath()",
            ],
        )


if __name__ == "__main__":
    unittest.main()
