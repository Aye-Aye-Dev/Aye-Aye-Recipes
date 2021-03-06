'''
Created on 16 Jan 2020

@author: si
'''
from collections import defaultdict

import ayeaye

from films_to_kafka import Film2Kafka

DEBUG = True


class FilmGenresSummary(ayeaye.Model):
    """
    Read the extract of IMDB film data from Kafka and count number of films within each genre.
    Output the summary to a JSON document.
    """

    input_stream = Film2Kafka.output_stream.clone(access=ayeaye.AccessMode.READ)
    genre_summary = ayeaye.Connect(engine_url="json://films_summary.json",
                                   access=ayeaye.AccessMode.WRITE
                                   )

    def build(self):

        self.log("Building a summary of films in the Kafka store")
        genre_summary = defaultdict(int)
        films_processed = 0
        for film in self.input_stream:

            # the 'genres field wasn't broken down into a list. Extract that here.
            for genre in film.genres.split(','):

                # little bit of mapping - Null to word
                if genre == r'\N':
                    genre = 'Unknown'

                genre_summary[genre] += 1

            films_processed += 1

            # occasionally tell the user how complete the processing is
            msg = f"{films_processed} films processes."
            self.log_progress(self.input_stream.progress, msg=msg)

        # Output log of the summary ...
        for genre_name, film_count in genre_summary.items():
            self.log(f"{genre_name} : {film_count} films")

        # ... and output the summary as a dataset
        self.genre_summary.data = genre_summary
        self.log(f"Summary written to {self.genre_summary.engine_url}")
        self.log(f"Complete! Processed {films_processed} films.")


if __name__ == '__main__':
    a = FilmGenresSummary()
    a.go()
