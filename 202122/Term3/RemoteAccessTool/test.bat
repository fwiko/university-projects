@echo off

cd %~dp0/server
start main.py

timeout /t 2

cd %~dp0/client
start main.py
