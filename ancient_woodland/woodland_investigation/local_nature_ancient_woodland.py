import ayeaye

from woodland_investigation.national_nature_ancient_woodland import NationalNatureAncientWoodland


class LocalNatureAncientWoodland(NationalNatureAncientWoodland):
    """
    Find intersections between ancient woodland and national nature reserves.
    see README.md alongside this file.
    see https://data.gov.uk/dataset/acdf4a9e-a115-41fb-bbe9-603c819aa7f7/local-nature-reserves-england
    data from https://naturalengland-defra.opendata.arcgis.com/datasets/Defra::local-nature-reserves-england/about
    """

    nature_reserves = ayeaye.Connect(
        engine_url="json://../NaturalEngland/Local_Nature_Reserves_England.json"
    )

    within_nature_reserves = NationalNatureAncientWoodland.within_nature_reserves.clone(
        engine_url="csv://../Ancient_woodland_inside_local_nature_reserves.csv"
    )


if __name__ == "__main__":
    m = LocalNatureAncientWoodland()
    m.go()
