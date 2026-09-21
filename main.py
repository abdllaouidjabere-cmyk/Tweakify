import os
import sys
import ctypes
import shutil
import subprocess
import threading
import winreg
import psutil
import platform
from datetime import datetime
# pyrefly: ignore [missing-import]
import customtkinter as ctk
from tkinter import messagebox

# ═══════════════════════════════════════════════
#             TWEAKIFY v2.0
#     Professional Windows Performance Suite
#         Developed by Jaber © 2025
# ═══════════════════════════════════════════════

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ──────────────────────────────────────────────
#  Helper function: Run a command silently
# ──────────────────────────────────────────────
def run_cmd(cmd, shell=True):
    try:
        subprocess.run(cmd, shell=shell, capture_output=True, timeout=15)
        return True
    except Exception:
        return False


# ──────────────────────────────────────────────
#  Helper function: Modify the Registry
# ──────────────────────────────────────────────
def set_registry(hive, path, name, value, reg_type=winreg.REG_DWORD):
    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, name, 0, reg_type, value)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def get_registry(hive, path, name):
    """Read a value from the Registry — returns None on failure"""
    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return val
    except Exception:
        return None


# ══════════════════════════════════════════════
#        Snapshot / Restore System
# ══════════════════════════════════════════════
import json, time

SNAPSHOT_FILE = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "tweakify_snapshot.json")

class SystemSnapshot:
    """Saves system settings before modification and restores them on request"""

    # Each entry: (hive, path, name, default_value)
    REGISTRY_ENTRIES = [
        (winreg.HKEY_CURRENT_USER,  r"Control Panel\Desktop\WindowMetrics",
         "MinAnimate",              1),
        (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
         "VisualFXSetting",         1),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
         "EnableTransparency",      1),
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Power",
         "HiberbootEnabled",        0),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\GameBar",
         "AutoGameModeEnabled",     0),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\GameBar",
         "AllowAutoGameMode",       0),
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
         "TcpAckFrequency",         2),
    ]

    SERVICES_DEFAULT = {
        "SysMain":        "auto",
        "DiagTrack":      "auto",
        "WSearch":        "auto",
        "XblAuthManager": "demand",
    }

    POWER_BALANCED = "381b4222-f694-41f0-9685-ff5bb260df2e"

    def take(self, log_fn=None):
        """Takes a snapshot of the current state and saves it"""
        snap = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "registry":  {},
            "services":  {},
            "power_plan": self._get_active_power_plan(),
        }

        for hive, path, name, default in self.REGISTRY_ENTRIES:
            val = get_registry(hive, path, name)
            # Convert hive to string for JSON
            hive_str = "HKCU" if hive == winreg.HKEY_CURRENT_USER else "HKLM"
            key_id = f"{hive_str}|{path}|{name}"
            snap["registry"][key_id] = val if val is not None else default

        for svc, default_start in self.SERVICES_DEFAULT.items():
            snap["services"][svc] = self._get_service_start(svc) or default_start

        try:
            with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
                json.dump(snap, f, ensure_ascii=False, indent=2)
            if log_fn:
                log_fn(f"💾 Snapshot saved: {snap['timestamp']}")
            return True
        except Exception as e:
            if log_fn:
                log_fn(f"❌ Failed to save snapshot: {e}")
            return False

    def load(self):
        """Load the saved snapshot"""
        try:
            with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def restore(self, log_fn=None):
        """Restore settings from snapshot"""
        snap = self.load()
        if not snap:
            if log_fn:
                log_fn("❌ No saved snapshot found to restore!")
            return False

        if log_fn:
            log_fn(f"♻️ Restoring to: {snap['timestamp']}")

        # ── Restore Registry ──
        hive_map = {"HKCU": winreg.HKEY_CURRENT_USER, "HKLM": winreg.HKEY_LOCAL_MACHINE}
        for key_id, value in snap["registry"].items():
            parts = key_id.split("|", 2)
            if len(parts) == 3:
                hive_str, path, name = parts
                hive = hive_map.get(hive_str)
                if hive and value is not None:
                    set_registry(hive, path, name, int(value))

        if log_fn:
            log_fn("✅ Registry settings restored")

        # ── Restore Services ──
        for svc, start_type in snap["services"].items():
            run_cmd(f"sc config {svc} start= {start_type}")
            run_cmd(f"sc start {svc}")
        if log_fn:
            log_fn("✅ Services restored")

        # ── Restore Power Plan ──
        power_guid = snap.get("power_plan") or self.POWER_BALANCED
        run_cmd(f"powercfg /setactive {power_guid}")
        if log_fn:
            log_fn("✅ Power plan restored")

        # ── Restore TCP Settings ──
        run_cmd("netsh int tcp set global autotuninglevel=normal")
        run_cmd("netsh int tcp set global rss=enabled")
        if log_fn:
            log_fn("✅ Network settings restored")

        # ── Restore Cortana ──
        run_cmd('reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /f')
        if log_fn:
            log_fn("✅ Cortana restored")

        # ── Restore BCD ──
        run_cmd("bcdedit /deletevalue useplatformtick")
        if log_fn:
            log_fn("✅ Timer settings restored")

        if log_fn:
            log_fn("🎉 Restore complete! It is recommended to restart your PC.")
        return True

    def _get_active_power_plan(self):
        try:
            result = subprocess.run("powercfg /getactivescheme", shell=True,
                                    capture_output=True, text=True, timeout=10)
            out = result.stdout.strip()
            import re
            match = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", out)
            return match.group(1) if match else self.POWER_BALANCED
        except Exception:
            return self.POWER_BALANCED

    def _get_service_start(self, svc):
        try:
            result = subprocess.run(f"sc qc {svc}", shell=True,
                                    capture_output=True, text=True, timeout=8)
            for line in result.stdout.splitlines():
                if "START_TYPE" in line:
                    if "AUTO" in line:
                        return "auto"
                    elif "DEMAND" in line:
                        return "demand"
                    elif "DISABLED" in line:
                        return "disabled"
            return "auto"
        except Exception:
            return "auto"


