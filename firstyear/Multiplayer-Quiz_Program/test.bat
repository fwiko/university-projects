@echo off
start "SERVER" python server/main.py
timeout 0
start "CLIENT-1" fin_client/env/Scripts/python fin_client/main.py & timeout 0 & start "CLIENT-2" fin_client/env/Scripts/python fin_client/main.py
