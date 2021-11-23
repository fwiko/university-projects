@echo off
start "SERVER" python server/main.py
timeout 0
start "CLIENT-1" python client/main.py
timeout 0
start "CLIENT-2" python client/main.py