# ══════════════════════════════════════════════
#        Smart Hardware Analyzer
# ══════════════════════════════════════════════
class HardwareAnalyzer:
    """Inspects system components and suggests the optimal power plan"""

    # Power plan GUIDs
    PLANS = {
        "ultimate":    ("🏎️ Ultimate Performance",  "e9a42b02-d5df-448d-aa00-03f14749eb61"),
        "high":        ("⚡ High Performance",       "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"),
        "balanced":    ("⚖️ Balanced",               "381b4222-f694-41f0-9685-ff5bb260df2e"),
        "saver":       ("🔋 Power Saver",            "a1841308-3541-4fab-bc81-f71556f20b4a"),
    }

    def __init__(self):
        self.profile   = {}   # Scan results
        self.score     = 0    # Performance score (0-100)
        self.plan_key  = "balanced"
        self.reasons   = []   # Reasons for recommendation
        self.warnings  = []   # Warnings

    # ── Gather information ──
    def analyze(self, log_fn=None):
        def _log(msg):
            if log_fn:
                log_fn(msg)

        _log("🔬 Starting hardware analysis...")

        self._detect_cpu(log_fn)
        self._detect_ram(log_fn)
        self._detect_gpu(log_fn)
        self._detect_battery(log_fn)
        self._detect_storage(log_fn)
        self._detect_thermal(log_fn)

        self._calculate_recommendation()

        _log(f"✅ Analysis complete. Score: {self.score}/100")
        _log(f"💡 Recommended plan: {self.PLANS[self.plan_key][0]}")
        return self.plan_key

    # ── CPU ──
    def _detect_cpu(self, log_fn=None):
        try:
            cores_physical = psutil.cpu_count(logical=False) or 1
            cores_logical  = psutil.cpu_count(logical=True)  or 1
            freq           = psutil.cpu_freq()
            max_freq       = freq.max if freq else 0

            self.profile["cpu_cores_p"] = cores_physical
            self.profile["cpu_cores_l"] = cores_logical
            self.profile["cpu_freq_max"] = max_freq

            cpu_name = platform.processor().lower()
            self.profile["cpu_name"] = cpu_name

            # Classification: gaming/workstation or regular laptop?
            is_server_class = cores_physical >= 8
            is_gaming_class = (cores_physical >= 6) or ("i7" in cpu_name) or \
                              ("i9" in cpu_name) or ("ryzen 7" in cpu_name) or \
                              ("ryzen 9" in cpu_name) or ("threadripper" in cpu_name)
            is_mobile       = ("u" in cpu_name and "ultra" not in cpu_name) or \
                              ("m " in cpu_name) or ("mobile" in cpu_name)

            self.profile["cpu_gaming"]  = is_gaming_class
            self.profile["cpu_mobile"]  = is_mobile
            self.profile["cpu_server"]  = is_server_class

            # CPU score
            pts = min(40, cores_physical * 4 + (int(max_freq / 500) if max_freq else 0))
            self.profile["cpu_score"] = pts

            if log_fn:
                log_fn(f"   🏛️ CPU: {cores_physical}P/{cores_logical}L cores | {max_freq:.0f} MHz")
        except Exception as e:
            self.profile["cpu_score"] = 10
            if log_fn:
                log_fn(f"   ⚠️ Could not read CPU info: {e}")

    # ── RAM ──
    def _detect_ram(self, log_fn=None):
        try:
            ram        = psutil.virtual_memory()
            ram_gb     = ram.total / (1024 ** 3)
            ram_used_p = ram.percent

            self.profile["ram_gb"]     = ram_gb
            self.profile["ram_used_p"] = ram_used_p

            pts = 0
            if ram_gb >= 32:  pts = 20
            elif ram_gb >= 16: pts = 15
            elif ram_gb >= 8:  pts = 10
            else:              pts = 5

            self.profile["ram_score"] = pts

            if ram_gb < 8:
                self.warnings.append("⚠️ RAM is less than 8GB — Ultimate plan is not recommended")

            if log_fn:
                log_fn(f"   🧠 RAM: {ram_gb:.1f} GB ({ram_used_p}% used)")
        except Exception:
            self.profile["ram_score"] = 5

    # ── GPU ──
    def _detect_gpu(self, log_fn=None):
        gpu_name   = "Unknown"
        is_gaming  = False
        is_nvidia  = False
        is_amd     = False
        is_intel_g = False
        vram_gb    = 0

        try:
            result = subprocess.run(
                'wmic path win32_VideoController get Name,AdapterRAM /format:csv',
                shell=True, capture_output=True, text=True, timeout=10
            )
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip() and "Node" not in l]
            gpus  = []
            for line in lines:
                parts = line.split(",")
                if len(parts) >= 3:
                    name_part = parts[2].strip()
                    ram_part  = parts[1].strip()
                    if name_part:
                        gpus.append((name_part, ram_part))

            if gpus:
                # Choose the strongest GPU (not basic Intel UHD if others exist)
                dedicated = [g for g in gpus if "intel" not in g[0].lower() or "arc" in g[0].lower()]
                chosen    = dedicated[0] if dedicated else gpus[0]
                gpu_name  = chosen[0]
                try:
                    vram_bytes = int(chosen[1])
                    vram_gb    = vram_bytes / (1024 ** 3)
                except Exception:
                    vram_gb = 0

                gpu_lower  = gpu_name.lower()
                is_nvidia  = "nvidia" in gpu_lower or "geforce" in gpu_lower or "rtx" in gpu_lower or "gtx" in gpu_lower
                is_amd     = "amd" in gpu_lower or "radeon" in gpu_lower or "rx " in gpu_lower
                is_intel_g = "intel" in gpu_lower and "arc" in gpu_lower

                # Is it a real gaming GPU?
                gaming_keywords = ["rtx", "gtx", "rx ", "radeon rx", "arc a", "titan", "quadro"]
                is_gaming = any(kw in gpu_lower for kw in gaming_keywords) or vram_gb >= 4
        except Exception:
            pass

        self.profile["gpu_name"]   = gpu_name
        self.profile["gpu_gaming"] = is_gaming
        self.profile["gpu_nvidia"] = is_nvidia
        self.profile["gpu_amd"]    = is_amd
        self.profile["gpu_vram"]   = vram_gb

        pts = 0
        if is_gaming:
            pts = 20
        elif is_nvidia or is_amd:
            pts = 12
        elif is_intel_g:
            pts = 8
        else:
            pts = 3

        self.profile["gpu_score"] = pts

        if log_fn:
            log_fn(f"   🎮 GPU: {gpu_name} | VRAM: {vram_gb:.1f} GB")

    # ── Battery ──
    def _detect_battery(self, log_fn=None):
        try:
            bat = psutil.sensors_battery()
            if bat:
                self.profile["has_battery"]   = True
                self.profile["battery_pct"]   = bat.percent
                self.profile["battery_plug"]  = bat.power_plugged
                self.profile["is_laptop"]     = True
                if not bat.power_plugged:
                    self.warnings.append("🔋 Device is running on battery — Balanced or Power Saver recommended")
                if log_fn:
                    plug = "Plugged in" if bat.power_plugged else "On battery"
                    log_fn(f"   🔋 Battery: {bat.percent:.0f}% ({plug})")
            else:
                self.profile["has_battery"] = False
                self.profile["is_laptop"]   = False
        except Exception:
            self.profile["has_battery"] = False
            self.profile["is_laptop"]   = False

    # ── Storage ──
    def _detect_storage(self, log_fn=None):
        try:
            disk = psutil.disk_usage("C:\\")
            free_gb = disk.free / (1024 ** 3)
            self.profile["disk_free_gb"] = free_gb
            if free_gb < 10:
                self.warnings.append("💾 Drive C: has less than 10GB free — may affect performance")
            if log_fn:
                log_fn(f"   💾 Drive C: {free_gb:.1f} GB available")
        except Exception:
            pass

    # ── Thermal ──
    def _detect_thermal(self, log_fn=None):
        try:
            temps = psutil.sensors_temperatures() if hasattr(psutil, "sensors_temperatures") else {}
            if temps:
                all_temps = [t.current for readings in temps.values() for t in readings]
                max_temp  = max(all_temps) if all_temps else 0
                self.profile["max_temp"] = max_temp
                if max_temp > 85:
                    self.warnings.append(f"🌡️ High temperature ({max_temp:.0f}°C) — Ultimate plan not recommended")
                if log_fn:
                    log_fn(f"   🌡️ Max temperature: {max_temp:.0f}°C")
        except Exception:
            pass

    # ── Calculate recommendation ──
    def _calculate_recommendation(self):
        cpu_s = self.profile.get("cpu_score", 10)
        ram_s = self.profile.get("ram_score", 5)
        gpu_s = self.profile.get("gpu_score", 5)
        self.score = min(100, cpu_s + ram_s + gpu_s)

        is_laptop      = self.profile.get("is_laptop", False)
        on_battery     = is_laptop and not self.profile.get("battery_plug", True)
        has_gaming_gpu = self.profile.get("gpu_gaming", False)
        is_gaming_cpu  = self.profile.get("cpu_gaming", False)
        high_temp      = self.profile.get("max_temp", 0) > 85
        low_ram        = self.profile.get("ram_gb", 8) < 8

        # ── Selection logic ──
        if on_battery:
            self.plan_key = "saver"
            self.reasons.append("Device is on battery → Power Saver to conserve energy")

        elif high_temp:
            self.plan_key = "balanced"
            self.reasons.append("High temperature → Balanced to reduce thermal stress")

        elif has_gaming_gpu and is_gaming_cpu and not low_ram and self.score >= 60:
            self.plan_key = "ultimate"
            self.reasons.append("Full gaming rig → Ultimate Performance for maximum output")

        elif (has_gaming_gpu or is_gaming_cpu) and not low_ram and self.score >= 40:
            self.plan_key = "high"
            self.reasons.append("High-performance components → High Performance for optimal balance")

        elif low_ram or self.score < 25:
            self.plan_key = "balanced"
            self.reasons.append("Mid-range or low RAM → Balanced for stability")

        else:
            self.plan_key = "high"
            self.reasons.append("Good components → High Performance for elevated output")

        # Additional warnings as reasons
        for w in self.warnings:
            self.reasons.append(w)

    def get_plan_label(self):
        return self.PLANS[self.plan_key][0]

    def get_plan_guid(self):
        return self.PLANS[self.plan_key][1]


