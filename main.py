#!/usr/bin/env python3
"""Microseason — start the server."""

import argparse
import uvicorn
from microseason.server import create_app


def main():
    parser = argparse.ArgumentParser(description="Microseason Calendar Server")
    parser.add_argument("--port", type=int, default=8430)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    args = parser.parse_args()

    app = create_app()
    print(f"\n  Microseason — http://localhost:{args.port}\n")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
