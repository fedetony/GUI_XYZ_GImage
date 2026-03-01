import re
from dataclasses import dataclass, field
import yaml
import time
from datetime import datetime

@dataclass
class Rule:
    name: str
    regex: re.Pattern
    groups: list[str] = field(default_factory=list)
    priority: int = 0
    flags: list[str] = field(default_factory=list)

    def match(self, msg: str):
        return self.regex.search(msg)

    def extract(self, match):
        data = {}
        for i, key in enumerate(self.groups):
            data[key] = match.group(i + 1)
        return data

class DeviceParser:
    def __init__(self, yaml_path, pattern_dict:dict=None):
        self.rules = []
        self.rules_by_priority = {}
        self.expected = None
        self.state = {}
        if yaml_path:
            self.load_yaml(yaml_path)
        if pattern_dict:
            self.load_pattern_dict(pattern_dict)

    # -----------------------------
    # Pattern dictionary
    # -----------------------------
    def load_pattern_dict(self, cfg):
        for name, entry in cfg.get("patterns", {}).items():
            rule = Rule(
                name=name,
                regex=re.compile(entry["regex"]),
                groups=entry.get("groups", []),
                priority=entry.get("priority", 0),
                flags=entry.get("flags", []),
            )
            self.rules.append(rule)

            self.rules_by_priority.setdefault(rule.priority, []).append(rule)

        self.timeouts = cfg.get("timeouts", {
            "default_response_ms": 300,
            "command_timeout_ms": 1000
        })

        self.commands = cfg.get("commands", {})

    # -----------------------------
    # YAML loading
    # -----------------------------
    def load_yaml(self, path):
        with open(path, "r") as f:
            cfg = yaml.safe_load(f)
        self.load_pattern_dict(cfg)

    # -----------------------------
    # Command sending
    # -----------------------------
    def expect_response(self, cmd_name):
        cmd = self.commands[cmd_name]
        self.expected = {
            "name": cmd_name,
            "regex": re.compile(cmd["expect"]),
            "groups": cmd.get("groups", []),
            "timeout": time.time() + cmd.get("timeout_ms", 500) / 1000.0
        }

    # -----------------------------
    # Main message interpreter
    # -----------------------------
    def interpret(self, msg: str):
        msg = msg.strip()
        if not msg:
            return None
        timestamp = datetime.now().isoformat() #.strftime("%Y%m%d_%H%M%S")
        now = time.time()

        # 1. Safety rules first
        for prio in sorted(self.rules_by_priority.keys(), reverse=True):
            for rule in self.rules_by_priority[prio]:
                if "safety" in rule.flags:
                    m = rule.match(msg)
                    if m:
                        return {
                            "timestamp": timestamp,
                            "event": "safety",
                            "rule": rule.name,
                            "data": rule.extract(m)
                        }

        # 2. Expected command response
        if self.expected:
            if now > self.expected["timeout"]:
                evt = {
                    "timestamp": timestamp,
                    "event": "timeout",
                    "command": self.expected["name"]
                }
                self.expected = None
                return evt

            m = self.expected["regex"].search(msg)
            if m:
                data = {}
                for i, key in enumerate(self.expected["groups"]):
                    data[key] = m.group(i + 1)

                evt = {
                    "timestamp": timestamp,
                    "event": "command_response",
                    "command": self.expected["name"],
                    "data": data
                }
                self.expected = None
                return evt

        # 3. Normal rules by priority
        for prio in sorted(self.rules_by_priority.keys(), reverse=True):
            for rule in self.rules_by_priority[prio]:
                m = rule.match(msg)
                if m:
                    evt_type = "telemetry"
                    if "ack" in rule.flags:
                        evt_type = "ack"
                    elif "sequence" in rule.flags:
                        evt_type = "sequence_step"

                    return {
                        "timestamp": timestamp,
                        "event": evt_type,
                        "rule": rule.name,
                        "data": rule.extract(m)
                    }

        # 4. Unmatched
        return {
            "timestamp": timestamp,
            "event": "unmatched",
            "message": msg
        }


# ------------------------------------------------------------
# Test messages
# ------------------------------------------------------------
test_messages = [
    "********Overcurrent Emergency Shutdown********",
    "Sequence mode=1 AUTO, step=2/10, rep=1/5, ts=123.4, pwm=50.0, v_sp=12.5, i_sp=1.2, p_sp=15.0, iave=1.1, vave=12.4, pave=13.7",
    "3 Step 2 SP: 12.50 -> 13.00 t=150ms",
    "GPIO A1; PWM 50.0%; CONTROL PID; MODE Voltage(1);SP 12.50V(12.40),Kp 1.00,Ki 0.50,Kd 0.10; >>> Vave 12.40(12.30), Iave 1.20(1.10), Pave 15.00(14.50)",
    "v_sp=12.50V(12.40), vave=12.30(12.20), vint=0.50",
    "A3: 1023",
    "Unknown message that should not match anything"
]


# ------------------------------------------------------------
# Run test
# ------------------------------------------------------------

if __name__ == "__main__":
    from class_LogHandler import get_appPath
    import os
    ymlfile=os.path.join(get_appPath(),"Devices/GIGAPIDCONTROLLER_patterns.yml")
    if not os.path.exists(ymlfile):
        print(f"File {ymlfile} does not exist!")
    else:
        parser = DeviceParser(ymlfile)
        for msg in test_messages:
            print("\n--- MESSAGE ---")
            print(msg)
            event = parser.interpret(msg)
            print("--- EVENT ---") 
            print(event)
            
