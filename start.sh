#!/bin/bash
uvicorn app:api --host 0.0.0.0 --port $PORT & python3 app.py
