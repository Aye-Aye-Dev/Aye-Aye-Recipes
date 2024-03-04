# Ancient woodland

First follow the instructions in the [top level README](../README.md) to setup the virtual environment for this sub-project.

Next, in the directory where you found this README-

```shell
mkdir NaturalEngland
```

Download from https://data.gov.uk/dataset/726484b0-d14e-44a3-9621-29e79fc47bfc/national-nature-reserves-england

Instructions as of 2024-03-04-

- In the "Data links" section follow the link to "NationalNatureReservesEngland_Download"
- In the "Download" panel on the right select...
- ... in the "Area of interest" dropdown select "Full data set"
- ... in "File format" select "GeoJSON"

Similar for https://data.gov.uk/dataset/acdf4a9e-a115-41fb-bbe9-603c819aa7f7/local-nature-reserves-england

- 'LocalNatureReservesEngland_Download' section

And similar for Ancient woodland-
https://www.data.gov.uk/dataset/9461f463-c363-4309-ae77-fdcd7e9df7d3/ancient-woodland-england

- 'AncientWoodlandEngland_Download' section
- Whole dataset is too big to download?!  so draw a polygon for a demo area.
- Call your file ''


Run the models-

```shell
export PYTHONPATH=`pwd`
cd woodland_investigation
python national_nature_ancient_woodland.py
python local_nature_ancient_woodland.py
python python overall_summary.py
```

Disclaimer - the methodology hasn't been thought through so is probably inaccurate. It's a coding demo only!
