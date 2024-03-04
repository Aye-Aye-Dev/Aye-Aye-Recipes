import csv
import json
import os
import shutil
import tempfile
import unittest

import pyproj

from woodland_investigation.national_nature_ancient_woodland import NationalNatureAncientWoodland


class TestAncientWoodland(unittest.TestCase):
    def setUp(self):
        self._working_directory = None

    def tearDown(self):
        if self._working_directory and os.path.isdir(self._working_directory):
            shutil.rmtree(self._working_directory)

    def working_directory(self):
        if self._working_directory is None:
            self._working_directory = tempfile.mkdtemp()

        return self._working_directory

    def create_fake_inputs(self):
        """
        create a nature 64 sq km reserve with a 50% overlap with a 64 sq km ancient woodland.

        This could just be saved to a test/data file but left as method to preserve logic.

        @return: (str, str)
            (fake_nature_reserve_path, fake_ancient_woodland_path)
        """
        wgs84 = pyproj.CRS("EPSG:4326")

        # South west corner of test area on OSGB grid
        sw = (358000, 174000)
        osgb = pyproj.CRS("EPSG:27700")

        # EPSG:32630 is the co-ordinate reference system for 'UTM zone 30N'.
        # It gives better numbers after re-projection than OSGB but doesn't cover all of the
        # area of interest. Leaving it here just in case a swap is needed.
        # utm_30n_origin_x = 519700
        # utm_30n_origin_y = 5695100
        # sw = (utm_30n_origin_x, utm_30n_origin_y)
        # utm30n = pyproj.CRS("EPSG:32630")

        transformer = pyproj.Transformer.from_crs(osgb, wgs84, always_xy=True).transform

        box_side = 100  # meters
        overlap = 50  # meters

        nature_reserve_sw = transformer(sw[0], sw[1])
        nature_reserve_ne = transformer(sw[0] + box_side, sw[1] + box_side)
        # print(sw[0], sw[1], sw[0] + box_side, sw[1] + box_side)

        # note - exterior ring is counter clockwise
        nature_reserve = {
            "type": "FeatureCollection",
            "name": "Fake_National_Nature_Reserves",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": [
                {
                    "type": "Feature",
                    "properties": {"OBJECTID": 1, "NNR_NAME": "Willowton marsh"},
                    "geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [
                                [
                                    [nature_reserve_sw[0], nature_reserve_sw[1]],
                                    [nature_reserve_ne[0], nature_reserve_sw[1]],
                                    [nature_reserve_ne[0], nature_reserve_ne[1]],
                                    [nature_reserve_sw[0], nature_reserve_ne[1]],
                                    [nature_reserve_sw[0], nature_reserve_sw[1]],
                                ]
                            ]
                        ],
                    },
                }
            ],
        }

        fake_nature_reserve_path = os.path.join(
            self.working_directory(), "fake_nature_reserve.geojson"
        )
        with open(fake_nature_reserve_path, "w") as f:
            json.dump(nature_reserve, f)

        ancient_woodland_sw = transformer(sw[0] + overlap, sw[1])
        ancient_woodland_ne = transformer(sw[0] + overlap + box_side, sw[1] + box_side)

        # print(sw[0] + overlap, sw[1], sw[0] + overlap + box_side, sw[1] + box_side)

        ancient_woodland = {
            "type": "FeatureCollection",
            "name": "Fake_Ancient_Woodland",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "OBJECTID": 1,
                        "name": "Long wood",
                        "theme": "ancient woodland",
                        "themname": "Ancient & Semi-Natural Woodland",
                        "THEMID": 1481207.0,
                        "status": "ASNW",
                    },
                    "geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [
                                [
                                    [ancient_woodland_sw[0], ancient_woodland_sw[1]],
                                    [ancient_woodland_ne[0], ancient_woodland_sw[1]],
                                    [ancient_woodland_ne[0], ancient_woodland_ne[1]],
                                    [ancient_woodland_sw[0], ancient_woodland_ne[1]],
                                    [ancient_woodland_sw[0], ancient_woodland_sw[1]],
                                ]
                            ]
                        ],
                    },
                }
            ],
        }
        fake_ancient_woodland_path = os.path.join(
            self.working_directory(), "fake_ancient_woodland.geojson"
        )
        with open(fake_ancient_woodland_path, "w") as f:
            json.dump(ancient_woodland, f)

        return fake_nature_reserve_path, fake_ancient_woodland_path

    def test_overlap(self):
        """Fully build the :class:`NationalNatureAncientWoodland` model with synthetic data and
        check for an expected value.
        """

        m = NationalNatureAncientWoodland()
        m.log_to_stdout = False  # silence the logging for the unit test

        # plug in some synthetic/fake data
        fake_nature_reserve_path, fake_ancient_woodland_path = self.create_fake_inputs()

        m.ancient_woodland = NationalNatureAncientWoodland.ancient_woodland.clone(
            engine_url=f"json://{fake_ancient_woodland_path}"
        )
        m.nature_reserves = NationalNatureAncientWoodland.nature_reserves.clone(
            engine_url=f"json://{fake_nature_reserve_path}"
        )

        # alternative output file
        output_path = os.path.join(self.working_directory(), "inside.csv")
        m.within_nature_reserves = NationalNatureAncientWoodland.within_nature_reserves.clone(
            engine_url=f"csv://{output_path}"
        )

        # run the model
        m.go()

        msg = (
            "The overlap will be box_side x overlap = 5,000 m2 = 0.005 km 2. The re-projections"
            " result in a difference"
        )
        expected_overlap = 0.005
        with open(output_path) as f:
            csv_reader = csv.DictReader(f)
            single_row = next(csv_reader)

        self.assertAlmostEqual(
            expected_overlap, float(single_row["area_in_nature_reserve"]), places=3, msg=msg
        )

        msg = "area of fake ancient woodland is: box_side x box_side -> km sq"
        expected_area = (100 * 100) / (1000 * 1000)
        self.assertAlmostEqual(expected_area, float(single_row["total_area"]), places=3, msg=msg)
