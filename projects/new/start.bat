@echo off
start "SERVER" python server/main.py
timeout 0
start python client/main.py