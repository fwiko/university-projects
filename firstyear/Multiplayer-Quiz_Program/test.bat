@echo off
start "SERVER" python server/main.py
timeout 0
start "CLIENT-1" client/env/Scripts/python client/main.py & timeout 0 & start "CLIENT-2" client/env/Scripts/python client/main.py
