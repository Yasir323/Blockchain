import argparse
from app import app

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", default=8000, type=int)
    args = parser.parse_args()

    # Start the app
    app.run("0.0.0.0", port=args.port)
