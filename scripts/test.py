#!/usr/bin/env python3
import sys
import uuid
import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib

from pydbus import SessionBus
from gi.repository import GLib

bus = SessionBus()

# Try to connect to the portal
try:
    portal = bus.get(
        "org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop"
    )
except Exception as e:
    print("Error: Could not connect to the desktop portal:", e)
    sys.exit(1)

# Introspect the remote object
xml = portal.Introspect()
print(xml)

# Check for the screencast *implementation* interface
if "org.freedesktop.portal.ScreenCast" not in xml:
    print("Error: Screencast backend not available.")
    print(
        "Install an actual screencast portal like xdg-desktop-portal-wlr or xdg-desktop-portal-hyprland."
    )
    sys.exit(1)

print("Screencast backend is present — proceeding...")

# Generate unique DBus tokens
sess_token = GLib.Variant("i", 42)
select_token = uuid.uuid4().hex

# Create a ScreenCast session
try:
    portal.CreateSession(
        {"handle_token": sess_token, "session_handle_token": sess_token}
    )
except Exception as e:
    print("Error: CreateSession failed:", e)
    sys.exit(1)

print("Session created, requesting source selection...")

# Select sources (opens a picker if the backend works)
try:
    portal.SelectSources({"handle_token": select_token, "types": 2})
except Exception as e:
    print("Error: SelectSources failed:", e)
    sys.exit(1)

print("Waiting for user selection...")

# Wait for the Response signal
selected = None
loop = GLib.MainLoop()


def on_response(request, response, results):
    global selected
    if response != 0:
        print("Selection canceled or denied.")
    else:
        selected = results.get("streams")
    loop.quit()


portal.onResponse = on_response

loop.run()

if not selected:
    print("No window selected.")
    sys.exit(1)

print("Selected streams:", selected)
print("This can now be passed to pipewiresrc.")
