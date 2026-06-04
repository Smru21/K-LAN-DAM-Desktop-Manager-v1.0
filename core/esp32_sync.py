"""
SmartBell Manager — ESP32 WiFi Sync
"""

import json
import urllib.request
import urllib.error

DEFAULT_ESP32_IP = "192.168.4.1"
SYNC_TIMEOUT = 10


def sync_sounds_to_esp32(sounds_list, ip=DEFAULT_ESP32_IP):
    url = f"http://{ip}/api/sounds"
    payload = json.dumps({"sounds": sounds_list}).encode("utf-8")

    print(f"[Sync] Sending {len(payload)} bytes to {url}")

    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(payload)),
                "Connection": "close"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=SYNC_TIMEOUT) as response:
            result_text = response.read().decode("utf-8")
            print(f"[Sync] Response: {result_text}")
            result = json.loads(result_text)

            if result.get("success"):
                count = result.get("count", len(sounds_list))
                return True, f"Synced {count} sound names to ESP32"
            else:
                error = result.get("error", "Unknown error")
                return False, f"ESP32 error: {error}"

    except urllib.error.URLError as e:
        print(f"[Sync] URLError: {e}")
        return False, f"Connection failed: {e.reason}"
    except TimeoutError:
        return False, "Connection timed out (10s)"
    except json.JSONDecodeError as e:
        print(f"[Sync] JSON decode error: {e}")
        return False, f"Invalid response from ESP32"
    except Exception as e:
        print(f"[Sync] Exception: {type(e).__name__}: {e}")
        return False, f"Error: {str(e)}"


def sync_school_name_to_esp32(name, ip=DEFAULT_ESP32_IP):
    url = f"http://{ip}/api/schoolname"
    payload = json.dumps({"name": name}).encode("utf-8")

    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(payload)),
                "Connection": "close"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=SYNC_TIMEOUT) as response:
            result = json.loads(response.read().decode("utf-8"))

            if result.get("success"):
                return True, f"School name updated: {result.get('name', name)}"
            else:
                return False, f"ESP32 error: {result.get('error', 'Unknown')}"

    except urllib.error.URLError as e:
        return False, f"Connection failed: {e.reason}"
    except TimeoutError:
        return False, "Connection timed out (10s)"
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_esp32_connection(ip=DEFAULT_ESP32_IP):
    url = f"http://{ip}/api/status"

    try:
        req = urllib.request.Request(
            url,
            headers={"Connection": "close"},
            method="GET"
        )

        with urllib.request.urlopen(req, timeout=SYNC_TIMEOUT) as response:
            result = json.loads(response.read().decode("utf-8"))
            return True, result

    except urllib.error.URLError as e:
        return False, f"Connection failed: {e.reason}"
    except TimeoutError:
        return False, "Connection timed out"
    except Exception as e:
        return False, f"Error: {str(e)}"


def get_esp32_sounds(ip=DEFAULT_ESP32_IP):
    url = f"http://{ip}/api/sounds"

    try:
        req = urllib.request.Request(
            url,
            headers={"Connection": "close"},
            method="GET"
        )

        with urllib.request.urlopen(req, timeout=SYNC_TIMEOUT) as response:
            result = json.loads(response.read().decode("utf-8"))
            return True, result.get("sounds", [])

    except urllib.error.URLError as e:
        return False, f"Connection failed: {e.reason}"
    except TimeoutError:
        return False, "Connection timed out"
    except Exception as e:
        return False, f"Error: {str(e)}"