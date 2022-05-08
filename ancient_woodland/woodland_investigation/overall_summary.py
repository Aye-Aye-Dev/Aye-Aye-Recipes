import itertools

import ayeaye

from woodland_investigation.local_nature_ancient_woodland import LocalNatureAncientWoodland
from woodland_investigation.national_nature_ancient_woodland import NationalNatureAncientWoodland


class OverallSummary(ayeaye.Model):
    """Calculate the percentage of England's ancient woodland that is within a nature reserve."""

    within_local = LocalNatureAncientWoodland.within_nature_reserves.clone(
        access=ayeaye.AccessMode.READ,
        expected_fields=LocalNatureAncientWoodland.within_nature_reserves.field_names,
        field_names=None,
    )
    within_national = NationalNatureAncientWoodland.within_nature_reserves.clone(
        access=ayeaye.AccessMode.READ,
        expected_fields=NationalNatureAncientWoodland.within_nature_reserves.field_names,
        field_names=None,
    )

    summary = ayeaye.Connect(
        engine_url="json:///Users/si/Documents/Scratch/NaturalEngland/summary.json;indent=4",
        access=ayeaye.AccessMode.WRITE,
    )

    def build(self):

        # each ancient woodland area should have it's `total_area` in both self.within_local and
        # self.within_national but to make the join slightly safer use a set of IDs and only
        # count the area once. This way an ancient woodland could exist in either or both and would
        # correctly contribute to the overall summary.
        # A remaining assumption is that local and national datasets don't spatially overlap.
        already_seen = set()
        area_total = 0.0
        area_within = 0.0

        for woodland in itertools.chain(self.within_local, self.within_national):

            if woodland.OBJECTID not in already_seen:
                already_seen.add(woodland.OBJECTID)
                area_total += float(woodland.total_area)

            area_within += float(woodland.area_in_nature_reserve)

        # note the area_total is double the actually area of woodland

        self.summary.data = {
            "area_total": area_total,
            "area_within": area_within,
            "ancient_woodland_within_nature_reserves": area_within / area_total,
        }

        self.log("All done!")


if __name__ == "__main__":
    m = OverallSummary()
    m.go()
