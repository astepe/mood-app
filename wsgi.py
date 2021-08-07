import sys

from mood_app import create_app
import os

if "--dev" in sys.argv:
    from dotenv import load_dotenv

    load_dotenv()
    os.environ["POSTGRES_HOST"] = "0.0.0.0"

app = create_app()

if __name__ == "__main__":

    if "--reload-db" in sys.argv:
        from mood_app.models import Base
        engine = app.session.get_bind()
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    app.run(host="0.0.0.0", debug=True)

