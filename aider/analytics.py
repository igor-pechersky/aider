import json
import platform
import sys
import time
import uuid
from pathlib import Path

from mixpanel import Mixpanel

from aider import __version__
from aider.dump import dump  # noqa: F401


class Analytics:
    def __init__(self, track, logfile=None, disable=False):
        self.logfile = logfile
        self.disable = disable
        if not track or disable:
            self.mp = None
            if disable:
                self.mark_as_disabled()
            return

        project_token = "6da9a43058a5d1b9f3353153921fb04d"
        self.mp = Mixpanel(project_token) if project_token else None
        self.user_id = self.get_or_create_uuid()

    def mark_as_disabled(self):
        uuid_file = Path.home() / ".aider" / "caches" / "mixpanel.json"
        uuid_file.parent.mkdir(parents=True, exist_ok=True)

        data = {"uuid": str(uuid.uuid4()), "disabled": True}
        with open(uuid_file, "w") as f:
            json.dump(data, f)

    def get_or_create_uuid(self):
        uuid_file = Path.home() / ".aider" / "caches" / "mixpanel.json"
        uuid_file.parent.mkdir(parents=True, exist_ok=True)

        if uuid_file.exists():
            with open(uuid_file, "r") as f:
                data = json.load(f)
                if "disabled" in data and data["disabled"]:
                    self.disable = True
                    self.mp = None
                return data["uuid"]

        new_uuid = str(uuid.uuid4())
        with open(uuid_file, "w") as f:
            json.dump({"uuid": new_uuid}, f)

        return new_uuid

    def get_system_info(self):
        return {
            "python_version": sys.version.split()[0],
            "os_platform": platform.system(),
            "os_release": platform.release(),
            "machine": platform.machine(),
        }

    def get_or_create_uuid(self):
        uuid_file = Path.home() / ".aider" / "caches" / "mixpanel.json"
        uuid_file.parent.mkdir(parents=True, exist_ok=True)

        if uuid_file.exists():
            with open(uuid_file, "r") as f:
                return json.load(f)["uuid"]

        new_uuid = str(uuid.uuid4())
        with open(uuid_file, "w") as f:
            json.dump({"uuid": new_uuid}, f)

        return new_uuid

    def event(self, event_name, main_model=None, **kwargs):
        if not self.mp and not self.logfile:
            return

        properties = {}

        if main_model:
            if main_model.info:
                properties["main_model"] = main_model.name
            elif "/" in main_model.name:
                properties["main_model"] = main_model.name.split("/")[0] + "/REDACTED"

        properties.update(kwargs)
        properties.update(self.get_system_info())  # Add system info to all events

        # Handle numeric values
        for key, value in properties.items():
            if isinstance(value, (int, float)):
                properties[key] = value
            else:
                properties[key] = str(value)

        properties["aider_version"] = __version__

        if self.mp:
            self.mp.track(self.user_id, event_name, properties)

        if self.logfile:
            log_entry = {
                "event": event_name,
                "properties": properties,
                "user_id": self.user_id,
                "time": int(time.time()),
            }
            with open(self.logfile, "a") as f:
                json.dump(log_entry, f)
                f.write("\n")