# Aye-Aye-Recipes
Examples of using Aye Aye ETL

This is a [monorepo](https://en.wikipedia.org/wiki/Monorepo) of small projects to demonstrate how to use [Aye Aye](https://github.com/Aye-Aye-Dev/AyeAye). Each sub-directory is a self contained project with it's own `Pipfile` so each should be run in a separate python virtual environment.

## Usage

For all recipes create a *recipe venv*. Assuming your current working directory is the directory containing this top level readme, create the virtual environment and install external python packages like this-

```shell
cd <recipe>
pipenv shell
pipenv install --dev
``` 

## Recipes summary

| Recipe | Description |
| --- | --- |
| [IMDB](./imdb/) | Extracts films from IMDB's public data; encodes a small selection of fields into a JSON doc. and stores these in a Kafka topic.|
| [Ancient woodland](./ancient_woodland/) | GIS example using public data from Natural England.|
