@echo off
cd %~dp0
start "SERVER" python server/main.py & timeout 0 & start python client/main.py & timeout 0 & start python client/main.py
