# Vercel serverless entry point: serves the FastAPI backend under /api
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from server import app as backend_app

app = FastAPI()
app.mount("/api", backend_app)
