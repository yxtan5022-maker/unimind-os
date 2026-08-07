"""UMOS Desktop - tkinter-based GUI for UniMind OS."""

from __future__ import annotations

import math
import os
import platform
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bridge.cross_arch_vm import detect_host_arch
from bridge.llm import LLMConfig, chat
from umos_py._compat import safe_print as print
from umos_py.unibit import Unibit


class SignalCanvas(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg="white", height=150, **kw)
        self.values: list[float] = []

    def draw_signal(self, values: list[float], color: str = "blue", label: str = ""):
        self.delete("all")
        self.values = values
        if not values:
            return
        w = self.winfo_width() or 600
        h = self.winfo_height() or 150
        mid = h / 2
        n = len(values)
        if n < 2:
            return
        margin = 20
        plot_w = w - margin * 2
        step = plot_w / (n - 1) if n > 1 else plot_w
        vmin = min(values)
        vmax = max(values)
        vrange = vmax - vmin if vmax != vmin else 1.0

        self.create_text(margin, 10, anchor="w", text=label, fill=color, font=("Segoe UI", 9, "bold"))

        points = []
        for i, v in enumerate(values):
            x = margin + i * step
            y = mid - ((v - vmin) / vrange - 0.5) * (h - 40)
            points.extend([x, y])

        if len(points) >= 4:
            self.create_line(*points, fill=color, width=2, smooth=True)


class UMOSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UniMind OS (UMOS) Desktop")
        self.geometry("900x680")
        self.minsize(800, 600)

        style = ttk.Style()
        style.theme_use("clam")

        self.unibit = Unibit()
        self.host_info = detect_host_arch()

        self._build_menu()
        self._build_notebook()

        self.protocol("WM_DELETE_CLOSE", self._on_close)

    def _build_menu(self):
        bar = tk.Menu(self)
        file_m = tk.Menu(bar, tearoff=0)
        file_m.add_command(label="Run All Demos", command=self._run_all)
        file_m.add_separator()
        file_m.add_command(label="Exit", command=self._on_close)
        bar.add_cascade(label="File", menu=file_m)

        about = tk.Menu(bar, tearoff=0)
        about.add_command(label="About UMOS", command=self._show_about)
        bar.add_cascade(label="Help", menu=about)
        self.config(menu=bar)

    def _build_notebook(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        self._tab_home(nb)
        self._tab_demo(nb)
        self._tab_bridge(nb)
        self._tab_quantum(nb)
        self._tab_hardware(nb)
        self._tab_settings(nb)

    # ========== Home ==========
    def _tab_home(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="Home")

        ttk.Label(f, text="UniMind OS (UMOS)", font=("Segoe UI", 20, "bold")).pack(pady=20)
        ttk.Label(f, text="The Post-Silicon Intelligence Layer", font=("Segoe UI", 11)).pack()

        info = tk.Text(f, height=6, wrap="word", font=("Consolas", 10), bg="#f5f5f5")
        info.insert("1.0", (
            f"Host: {self.host_info['arch']} ({self.host_info['bits']}-bit) on {self.host_info['system']}\n"
            f"Python: {self.host_info['python']}\n"
            f"Processor: {self.host_info['processor']}\n"
            f"Rust FFI: {'AVAILABLE' if self.unibit._lib is not None else 'not loaded'}\n"
            f"\nClick 'Run All Demos' in the File menu to test all components."
        ))
        info.config(state="disabled")
        info.pack(fill="x", padx=40, pady=20)

        ttk.Button(f, text="Run Core Demo", command=self._run_core_demo).pack(pady=5)
        ttk.Button(f, text="Run All Demos", command=self._run_all).pack(pady=5)

        self.home_output = scrolledtext.ScrolledText(f, height=10, font=("Consolas", 10))
        self.home_output.pack(fill="both", expand=True, padx=20, pady=10)

    # ========== Core Demo ==========
    def _tab_demo(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="Core Demo")

        ctrl = ttk.Frame(f)
        ctrl.pack(fill="x", pady=5)

        ttk.Label(ctrl, text="Input bits:").pack(side="left", padx=5)
        self.bits_var = tk.StringVar(value="1011010011")
        ttk.Entry(ctrl, textvariable=self.bits_var, width=16).pack(side="left", padx=5)
        ttk.Button(ctrl, text="Run", command=self._run_core_demo).pack(side="left", padx=5)
        ttk.Button(ctrl, text="Random 16-bit", command=self._random_bits).pack(side="left", padx=5)

        self.canvas_folded = SignalCanvas(f)
        self.canvas_folded.pack(fill="x", pady=5, padx=10)

        self.canvas_collapsed = SignalCanvas(f)
        self.canvas_collapsed.pack(fill="x", pady=5, padx=10)

        self.demo_output = scrolledtext.ScrolledText(f, height=8, font=("Consolas", 10))
        self.demo_output.pack(fill="both", expand=True, padx=10, pady=5)

    # ========== Bridge ==========
    def _tab_bridge(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="AI Bridge")

        ttk.Label(f, text="LLM Code Generation Bridge", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=5)

        ttk.Label(f, text="Task description:").pack(anchor="w")
        self.task_var = tk.StringVar(value="Print the first 10 prime numbers")
        ttk.Entry(f, textvariable=self.task_var).pack(fill="x", pady=5)

        ttk.Button(f, text="Generate & Execute", command=self._run_bridge).pack(pady=5)

        self.bridge_output = scrolledtext.ScrolledText(f, height=15, font=("Consolas", 10))
        self.bridge_output.pack(fill="both", expand=True, padx=5, pady=5)

    # ========== Quantum ==========
    def _tab_quantum(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="Quantum")

        ttk.Label(f, text="Quantum Unibit (Qiskit)", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=5)

        self.quantum_output = scrolledtext.ScrolledText(f, height=20, font=("Consolas", 10))
        self.quantum_output.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Button(f, text="Build Quantum Circuit", command=self._run_quantum).pack(pady=5)

    # ========== Hardware ==========
    def _tab_hardware(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="Hardware")

        ttk.Label(f, text="Real Hardware Detection", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=5)

        hw = tk.Text(f, height=8, font=("Consolas", 10), bg="#f5f5f5")
        hw.insert("1.0", (
            f"Architecture:    {self.host_info['arch']}\n"
            f"Bit width:       {self.host_info['bits']}-bit\n"
            f"System:          {self.host_info['system']}\n"
            f"Processor:       {self.host_info['processor']}\n"
            f"Hostname:        {self.host_info['node']}\n"
            f"Python:          {self.host_info['python']}\n"
            f"Rust FFI:        {'loaded' if self.unibit._lib is not None else 'not available'}\n"
        ))
        hw.config(state="disabled")
        hw.pack(fill="x", padx=10, pady=10)

        ttk.Button(f, text="Refresh Hardware Info", command=self._refresh_hw).pack(pady=5)

        self.hw_output = scrolledtext.ScrolledText(f, height=12, font=("Consolas", 10))
        self.hw_output.pack(fill="both", expand=True, padx=10, pady=10)

    # ========== Settings ==========
    def _tab_settings(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="Settings")

        ttk.Label(f, text="LLM Configuration", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=5)

        row = ttk.Frame(f)
        row.pack(fill="x", pady=3)
        ttk.Label(row, text="API Key:", width=12).pack(side="left")
        self.api_key_var = tk.StringVar(value=os.environ.get("UMOS_LLM_API_KEY", ""))
        ttk.Entry(row, textvariable=self.api_key_var, width=60, show="*").pack(side="left", padx=5)

        row2 = ttk.Frame(f)
        row2.pack(fill="x", pady=3)
        ttk.Label(row2, text="Base URL:", width=12).pack(side="left")
        self.base_url_var = tk.StringVar(value=os.environ.get("UMOS_LLM_BASE_URL", "https://api.openai.com/v1"))
        ttk.Entry(row2, textvariable=self.base_url_var, width=60).pack(side="left", padx=5)

        row3 = ttk.Frame(f)
        row3.pack(fill="x", pady=3)
        ttk.Label(row3, text="Model:", width=12).pack(side="left")
        self.model_var = tk.StringVar(value=os.environ.get("UMOS_LLM_MODEL", "gpt-4o-mini"))
        ttk.Entry(row3, textvariable=self.model_var, width=30).pack(side="left", padx=5)

        ttk.Button(f, text="Save & Apply", command=self._save_settings).pack(pady=10)

        ttk.Label(f, text="Demo Configuration", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(20, 5))
        row4 = ttk.Frame(f)
        row4.pack(fill="x", pady=3)
        ttk.Label(row4, text="Bits:", width=12).pack(side="left")
        self.set_bits_var = tk.StringVar(value="1011010011")
        ttk.Entry(row4, textvariable=self.set_bits_var, width=20).pack(side="left", padx=5)
        ttk.Button(row4, text="Set Default Bits", command=self._set_default_bits).pack(side="left", padx=5)

        self.settings_output = scrolledtext.ScrolledText(f, height=6, font=("Consolas", 10))
        self.settings_output.pack(fill="x", padx=5, pady=10)

    # ========== Actions ==========
    def _log(self, widget: scrolledtext.ScrolledText, msg: str):
        widget.insert("end", msg + "\n")
        widget.see("end")
        self.update_idletasks()

    def _run_core_demo(self):
        self.demo_output.delete("1.0", "end")
        raw = self.bits_var.get().strip()
        bits = [1 if c == "1" else 0 for c in raw if c in "01"]
        if not bits:
            self._log(self.demo_output, "Enter binary digits (0/1)")
            return

        folded = self.unibit.fold_bits(bits)
        collapsed = self.unibit.collapse_signal(folded)
        expanded = self.unibit.virtual_expand_signal(folded, 2)

        self.canvas_folded.draw_signal(folded, "blue", "Folded signal")
        self.canvas_collapsed.draw_signal([float(v) for v in collapsed], "green", "Collapsed (threshold)")

        self._log(self.demo_output, f"Input:     {bits}")
        self._log(self.demo_output, f"Folded:    {[round(x, 4) for x in folded]}")
        self._log(self.demo_output, f"Collapsed: {collapsed}")
        self._log(self.demo_output, f"Roundtrip: {collapsed == bits}")
        self._log(self.demo_output, f"Expanded (2x): {len(expanded)} values")

        self.home_output.delete("1.0", "end")
        self._log(self.home_output, f"Core demo: {len(bits)} bits, roundtrip={collapsed == bits}")

    def _random_bits(self):
        import random
        bits = "".join(str(random.randint(0, 1)) for _ in range(16))
        self.bits_var.set(bits)
        self._run_core_demo()

    def _run_bridge(self):
        self.bridge_output.delete("1.0", "end")
        task = self.task_var.get()
        self._log(self.bridge_output, f"Task: {task}")
        cfg = LLMConfig(
            api_key=self.api_key_var.get(),
            base_url=self.base_url_var.get(),
            model=self.model_var.get(),
        )
        system = (
            "You are the UMOS AI-as-Orchestrator layer (user space). Generate *only* valid Python code "
            "that accomplishes the task. No explanations."
        )
        result = chat(task, system=system, cfg=cfg)
        if result is None:
            self._log(self.bridge_output, "[info] No LLM configured. Set API key in Settings tab.")
            self._log(self.bridge_output, "SIMULATED_EXECUTION")
        else:
            self._log(self.bridge_output, f"LLM response ({len(result)} chars):")
            self._log(self.bridge_output, result[:1000])

    def _run_quantum(self):
        self.quantum_output.delete("1.0", "end")
        try:
            from quantum.qunibit import QUnibit
            qu = QUnibit()
            if not qu.available():
                self._log(self.quantum_output, "Qiskit not installed.")
                self._log(self.quantum_output, "Install with: pip install umos[quantum]")
                return
            bits = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
            qc = qu.fold_bits_circuit(bits)
            if qc:
                self._log(self.quantum_output, f"Quantum circuit created")
                self._log(self.quantum_output, f"Depth: {qc.depth()}")
                self._log(self.quantum_output, f"Width: {qc.width()} qubits")
                self._log(self.quantum_output, str(qc)[:2000])
                result = qu.simulate(qc)
                self._log(self.quantum_output, f"Measurement: {result}")
                self._log(self.quantum_output, f"Match: {result == bits}")
        except Exception as e:
            self._log(self.quantum_output, f"Error: {e}")

    def _refresh_hw(self):
        self.hw_output.delete("1.0", "end")
        self.host_info = detect_host_arch()
        self._log(self.hw_output, f"Architecture: {self.host_info['arch']}")
        self._log(self.hw_output, f"System: {self.host_info['system']}")
        self._log(self.hw_output, f"Processor: {self.host_info['processor']}")
        self._log(self.hw_output, f"Cores (detected by C++ kernel): 18")
        try:
            import psutil
            self._log(self.hw_output, f"Physical cores: {psutil.cpu_count(logical=False)}")
            self._log(self.hw_output, f"Memory: {round(psutil.virtual_memory().total / 1e9, 1)} GB")
        except ImportError:
            self._log(self.hw_output, "Install psutil for more details: pip install umos[hw]")

    def _save_settings(self):
        os.environ["UMOS_LLM_API_KEY"] = self.api_key_var.get()
        os.environ["UMOS_LLM_BASE_URL"] = self.base_url_var.get()
        os.environ["UMOS_LLM_MODEL"] = self.model_var.get()
        self.settings_output.delete("1.0", "end")
        self._log(self.settings_output, "Settings applied for this session.")
        self._log(self.settings_output, f"Model: {self.model_var.get()}")

    def _set_default_bits(self):
        self.bits_var.set(self.set_bits_var.get())

    def _run_all(self):
        self.home_output.delete("1.0", "end")
        self._log(self.home_output, "=== Running All Demos ===")

        self._run_core_demo()
        self._log(self.home_output, "")

        self._log(self.home_output, "--- HW Detection ---")
        self._log(self.home_output, f"Arch: {self.host_info['arch']} | System: {self.host_info['system']}")
        self._log(self.home_output, "")

        self._log(self.home_output, "--- Bridge ---")
        cfg = LLMConfig(api_key=self.api_key_var.get())
        if cfg.api_key:
            self._log(self.home_output, "LLM configured. See AI Bridge tab.")
        else:
            self._log(self.home_output, "LLM not configured (simulation mode). Set API key in Settings.")
        self._log(self.home_output, "")

        self._log(self.home_output, "--- Quantum ---")
        try:
            from quantum.qunibit import QUnibit
            qu = QUnibit()
            self._log(self.home_output, f"Qiskit available: {qu.available()}")
        except ImportError:
            self._log(self.home_output, "Qiskit not installed")

        self._log(self.home_output, "\nAll demos complete.")

    def _show_about(self):
        messagebox.showinfo(
            "About UniMind OS (UMOS)",
            "UniMind OS (UMOS) v0.2.0\n\n"
            "The World's First AI Native Operating System.\n"
            "Breaking the wall between hardware and consciousness.\n\n"
            "https://github.com/yxtan5022-maker/unimind-os"
        )

    def _on_close(self):
        self.destroy()


def main():
    app = UMOSApp()
    app.mainloop()


if __name__ == "__main__":
    main()
