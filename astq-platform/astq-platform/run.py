"""Local entry point:  python run.py   (dashboard on http://127.0.0.1:5000)"""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # use_reloader=False: the reloader would spawn a second process and re-run recovery logic.
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")),
            debug=os.getenv("FLASK_DEBUG", "0") == "1", use_reloader=False, threaded=True)
