from server.main import app
import server.main
import sys
import os
sys.path.insert(0, os.getcwd())


print(f"App location: {server.main.__file__}")
print("--- Registered Routes ---")

for route in app.routes:
    if hasattr(route, "path"):
        print(f"Path: {route.path}, Name: {route.name}")
    elif hasattr(route, "routes"):
        for sub_route in route.routes:
            print(f"Sub-Path: {sub_route.path}, Name: {sub_route.name}")
