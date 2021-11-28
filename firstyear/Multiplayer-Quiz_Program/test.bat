@echo off
start "SERVER" python %~dp0/server/main.py
timeout 0
start "CLIENT-1" %~dp0/client/env/Scripts/python %~dp0/client/main.py & timeout 0 & start "CLIENT-2" %~dp0/client/env/Scripts/python %~dp0/client/main.py
