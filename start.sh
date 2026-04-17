#!/usr/bin/env bash
pip install -r requirements.txt
playwright install
gunicorn app:app