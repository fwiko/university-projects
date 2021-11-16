@echo off
start "SERVER" python server/server.py
start "CLIENT-1" python client/client.py
