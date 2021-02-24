from ctrack_bot import app
from config import *

if __name__ == "__main__":
    app.run(port=PORT, host=HOST)