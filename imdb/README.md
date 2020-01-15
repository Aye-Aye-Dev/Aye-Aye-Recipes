# IMDB Aye-Aye-Recipes

Extract films from IMDB's publically available data; encodes a small selection of fields into a JSON doc. and stores these in a Kafka topic.

## Quickstart

IMDB very kindly make a 6M+ record [dataset of films](https://www.imdb.com/interfaces/) available for personal and non-commercial use. This recipe uses the `title.basics.tsv.gz` dataset.

Install the python virtual environment (venv) (see (top level readme)[../README.md].

Download and uncompress the IMDB into the same directory as this readme.

```shell
curl -O "https://datasets.imdbws.com/title.basics.tsv.gz"
gunzip title.basics.tsv.gz
```

You should then have a file called `title.basics.tsv` of roughly 520M in size.

A quick way to get a running instance of Kafka is to follow the [Kafka quickstart](https://kafka.apache.org/quickstart) guide. This also provides a commandline tool that you should use to create the `topic` used in this recipe:

```shell
bin/kafka-topics.sh --create --topic imdb-films --bootstrap-server localhost:9092
```

The recipe assumes Kafka is running on the localhost. Edit the file if this isn't the case. Run the ingest of IMDB films from TSV (Tab Separated Values) to Kafka from within the pipenv virtual environment:

```
python films_to_kafka.py
```