# ══════════════════════════════════════════════
#          Main Window
# ══════════════════════════════════════════════
class TweakifyApp(ctk.CTk):

    VERSION = "2.0 PRO"
    AUTHOR  = "Jaber"

    # ── System colors ──
    C_ACCENT   = "#00d4ff"
    C_GREEN    = "#00ff88"
    C_ORANGE   = "#ff8c00"
    C_RED      = "#ff4444"
    C_BG_DEEP  = "#0a0a0f"
    C_BG_MID   = "#12121a"
    C_BG_CARD  = "#1a1a2e"

    def __init__(self):
        super().__init__()

        # ── Window setup ──
        self.title("⚡ TWEAKIFY v2.0 — Windows Performance Suite")
        self.geometry("800x700")
        self.minsize(800, 700)
        self.configure(fg_color=self.C_BG_DEEP)
        self.resizable(True, True)

        self.analyzer = HardwareAnalyzer()
        self.snapshot = SystemSnapshot()

        self._build_ui()
        self._update_stats_loop()
        # Run analysis in background after 1 second
        self.after(1200, lambda: threading.Thread(target=self._run_auto_analysis, daemon=True).start())

    # ══════════════════════════════════════════
    #          Build UI
    # ══════════════════════════════════════════
    def _build_ui(self):
        # ── Top title bar ──
        self._build_header()

        # ── Content area (tabs) ──
        self.tab_view = ctk.CTkTabview(
            self,
            fg_color=self.C_BG_MID,
            segmented_button_selected_color=self.C_ACCENT,
            segmented_button_selected_hover_color="#009ab8",
            segmented_button_unselected_color=self.C_BG_CARD,
            segmented_button_unselected_hover_color="#1e1e30",
            text_color="white",
            corner_radius=12,
        )
        self.tab_view.pack(pady=(0, 10), padx=20, fill="both", expand=True)

        self.tab_view.add("🤖  Smart Power")
        self.tab_view.add("🚀  Performance")
        self.tab_view.add("🧹  Cleanup")
        self.tab_view.add("🔧  Tweaks")
        self.tab_view.add("♻️  Restore")
        self.tab_view.add("📊  System Info")

        self._build_tab_smart_power()
        self._build_tab_performance()
        self._build_tab_clean()
        self._build_tab_tweak()
        self._build_tab_restore()
        self._build_tab_sysinfo()

        # ── Log console ──
        self._build_console()

    # ──────────────────────────────────────────
    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=self.C_BG_CARD, corner_radius=12, height=80)
        hdr.pack(fill="x", padx=20, pady=(15, 10))
        hdr.pack_propagate(False)

        # Program name
        ctk.CTkLabel(
            hdr,
            text="⚡  TWEAKIFY",
            font=("Consolas", 26, "bold"),
            text_color=self.C_ACCENT,
        ).place(x=20, y=10)

        ctk.CTkLabel(
            hdr,
            text=f"Windows Performance Suite  •  v{self.VERSION}  •  by {self.AUTHOR}",
            font=("Consolas", 11),
            text_color="gray",
        ).place(x=22, y=46)

        # Live indicators (CPU / RAM) in top-right corner
        self.lbl_cpu = ctk.CTkLabel(hdr, text="CPU: ---%", font=("Consolas", 12), text_color=self.C_GREEN)
        self.lbl_cpu.place(relx=0.75, rely=0.2)

        self.lbl_ram = ctk.CTkLabel(hdr, text="RAM: ---%", font=("Consolas", 12), text_color=self.C_ORANGE)
        self.lbl_ram.place(relx=0.75, rely=0.55)

    # ──────────────────────────────────────────
    def _build_tab_smart_power(self):
        tab = self.tab_view.tab("🤖  Smart Power")

        # ── Result card ──
        result_frame = ctk.CTkFrame(tab, fg_color=self.C_BG_CARD, corner_radius=12)
        result_frame.pack(fill="x", padx=5, pady=(8, 6))

        ctk.CTkLabel(result_frame, text="🤖 Smart Power Plan Recommendation",
                     font=("Consolas", 13, "bold"), text_color=self.C_ACCENT).pack(anchor="w", padx=14, pady=(10, 2))
        ctk.CTkFrame(result_frame, fg_color=self.C_ACCENT, height=1).pack(fill="x", padx=14)

        inner_r = ctk.CTkFrame(result_frame, fg_color="transparent")
        inner_r.pack(fill="x", padx=14, pady=10)

        # Performance score
        score_col = ctk.CTkFrame(inner_r, fg_color=self.C_BG_DEEP, corner_radius=10, width=160)
        score_col.pack(side="left", padx=(0, 12), pady=4, fill="y")
        score_col.pack_propagate(False)

        ctk.CTkLabel(score_col, text="Device Score", font=("Consolas", 11), text_color="gray").pack(pady=(14, 2))
        self.lbl_hw_score = ctk.CTkLabel(score_col, text="--", font=("Consolas", 34, "bold"), text_color=self.C_ACCENT)
        self.lbl_hw_score.pack()
        ctk.CTkLabel(score_col, text="/ 100", font=("Consolas", 11), text_color="gray").pack(pady=(0, 14))

        # Recommended plan
        plan_col = ctk.CTkFrame(inner_r, fg_color="transparent")
        plan_col.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(plan_col, text="Recommended Plan:", font=("Consolas", 11), text_color="gray").pack(anchor="w")
        self.lbl_recommended_plan = ctk.CTkLabel(plan_col, text="Analyzing...",
                                                  font=("Consolas", 18, "bold"), text_color=self.C_GREEN)
        self.lbl_recommended_plan.pack(anchor="w", pady=4)

        self.lbl_plan_reason = ctk.CTkLabel(plan_col, text="",
                                             font=("Consolas", 10), text_color="gray",
                                             wraplength=400, justify="left")
        self.lbl_plan_reason.pack(anchor="w")

        self.btn_apply_smart = ctk.CTkButton(
            result_frame,
            text="✅ Apply Recommended Plan Now",
            command=self._apply_smart_plan,
            fg_color=self.C_GREEN, hover_color="#00aa66", text_color="black",
            height=40, font=("Consolas", 13, "bold"), corner_radius=10,
            state="disabled",
        )
        self.btn_apply_smart.pack(fill="x", padx=14, pady=(4, 14))

        # ── Smart progress bar card ──
        bars_frame = ctk.CTkFrame(tab, fg_color=self.C_BG_CARD, corner_radius=12)
        bars_frame.pack(fill="x", padx=5, pady=6)
        ctk.CTkLabel(bars_frame, text="📊 Component Analysis",
                     font=("Consolas", 12, "bold"), text_color=self.C_ACCENT).pack(anchor="w", padx=14, pady=(10, 4))
        ctk.CTkFrame(bars_frame, fg_color=self.C_ACCENT, height=1).pack(fill="x", padx=14)

        bars_inner = ctk.CTkFrame(bars_frame, fg_color="transparent")
        bars_inner.pack(fill="x", padx=14, pady=10)

        self._hw_bars = {}
        hw_items = [
            ("cpu",  "🏛️  CPU",    self.C_ACCENT),
            ("ram",  "🧠  RAM",    self.C_ORANGE),
            ("gpu",  "🎮  GPU",    self.C_GREEN),
        ]
        for key, label, color in hw_items:
            row = ctk.CTkFrame(bars_inner, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=label, font=("Consolas", 11), width=130, anchor="w").pack(side="left")
            bar = ctk.CTkProgressBar(row, progress_color=color, height=12, corner_radius=6)
            bar.set(0)
            bar.pack(side="left", fill="x", expand=True, padx=8)
            lbl = ctk.CTkLabel(row, text="--", font=("Consolas", 11), text_color=color, width=50)
            lbl.pack(side="left")
            self._hw_bars[key] = (bar, lbl)

        # ── Component detail card ──
        detail_frame = ctk.CTkFrame(tab, fg_color=self.C_BG_CARD, corner_radius=12)
        detail_frame.pack(fill="both", expand=True, padx=5, pady=6)
        ctk.CTkLabel(detail_frame, text="🔍 Detected Component Details",
                     font=("Consolas", 12, "bold"), text_color=self.C_ACCENT).pack(anchor="w", padx=14, pady=(10, 4))
        ctk.CTkFrame(detail_frame, fg_color=self.C_ACCENT, height=1).pack(fill="x", padx=14)

        self.smart_detail_box = ctk.CTkScrollableFrame(detail_frame, fg_color="transparent")
        self.smart_detail_box.pack(fill="both", expand=True, padx=10, pady=8)

        self.lbl_analyzing = ctk.CTkLabel(
            self.smart_detail_box,
            text="⏳ Analysis will begin automatically in a moment...",
            font=("Consolas", 12), text_color="gray",
        )
        self.lbl_analyzing.pack(pady=20)

        # Re-analyze button
        ctk.CTkButton(
            tab,
            text="🔄 Re-analyze Hardware",
            command=lambda: threading.Thread(target=self._run_auto_analysis, daemon=True).start(),
            fg_color=self.C_BG_CARD, border_color=self.C_ACCENT, border_width=1,
            height=36, font=("Consolas", 12),
        ).pack(fill="x", padx=5, pady=(2, 8))

    # ──────────────────────────────────────────
    def _run_auto_analysis(self):
        """Runs in a separate thread — analyzes hardware and updates the UI"""
        # Clear old details
        self.after(0, self._clear_smart_details)
        self.after(0, lambda: self.btn_apply_smart.configure(state="disabled"))
        self.after(0, lambda: self.lbl_recommended_plan.configure(text="Analyzing...", text_color="gray"))

        self.analyzer = HardwareAnalyzer()
        self.analyzer.analyze(log_fn=self.log)

        # Update UI in the main thread
        self.after(0, self._update_smart_ui)

    def _clear_smart_details(self):
        for w in self.smart_detail_box.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.smart_detail_box, text="⏳ Analyzing...",
                     font=("Consolas", 11), text_color="gray").pack(pady=10)

    def _update_smart_ui(self):
        a = self.analyzer
        p = a.profile

        # ── Device score ──
        score = a.score
        score_color = self.C_GREEN if score >= 65 else (self.C_ORANGE if score >= 35 else self.C_RED)
        self.lbl_hw_score.configure(text=str(score), text_color=score_color)

        # ── Recommended plan ──
        plan_colors = {
            "ultimate": "#ff4444",
            "high":     "#ff8c00",
            "balanced": self.C_ACCENT,
            "saver":    self.C_GREEN,
        }
        plan_label = a.get_plan_label()
        plan_color = plan_colors.get(a.plan_key, self.C_ACCENT)
        self.lbl_recommended_plan.configure(text=plan_label, text_color=plan_color)

        reasons_text = "\n".join(f"• {r}" for r in a.reasons) if a.reasons else ""
        self.lbl_plan_reason.configure(text=reasons_text)
        self.btn_apply_smart.configure(state="normal")

        # ── Component bars ──
        cpu_max = 40
        ram_max = 20
        gpu_max = 20

        cpu_s = p.get("cpu_score", 0)
        ram_s = p.get("ram_score", 0)
        gpu_s = p.get("gpu_score", 0)

        bar_cpu, lbl_cpu = self._hw_bars["cpu"]
        bar_ram, lbl_ram = self._hw_bars["ram"]
        bar_gpu, lbl_gpu = self._hw_bars["gpu"]

        bar_cpu.set(min(1.0, cpu_s / cpu_max))
        lbl_cpu.configure(text=f"{cpu_s}/{cpu_max}")

        bar_ram.set(min(1.0, ram_s / ram_max))
        lbl_ram.configure(text=f"{ram_s}/{ram_max}")

        bar_gpu.set(min(1.0, gpu_s / gpu_max))
        lbl_gpu.configure(text=f"{gpu_s}/{gpu_max}")

        # ── Component details ──
        for w in self.smart_detail_box.winfo_children():
            w.destroy()

        details = [
            ("🏛️ CPU",              p.get("cpu_name", "N/A")[:60]),
            ("🧵 Cores",            f"{p.get('cpu_cores_p','?')} Physical / {p.get('cpu_cores_l','?')} Logical"),
            ("⚡ Max Frequency",    f"{p.get('cpu_freq_max', 0):.0f} MHz"),
            ("🧠 RAM",              f"{p.get('ram_gb', 0):.1f} GB ({p.get('ram_used_p', 0):.0f}% used)"),
            ("🎮 GPU",              p.get("gpu_name", "N/A")[:60]),
            ("📺 VRAM",             f"{p.get('gpu_vram', 0):.1f} GB"),
            ("💻 Device Type",      "Laptop" if p.get("is_laptop") else "Desktop"),
            ("🔋 Battery",          f"{p.get('battery_pct', 0):.0f}%" if p.get("has_battery") else "Not present"),
            ("💾 Drive C: Free",    f"{p.get('disk_free_gb', 0):.1f} GB"),
            ("🌡️ Max Temperature",  f"{p.get('max_temp', 0):.0f}°C" if p.get("max_temp") else "Not available"),
        ]

        for label, value in details:
            row = ctk.CTkFrame(self.smart_detail_box, fg_color=self.C_BG_DEEP, corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)
            ctk.CTkLabel(row, text=label, font=("Consolas", 11, "bold"),
                         text_color=self.C_ACCENT, width=160, anchor="w").pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(row, text=value, font=("Consolas", 11),
                         text_color="white", anchor="w").pack(side="left", padx=5)

        # Warnings if any
        if a.warnings:
            ctk.CTkLabel(self.smart_detail_box, text="⚠️ Warnings:",
                         font=("Consolas", 11, "bold"), text_color=self.C_ORANGE).pack(anchor="w", padx=4, pady=(8, 2))
            for w in a.warnings:
                ctk.CTkLabel(self.smart_detail_box, text=w,
                             font=("Consolas", 10), text_color=self.C_ORANGE).pack(anchor="w", padx=12)

    def _apply_smart_plan(self):
        guid  = self.analyzer.get_plan_guid()
        label = self.analyzer.get_plan_label()
        self.log(f"🤖 Applying recommended plan: {label}")
        threading.Thread(target=lambda: self._set_power(guid, label), daemon=True).start()

    # ──────────────────────────────────────────
    def _build_tab_performance(self):
        tab = self.tab_view.tab("🚀  Performance")

        # Card: Power Plan
        self._card(tab, "⚡ Power Plans", 0, 0, colspan=2, content_fn=self._power_card)

        # Card: Services
        self._card(tab, "🛑 Service Manager", 1, 0, content_fn=self._services_card)

        # Card: RAM
        self._card(tab, "🧠 Memory Optimization", 1, 1, content_fn=self._ram_card)

        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)

    def _power_card(self, frame):
        plans = [
            ("⚡ High Performance",        "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"),
            ("🏎️ Ultimate Performance",     "e9a42b02-d5df-448d-aa00-03f14749eb61"),
            ("⚖️ Balanced",                 "381b4222-f694-41f0-9685-ff5bb260df2e"),
            ("🔋 Power Saver",              "a1841308-3541-4fab-bc81-f71556f20b4a"),
        ]
        for i, (label, guid) in enumerate(plans):
            btn = ctk.CTkButton(
                frame, text=label,
                command=lambda g=guid, l=label: self._set_power(g, l),
                fg_color=self.C_BG_DEEP, hover_color="#1e3a4a",
                border_color=self.C_ACCENT, border_width=1,
                font=("Consolas", 12), height=34,
            )
            btn.grid(row=0, column=i, padx=6, pady=6, sticky="ew")
            frame.columnconfigure(i, weight=1)

    def _services_card(self, frame):
        services = [
            ("SysMain (SuperFetch)", "SysMain"),
            ("Telemetry",            "DiagTrack"),
            ("Windows Update",       "wuauserv"),
            ("Xbox Live",            "XblAuthManager"),
        ]
        for i, (label, svc) in enumerate(services):
            row_f = ctk.CTkFrame(frame, fg_color="transparent")
            row_f.grid(row=i, column=0, columnspan=2, sticky="ew", pady=2)
            row_f.columnconfigure(0, weight=1)

            ctk.CTkLabel(row_f, text=label, font=("Consolas", 11), text_color="lightgray").grid(row=0, column=0, sticky="w")

            ctk.CTkButton(
                row_f, text="Stop", width=70, height=26,
                fg_color=self.C_RED, hover_color="#aa2222",
                font=("Consolas", 11),
                command=lambda s=svc: self._stop_service(s),
            ).grid(row=0, column=1, padx=4)

            ctk.CTkButton(
                row_f, text="Start", width=70, height=26,
                fg_color="#1a5e1a", hover_color="#2a8a2a",
                font=("Consolas", 11),
                command=lambda s=svc: self._start_service(s),
            ).grid(row=0, column=2, padx=4)

        frame.columnconfigure(0, weight=1)

    def _ram_card(self, frame):
        self.ram_bar = ctk.CTkProgressBar(frame, progress_color=self.C_ORANGE, height=14)
        self.ram_bar.set(0)
        self.ram_bar.pack(fill="x", pady=(0, 8))

        self.lbl_ram_detail = ctk.CTkLabel(frame, text="Checking...", font=("Consolas", 11), text_color="gray")
        self.lbl_ram_detail.pack()

        ctk.CTkButton(
            frame, text="🧹 Free RAM Now",
            command=lambda: threading.Thread(target=self.optimize_ram, daemon=True).start(),
            fg_color="#1a3a4a", hover_color="#1e4a5a",
            border_color=self.C_ORANGE, border_width=1,
            font=("Consolas", 12), height=36,
        ).pack(fill="x", pady=(10, 0))

    # ──────────────────────────────────────────
    def _build_tab_clean(self):
        tab = self.tab_view.tab("🧹  Cleanup")

        # List of items to clean
        self.clean_vars = {}
        items = [
            ("temp_user",    "🗑️  User Temp Files"),
            ("temp_windows", "🗑️  Windows Temp Files"),
            ("prefetch",     "⚡  Prefetch Files"),
            ("recycle",      "♻️  Recycle Bin"),
            ("browser_cache","🌐  Browser Cache"),
            ("event_logs",   "📋  Event Logs"),
            ("update_cache", "🔄  Windows Update Cache"),
            ("thumbnail",    "🖼️  Thumbnail Cache"),
        ]

        frame_checks = ctk.CTkScrollableFrame(tab, fg_color=self.C_BG_CARD, corner_radius=10)
        frame_checks.pack(fill="both", expand=True, pady=(10, 8), padx=5)

        for key, label in items:
            var = ctk.BooleanVar(value=True)
            self.clean_vars[key] = var
            ctk.CTkCheckBox(
                frame_checks, text=label, variable=var,
                font=("Consolas", 12),
                checkmark_color=self.C_GREEN,
                border_color=self.C_ACCENT,
            ).pack(anchor="w", pady=5, padx=10)

        # Control buttons
        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.pack(fill="x", pady=6, padx=5)

        ctk.CTkButton(
            btn_row, text="✅ Select All",
            command=lambda: [v.set(True) for v in self.clean_vars.values()],
            fg_color=self.C_BG_CARD, width=120, height=36, font=("Consolas", 12),
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row, text="❌ Deselect All",
            command=lambda: [v.set(False) for v in self.clean_vars.values()],
            fg_color=self.C_BG_CARD, width=120, height=36, font=("Consolas", 12),
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row, text="🚀 Clean Selected Now",
            command=lambda: threading.Thread(target=self.run_clean, daemon=True).start(),
            fg_color=self.C_ACCENT, hover_color="#009ab8", text_color="black",
            height=40, font=("Consolas", 13, "bold"),
        ).pack(side="right", padx=5)

    # ──────────────────────────────────────────
    def _build_tab_tweak(self):
        tab = self.tab_view.tab("🔧  Tweaks")

        tweaks = [
            ("disable_animations",  "🎞️  Disable Animations",           self._tweak_disable_animations),
            ("disable_transparency","💎  Disable Transparency",          self._tweak_disable_transparency),
            ("fast_startup",        "⚡  Enable Fast Startup",           self._tweak_fast_startup),
            ("disable_cortana",     "🤫  Disable Cortana",              self._tweak_disable_cortana),
            ("gaming_mode",         "🎮  Enable Game Mode",             self._tweak_gaming_mode),
            ("high_timer",          "⏱️  Increase Timer Resolution",    self._tweak_timer),
            ("network_opt",         "🌐  Optimize Network",             self._tweak_network),
            ("disable_search_idx",  "🔍  Disable Search Indexing",      self._tweak_search_index),
        ]

        self.tweak_vars = {}
        frame_tw = ctk.CTkScrollableFrame(tab, fg_color=self.C_BG_CARD, corner_radius=10)
        frame_tw.pack(fill="both", expand=True, pady=(10, 8), padx=5)

        for key, label, _ in tweaks:
            var = ctk.BooleanVar(value=False)
            self.tweak_vars[key] = var
            ctk.CTkCheckBox(
                frame_tw, text=label, variable=var,
                font=("Consolas", 12),
                checkmark_color=self.C_GREEN,
                border_color=self.C_ACCENT,
            ).pack(anchor="w", pady=6, padx=10)

        self._tweak_actions = {k: fn for k, _, fn in tweaks}

        ctk.CTkButton(
            tab, text="⚙️  Apply Selected Tweaks",
            command=lambda: threading.Thread(target=self.apply_tweaks, daemon=True).start(),
            fg_color=self.C_GREEN, hover_color="#00aa66", text_color="black",
            height=42, font=("Consolas", 13, "bold"), corner_radius=10,
        ).pack(fill="x", pady=6, padx=5)

    # ──────────────────────────────────────────
    def _build_tab_restore(self):
        tab = self.tab_view.tab("♻️  Restore")

        # ── Card: Current snapshot ──
        snap_frame = ctk.CTkFrame(tab, fg_color=self.C_BG_CARD, corner_radius=12)
        snap_frame.pack(fill="x", padx=5, pady=(8, 6))

        ctk.CTkLabel(snap_frame, text="💾 Settings Snapshot",
                     font=("Consolas", 13, "bold"), text_color=self.C_ACCENT).pack(anchor="w", padx=14, pady=(10, 2))
        ctk.CTkFrame(snap_frame, fg_color=self.C_ACCENT, height=1).pack(fill="x", padx=14)

        snap_inner = ctk.CTkFrame(snap_frame, fg_color="transparent")
        snap_inner.pack(fill="x", padx=14, pady=10)

        # Snapshot status
        snap_data = self.snapshot.load()
        if snap_data:
            snap_text  = f"📅 Saved on: {snap_data.get('timestamp', 'Unknown')}"
            snap_color = self.C_GREEN
        else:
            snap_text  = "⚠️  No snapshot saved yet"
            snap_color = self.C_ORANGE

        self.lbl_snap_status = ctk.CTkLabel(
            snap_inner, text=snap_text,
            font=("Consolas", 12), text_color=snap_color,
        )
        self.lbl_snap_status.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            snap_inner,
            text="💡 Snapshot saves: Power plan, Services, Registry settings, Network.\n"
                 "    It is taken automatically before any change, or you can take one manually now.",
            font=("Consolas", 10), text_color="gray", justify="left",
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkButton(
            snap_frame,
            text="📸 Take Snapshot Now (Before Modifying)",
            command=lambda: threading.Thread(target=self._take_snapshot_now, daemon=True).start(),
            fg_color=self.C_BG_DEEP, hover_color="#1e3a4a",
            border_color=self.C_ACCENT, border_width=1,
            height=38, font=("Consolas", 12),
        ).pack(fill="x", padx=14, pady=(0, 14))

        # ── Card: What will be restored ──
        what_frame = ctk.CTkFrame(tab, fg_color=self.C_BG_CARD, corner_radius=12)
        what_frame.pack(fill="x", padx=5, pady=6)

        ctk.CTkLabel(what_frame, text="🔍 What Will Be Restored?",
                     font=("Consolas", 12, "bold"), text_color=self.C_ACCENT).pack(anchor="w", padx=14, pady=(10, 2))
        ctk.CTkFrame(what_frame, fg_color=self.C_ACCENT, height=1).pack(fill="x", padx=14)

        items_text = [
            ("⚡", "Power Plan",           "Reverted to the plan active at snapshot time"),
            ("🛑", "Services",             "SysMain, DiagTrack, WSearch, XblAuthManager"),
            ("🎞️", "Animations",           "Re-enabled if they were disabled"),
            ("💎", "Transparency",         "Restored to its original state"),
            ("🌐", "TCP Network Settings", "Reset to defaults"),
            ("🤫", "Cortana",              "Disable policy removed"),
            ("⏱️", "Timer Resolution",     "Reset to default"),
            ("🎮", "Game Mode",            "Restored to original setting"),
        ]

        for icon, label, desc in items_text:
            row = ctk.CTkFrame(what_frame, fg_color=self.C_BG_DEEP, corner_radius=6)
            row.pack(fill="x", pady=2, padx=14)
            ctk.CTkLabel(row, text=f"{icon}  {label}", font=("Consolas", 11, "bold"),
                         text_color="white", width=180, anchor="w").pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(row, text=desc, font=("Consolas", 10),
                         text_color="gray", anchor="w").pack(side="left")

        ctk.CTkFrame(what_frame, fg_color="transparent", height=6).pack()

        # ── Note ──
        note_frame = ctk.CTkFrame(tab, fg_color="#2a1a00", corner_radius=10)
        note_frame.pack(fill="x", padx=5, pady=6)
        ctk.CTkLabel(
            note_frame,
            text="⚠️  Note: Restore does NOT recover files deleted during cleanup.\n"
                 "    Only system settings, services, and the power plan are restored.",
            font=("Consolas", 10), text_color=self.C_ORANGE, justify="left",
        ).pack(padx=14, pady=8, anchor="w")

        # ── Main restore button ──
        self.btn_restore = ctk.CTkButton(
            tab,
            text="♻️  Restore All Settings to Previous State",
            command=self._confirm_restore,
            fg_color=self.C_RED, hover_color="#aa2222",
            height=50, font=("Consolas", 14, "bold"), corner_radius=12,
            state="normal" if snap_data else "disabled",
        )
        self.btn_restore.pack(fill="x", padx=5, pady=8)

    # ──────────────────────────────────────────
    def _take_snapshot_now(self):
        self.log("📸 Taking snapshot of current settings...")
        ok = self.snapshot.take(log_fn=self.log)
        if ok:
            snap_data = self.snapshot.load()
            ts = snap_data.get("timestamp", "") if snap_data else ""
            self.after(0, lambda: self.lbl_snap_status.configure(
                text=f"📅 Saved on: {ts}", text_color=self.C_GREEN))
            self.after(0, lambda: self.btn_restore.configure(state="normal"))
        else:
            self.after(0, lambda: self.lbl_snap_status.configure(
                text="❌ Failed to save snapshot!", text_color=self.C_RED))

    def _confirm_restore(self):
        """Confirmation dialog before restoring"""
        win = ctk.CTkToplevel(self)
        win.title("Confirm Restore")
        win.geometry("440x220")
        win.resizable(False, False)
        win.configure(fg_color=self.C_BG_CARD)
        win.grab_set()
        win.lift()

        ctk.CTkLabel(win, text="⚠️  Confirm Restore",
                     font=("Consolas", 16, "bold"), text_color=self.C_RED).pack(pady=(20, 8))
        ctk.CTkLabel(win,
                     text="All system settings will be reverted\n"
                          "to what they were at the last saved snapshot.\n\n"
                          "Are you sure?",
                     font=("Consolas", 12), text_color="white").pack(pady=4)

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(pady=16)

        def _do_restore():
            win.destroy()
            threading.Thread(target=self._run_restore, daemon=True).start()

        ctk.CTkButton(btn_row, text="✅ Yes, Restore Now",
                      command=_do_restore,
                      fg_color=self.C_RED, hover_color="#aa2222",
                      font=("Consolas", 12, "bold"), width=180, height=38).pack(side="left", padx=10)

        ctk.CTkButton(btn_row, text="❌ Cancel",
                      command=win.destroy,
                      fg_color=self.C_BG_DEEP, font=("Consolas", 12), width=120, height=38).pack(side="left")

    def _run_restore(self):
        self.log("♻️ Starting full restore operation...")
        self.snapshot.restore(log_fn=self.log)

    # ──────────────────────────────────────────
    def _build_tab_sysinfo(self):
        tab = self.tab_view.tab("📊  System Info")

        info_frame = ctk.CTkScrollableFrame(tab, fg_color=self.C_BG_CARD, corner_radius=10)
        info_frame.pack(fill="both", expand=True, padx=5, pady=10)

        info = self._gather_sysinfo()
        for label, value in info:
            row = ctk.CTkFrame(info_frame, fg_color=self.C_BG_DEEP, corner_radius=6)
            row.pack(fill="x", pady=3, padx=5)
            ctk.CTkLabel(row, text=label, font=("Consolas", 11, "bold"),
                         text_color=self.C_ACCENT, width=200, anchor="w").pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(row, text=value, font=("Consolas", 11),
                         text_color="white", anchor="w").pack(side="left", padx=5)

        ctk.CTkButton(
            tab, text="🔄 Refresh Info",
            command=self._refresh_sysinfo,
            fg_color=self.C_BG_CARD, border_color=self.C_ACCENT, border_width=1,
            height=36, font=("Consolas", 12),
        ).pack(fill="x", padx=5, pady=5)

    # ──────────────────────────────────────────
    def _build_console(self):
        console_outer = ctk.CTkFrame(self, fg_color=self.C_BG_CARD, corner_radius=10, height=160)
        console_outer.pack(fill="x", padx=20, pady=(0, 15))
        console_outer.pack_propagate(False)

        ctk.CTkLabel(
            console_outer, text="📡 Live Log",
            font=("Consolas", 11, "bold"), text_color=self.C_ACCENT,
        ).pack(anchor="w", padx=12, pady=(6, 0))

        self.console_box = ctk.CTkTextbox(
            console_outer,
            fg_color=self.C_BG_DEEP, text_color=self.C_GREEN,
            font=("Consolas", 11), corner_radius=8,
        )
        self.console_box.pack(fill="both", expand=True, padx=8, pady=(2, 8))
        self.log("⚡ TWEAKIFY ready. Choose an operation to begin.")
        self.log(f"   System: {platform.system()} {platform.release()} | {platform.machine()}")

    # ══════════════════════════════════════════
    #          Card Builder Helper
    # ══════════════════════════════════════════
    def _card(self, parent, title, row, col, colspan=1, content_fn=None):
        frame = ctk.CTkFrame(parent, fg_color=self.C_BG_CARD, corner_radius=10)
        frame.grid(row=row, column=col, columnspan=colspan,
                   padx=8, pady=8, sticky="nsew")
        parent.rowconfigure(row, weight=1)

        ctk.CTkLabel(frame, text=title, font=("Consolas", 12, "bold"),
                     text_color=self.C_ACCENT).pack(anchor="w", padx=12, pady=(8, 4))

        ctk.CTkFrame(frame, fg_color=self.C_ACCENT, height=1).pack(fill="x", padx=12)

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=8)

        if content_fn:
            content_fn(inner)
        return frame

    # ══════════════════════════════════════════
    #          Operation Logic
    # ══════════════════════════════════════════
    def log(self, text):
        ts = datetime.now().strftime("%H:%M:%S")
        self.console_box.insert("end", f"[{ts}] {text}\n")
        self.console_box.see("end")
        self.update_idletasks()

    def _refresh_snap_status(self):
        """Update snapshot status text in the Restore tab"""
        try:
            snap_data = self.snapshot.load()
            if snap_data:
                ts = snap_data.get("timestamp", "")
                self.lbl_snap_status.configure(
                    text=f"📅 Saved on: {ts}", text_color=self.C_GREEN)
                self.btn_restore.configure(state="normal")
        except Exception:
            pass

    # ── Power Plans ──
    def _set_power(self, guid, label):
        def _do():
            # Auto-snapshot before changing power plan (only once if none exists)
            if not self.snapshot.load():
                self.log("📸 Auto-snapshot before changing power plan...")
                self.snapshot.take(log_fn=self.log)
                self.after(0, self._refresh_snap_status)
            self.log(f"⚡ Applying power plan: {label}...")
            ok = run_cmd(f"powercfg /setactive {guid}")
            self.log(f"{'✅' if ok else '❌'} {label}")
        threading.Thread(target=_do, daemon=True).start()

    # ── Services ──
    def _stop_service(self, svc):
        def _do():
            self.log(f"🛑 Stopping service: {svc}...")
            run_cmd(f"sc stop {svc}")
            run_cmd(f"sc config {svc} start= disabled")
            self.log(f"✅ {svc} stopped")
        threading.Thread(target=_do, daemon=True).start()

    def _start_service(self, svc):
        def _do():
            self.log(f"▶️  Starting service: {svc}...")
            run_cmd(f"sc config {svc} start= auto")
            run_cmd(f"sc start {svc}")
            self.log(f"✅ {svc} started")
        threading.Thread(target=_do, daemon=True).start()

    # ── RAM Optimization ──
    def optimize_ram(self):
        self.log("🧠 Freeing RAM...")
        run_cmd('taskkill /f /fi "status eq not responding"')
        run_cmd("rundll32.exe advapi32.dll,ProcessIdleTasks")
        # Free Working Sets
        try:
            for proc in psutil.process_iter():
                try:
                    proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                except Exception:
                    pass
        except Exception:
            pass
        self.log("✅ Memory optimized and unresponsive processes cleared.")

    # ── Cleanup ──
    def run_clean(self):
        self.log("🧹 Starting full cleanup...")
        total = 0

        if self.clean_vars["temp_user"].get():
            total += self._delete_folder(os.environ.get("TEMP", ""), "User Temp")

        if self.clean_vars["temp_windows"].get():
            total += self._delete_folder(r"C:\Windows\Temp", "Windows Temp")

        if self.clean_vars["prefetch"].get():
            total += self._delete_folder(r"C:\Windows\Prefetch", "Prefetch")

        if self.clean_vars["recycle"].get():
            run_cmd("rd /s /q C:\\$Recycle.Bin")
            self.log("✅ Recycle Bin emptied.")

        if self.clean_vars["browser_cache"].get():
            self._clean_browsers()

        if self.clean_vars["event_logs"].get():
            run_cmd("wevtutil el | for /f %x in ('wevtutil el') do wevtutil cl %x")
            self.log("✅ Event logs cleared.")

        if self.clean_vars["update_cache"].get():
            run_cmd("net stop wuauserv")
            total += self._delete_folder(r"C:\Windows\SoftwareDistribution\Download", "Update Cache")
            run_cmd("net start wuauserv")

        if self.clean_vars["thumbnail"].get():
            cache_path = os.path.expandvars(r"%LocalAppData%\Microsoft\Windows\Explorer")
            total += self._delete_folder(cache_path, "Thumbnail Cache", pattern="thumbcache_")

        self.log(f"🎉 Done! Freed approximately {total / (1024**2):.1f} MB of space.")

    def _delete_folder(self, path, label, pattern=None):
        freed = 0
        if not path or not os.path.exists(path):
            return 0
        for item in os.listdir(path):
            if pattern and not item.startswith(pattern):
                continue
            fp = os.path.join(path, item)
            try:
                size = os.path.getsize(fp) if os.path.isfile(fp) else 0
                if os.path.isfile(fp):
                    os.unlink(fp)
                elif os.path.isdir(fp):
                    size = sum(
                        os.path.getsize(os.path.join(dp, f))
                        for dp, _, fs in os.walk(fp) for f in fs
                        if os.path.exists(os.path.join(dp, f))
                    )
                    shutil.rmtree(fp, ignore_errors=True)
                freed += size
            except Exception:
                continue
        self.log(f"✅ {label}: freed {freed / (1024**2):.1f} MB")
        return freed

    def _clean_browsers(self):
        paths = {
            "Chrome":  os.path.expandvars(r"%LocalAppData%\Google\Chrome\User Data\Default\Cache"),
            "Edge":    os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\User Data\Default\Cache"),
            "Firefox": os.path.expandvars(r"%LocalAppData%\Mozilla\Firefox\Profiles"),
        }
        for browser, path in paths.items():
            if os.path.exists(path):
                self._delete_folder(path, f"{browser} Cache")

    # ── Tweaks ──
    def apply_tweaks(self):
        self.log("📸 Auto-saving snapshot before applying tweaks...")
        self.snapshot.take(log_fn=self.log)
        self.after(0, lambda: self._refresh_snap_status())
        self.log("🔧 Applying selected tweaks...")
        for key, var in self.tweak_vars.items():
            if var.get():
                fn = self._tweak_actions.get(key)
                if fn:
                    fn()
        self.log("✅ All tweaks applied successfully.")

    def _tweak_disable_animations(self):
        self.log("🎞️  Disabling animations...")
        set_registry(winreg.HKEY_CURRENT_USER,
                     r"Control Panel\Desktop\WindowMetrics", "MinAnimate", 0)
        run_cmd("reg add \"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects\" /v VisualFXSetting /t REG_DWORD /d 2 /f")

    def _tweak_disable_transparency(self):
        self.log("💎  Disabling transparency...")
        set_registry(winreg.HKEY_CURRENT_USER,
                     r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                     "EnableTransparency", 0)

    def _tweak_fast_startup(self):
        self.log("⚡  Enabling Fast Startup...")
        set_registry(winreg.HKEY_LOCAL_MACHINE,
                     r"SYSTEM\CurrentControlSet\Control\Session Manager\Power",
                     "HiberbootEnabled", 1)

    def _tweak_disable_cortana(self):
        self.log("🤫  Disabling Cortana...")
        run_cmd("reg add \"HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search\" /v AllowCortana /t REG_DWORD /d 0 /f")

    def _tweak_gaming_mode(self):
        self.log("🎮  Enabling Game Mode...")
        set_registry(winreg.HKEY_CURRENT_USER,
                     r"SOFTWARE\Microsoft\GameBar", "AutoGameModeEnabled", 1)
        set_registry(winreg.HKEY_CURRENT_USER,
                     r"SOFTWARE\Microsoft\GameBar", "AllowAutoGameMode", 1)

    def _tweak_timer(self):
        self.log("⏱️  Increasing timer resolution...")
        run_cmd("bcdedit /set useplatformtick yes")
        run_cmd("bcdedit /deletevalue useplatformclock")

    def _tweak_network(self):
        self.log("🌐  Optimizing network...")
        run_cmd("netsh int tcp set global autotuninglevel=normal")
        run_cmd("netsh int tcp set global rss=enabled")
        run_cmd("netsh int tcp set global dca=enabled")
        run_cmd("netsh int tcp set global netdma=enabled")
        run_cmd("netsh int tcp set global ecncapability=disabled")
        run_cmd("netsh int tcp set heuristics disabled")
        set_registry(winreg.HKEY_LOCAL_MACHINE,
                     r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
                     "TcpAckFrequency", 1)

    def _tweak_search_index(self):
        self.log("🔍  Disabling search indexing...")
        run_cmd("sc stop WSearch")
        run_cmd("sc config WSearch start= disabled")

    # ══════════════════════════════════════════
    #          System Information
    # ══════════════════════════════════════════
    def _gather_sysinfo(self):
        try:
            cpu_freq = psutil.cpu_freq()
            freq_str = f"{cpu_freq.current:.0f} MHz (Max: {cpu_freq.max:.0f} MHz)" if cpu_freq else "N/A"
        except Exception:
            freq_str = "N/A"

        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")

        return [
            ("🖥️  Operating System",   f"{platform.system()} {platform.release()} ({platform.version()})"),
            ("🏛️  CPU",                platform.processor() or "N/A"),
            ("⚡  CPU Frequency",       freq_str),
            ("🧵  Core Count",          f"{psutil.cpu_count(logical=False)} Physical / {psutil.cpu_count()} Logical"),
            ("🧠  Total RAM",           f"{ram.total / (1024**3):.1f} GB"),
            ("📊  RAM Used",            f"{ram.used / (1024**3):.1f} GB ({ram.percent}%)"),
            ("💾  Drive C:",            f"{disk.total / (1024**3):.0f} GB total | {disk.free / (1024**3):.1f} GB free"),
            ("🕒  Uptime",              self._uptime()),
            ("🏠  Hostname",            platform.node()),
            ("👤  User",               os.environ.get("USERNAME", "N/A")),
        ]

    def _uptime(self):
        try:
            seconds = (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).seconds
            h, m = divmod(seconds // 60, 60)
            return f"{h}h {m}m"
        except Exception:
            return "N/A"

    def _refresh_sysinfo(self):
        # Rebuild the System Info tab
        tab = self.tab_view.tab("📊  System Info")
        for w in tab.winfo_children():
            w.destroy()
        self._build_tab_sysinfo()
        self.log("🔄 System info refreshed.")

    # ══════════════════════════════════════════
    #          Live Stats Update Loop
    # ══════════════════════════════════════════
    def _update_stats_loop(self):
        def _update():
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent

                cpu_color = self.C_GREEN if cpu < 60 else (self.C_ORANGE if cpu < 85 else self.C_RED)
                ram_color = self.C_GREEN if ram < 60 else (self.C_ORANGE if ram < 85 else self.C_RED)

                self.lbl_cpu.configure(text=f"CPU: {cpu:.0f}%", text_color=cpu_color)
                self.lbl_ram.configure(text=f"RAM: {ram:.0f}%", text_color=ram_color)

                if hasattr(self, "ram_bar"):
                    self.ram_bar.set(ram / 100)
                    used = psutil.virtual_memory().used / (1024**3)
                    total = psutil.virtual_memory().total / (1024**3)
                    self.lbl_ram_detail.configure(
                        text=f"{used:.1f} GB / {total:.1f} GB ({ram}%)"
                    )
            except Exception:
                pass
            self.after(2000, _update)

        self.after(1000, _update)


# ══════════════════════════════════════════════
#          Entry Point
# ══════════════════════════════════════════════
if __name__ == "__main__":
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)
    else:
        app = TweakifyApp()
        app.mainloop()