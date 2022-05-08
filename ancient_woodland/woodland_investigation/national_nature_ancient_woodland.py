import ayeaye
import pyproj
from shapely.geometry import box, shape
from shapely.ops import transform


class NationalNatureAncientWoodland(ayeaye.Model):
    """
    Find intersections between ancient woodland and national nature reserves.
    """

    ancient_woodland = ayeaye.Connect(
        engine_url="json:///Users/si/Documents/Scratch/NaturalEngland/Ancient_Woodland_(England).geojson"
    )

    nature_reserves = ayeaye.Connect(
        engine_url="json:///Users/si/Documents/Scratch/NaturalEngland/National_Nature_Reserves_(England).geojson"
    )

    within_nature_reserves = ayeaye.Connect(
        engine_url="csv:///Users/si/Documents/Scratch/NaturalEngland/Ancient_woodland_inside_nature_reserves.csv",
        access=ayeaye.AccessMode.WRITE,
        field_names=["OBJECTID", "name", "area_in_nature_reserves"],
    )

    def build(self):

        self.log("Loading map co-ordinate transformer")
        # co-ordinate system for the most familiar 'latitude/longitude' co-ordinate system
        wgs84 = pyproj.CRS("EPSG:4326")

        # EPSG:27700 is the co-ordinate reference for 'OSGB 1936' - British National Grid
        # see https://epsg.io/27700
        # It's a 'square' grid with 1 meter cells. It's being used below as a simple way to
        # find the area in square kilometres for a polygon built with WGS84 (i.e. lat/lng)
        # co-ordinates
        osgb = pyproj.CRS("EPSG:27700")
        re_project_coord = pyproj.Transformer.from_crs(wgs84, osgb, always_xy=True).transform

        self.log("Loading ancient woodland")
        woodland = []
        woodland_types = set()
        for row_number, ancient_woodland in enumerate(self.ancient_woodland.data.features):

            properties = ancient_woodland.properties
            woodland_types.add((properties.THEME, properties.THEMNAME, properties.STATUS))

            if properties.STATUS == "PAWS":
                # PAWS = 'Ancient Replanted Woodland', see 'THEMNAME' field
                # This is a commercial plantation in the site of ancient woodland. This doesn't
                # count as ancient woodland!
                continue

            geom = shape(ancient_woodland.geometry)
            woodland_extract = ayeaye.Pinnate(
                {
                    "OBJECTID": properties.OBJECTID,
                    "name": properties.NAME,
                    "geom": geom,
                    "bounding": box(*geom.bounds),
                    "area_in_nature_reserves": 0.0,  # square kilometres are added below
                }
            )
            if woodland_extract.name.strip() == "":
                woodland_extract.name = "Unknown"

            woodland.append(woodland_extract)

        woodland_count = len(woodland)
        self.log(f"{woodland_count} ancient woodland areas found")

        self.log("Loading nature reserves")
        nature_reserves_count = len(self.nature_reserves.data.features)
        self.log(f"Found {nature_reserves_count} nature reserves")

        for row_number, nature_reserve in enumerate(self.nature_reserves.data.features):

            nature_reserve_geom = shape(nature_reserve.geometry)
            nature_reserve_bounding = box(*nature_reserve_geom.bounds)

            assert nature_reserve.type == "Feature", "Feature is the only known type in these data"

            # this progress percent doesn't include the time to load ancient woodland so isn't
            # totally accurate but is good enough
            self.log_progress(row_number / nature_reserves_count)

            # other than a bounding box check there is no consideration of efficiency. For example,
            # use of a spatial index.
            for ancient_woodland in woodland:

                if not ancient_woodland.bounding.intersects(nature_reserve_bounding):
                    continue

                overlap = ancient_woodland.geom.intersection(nature_reserve_geom)
                if overlap.area > 0:
                    # the output must be in square kilometres. One way to do this is
                    # to use the OSGB map projection. See note above.
                    as_osgb = transform(re_project_coord, overlap)
                    ancient_woodland.area_in_nature_reserves += as_osgb.area / (1000 * 1000)

        self.log("Writing output")
        for ancient_woodland in woodland:
            record_subset = {k: ancient_woodland[k] for k in self.within_nature_reserves.field_names}
            self.within_nature_reserves.add(record_subset)

        self.log(f"All done!")


if __name__ == "__main__":
    m = NationalNatureAncientWoodland()
    m.go()
