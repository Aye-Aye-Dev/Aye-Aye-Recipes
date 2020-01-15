'''
Created on 14 Jan 2020

@author: si
'''
import ayeaye

DEBUG=True

class Film2Kafka(ayeaye.Model):
    """
    Extract a few fields from an IMDB data file, encode into JSON and send to Kafka.
    """
    imdb_films = ayeaye.Connect(engine_url="tsv://title.basics.tsv")
    output_stream = ayeaye.Connect(engine_url="kafka://localhost/topic=imdb-films",
                                   access=ayeaye.AccessMode.WRITE
                                   )

    def build(self):
        
        self.log("Adding films to Kafka")
        required_fields = ['tconst', 'primaryTitle', 'startYear', 'genres']
        for film in self.imdb_films:

            # Filter out anything that isn't a film
            if film.endYear != r'\N':
                continue

            film_j = film.as_json(select_fields=required_fields)
            self.output_stream.add(film_j)

            # occasionally tell the user how complete the processing is
            msg = f"{self.output_stream.stats.added} films added." 
            self.log_progress(self.imdb_films.progress, msg=msg)

            if DEBUG and self.output_stream.stats.added >= 100000:
                self.log("Debug mode, finishing early.")
                break

        self.log(f"Complete! Added {self.output_stream.stats.added} films.")

if __name__ == '__main__':
    a = Film2Kafka()
    a.go()
