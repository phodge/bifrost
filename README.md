# Bifrost RPC

Bifrost RPC allows you to build inter-service APIs where the endpoints are everyday typed
functions, and the generated client-side libraries expose functions with identical signatures.

# Example

If you have a python service with some useful function such as this:

    def get_movies() -> List[Movie]:
        """Get a list of movies."""
        return [
            Movie.from_dict(movie)
            for movie in db.query('SELECT * FROM movies')
        ]

    def get_actors(movie_id: int) -> Union[List[Actor], Literal["movie_not_found"]]:
        """Get actors associated with a movie."""
        if not any([m.movie_id == movie_id for m in get_movies()]):
            return "movie_not_found"
        return [
            Actor.from_dict(actor)
            for actor in db.query('SELECT * FROM actors WHERE ...')
        ]

Then you can turn it into a Bifrost RPC service like this:

    app = BifrostRPC()
    app.addType(Actor)
    app.addType(Movie)
    app.addMethod(get_movies)
    app.addMethod(get_actors)
    app.run(port=8000)

And have this client code generated for you:

    // TypeScript
    class MovieService {
        public get_movies() -> Movie[] {
            /* ... */
        }

        public get_actors(movie_id: number) -> Actor[] | "movie_not_found" {
            /* ... */
        }
    }

    // PHP
    class MovieService {
        /**
         * Get a list of movies.
         *
         * @return Movie[]
         */
        public function get_movies() {
            /* ... */
        }

        /**
         * Get a list of movies.
         *
         * @param int $movie_id
         *
         * @return Movie[] | string
         */
        public get_actors(int $movie_id) {
            /* ... */
        }


# Development

To run unit tests using docker:

    # run tests using python3.9
    $ docker build --build-arg SOURCE_IMAGE=python:3.9 -f tests/Dockerfile .
