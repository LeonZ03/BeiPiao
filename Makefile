.PHONY: init start local check

# Optional shortcuts for Windows; double-click launch does not require make.
init:
	powershell.exe -NoProfile -ExecutionPolicy Bypass -File local-access/init-room.ps1

start:
	powershell.exe -NoProfile -ExecutionPolicy Bypass -File local-access/start-room.ps1

local:
	powershell.exe -NoProfile -ExecutionPolicy Bypass -File local-access/start-room.ps1 -SkipTunnel

check:
	powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/check.ps1
