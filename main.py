import threading
import time
import customtkinter as ctk
import serial.tools.list_ports  # Dynamic COM port scanner
from pymodbus.client import ModbusSerialClient


# --- GUI Application ---
class PowerSupplyGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Settings
        self.title("Sky Toppower Control Center")
        self.geometry("450x700")  # Resized to neatly fit new drop-downs
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.client = None  # Instantiated dynamically on connection
        self.connected = False
        self.output_on = False
        self.running_monitor = False

        # --- UI LAYOUT ---

        # Title Label
        self.title_label = ctk.CTkLabel(self, text="STP2S3010E22 Control", font=ctk.CTkFont(size=22, weight="bold"))
        self.title_label.pack(pady=20)

        # Connection Configuration Frame
        self.conn_frame = ctk.CTkFrame(self)
        self.conn_frame.pack(pady=10, fill="x", padx=20)

        # Drop-down for COM port selection
        ctk.CTkLabel(self.conn_frame, text="COM Port:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.port_combobox = ctk.CTkComboBox(self.conn_frame, values=["None"], width=120)
        self.port_combobox.grid(row=0, column=1, padx=5, pady=10)

        # Refresh button next to drop-down
        self.refresh_btn = ctk.CTkButton(self.conn_frame, text="🔄", width=35, command=self.refresh_com_ports)
        self.refresh_btn.grid(row=0, column=2, padx=5, pady=10)

        # Connect Button
        self.conn_btn = ctk.CTkButton(self.conn_frame, text="Connect Device", command=self.toggle_connection,
                                      fg_color="#2b719e", width=120)
        self.conn_btn.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # Status Label
        self.status_lbl = ctk.CTkLabel(self.conn_frame, text="Status: Disconnected", text_color="#e06666",
                                       font=ctk.CTkFont(weight="bold"))
        self.status_lbl.grid(row=1, column=2, padx=10, pady=10, sticky="e")

        # Readout Displays (Live Metrics)
        self.readout_frame = ctk.CTkFrame(self, fg_color="#1e1e1e")
        self.readout_frame.pack(pady=15, fill="x", padx=20)

        self.volt_display = ctk.CTkLabel(self.readout_frame, text="0.00 V", font=ctk.CTkFont(size=36, weight="bold"),
                                         text_color="#67c23a")
        self.volt_display.pack(pady=(15, 2))

        self.curr_display = ctk.CTkLabel(self.readout_frame, text="0.00 A", font=ctk.CTkFont(size=28, weight="bold"),
                                         text_color="#e6a23c")
        self.curr_display.pack(pady=(2, 2))

        # Mode Indicator (CV / CC)
        self.mode_display = ctk.CTkLabel(self.readout_frame, text="MODE: OFF", font=ctk.CTkFont(size=14, weight="bold"),
                                         text_color="#909399")
        self.mode_display.pack(pady=(2, 15))

        # Controls Input Frame
        self.ctrl_frame = ctk.CTkFrame(self)
        self.ctrl_frame.pack(pady=10, fill="x", padx=20)

        # Voltage Input
        ctk.CTkLabel(self.ctrl_frame, text="Target Voltage (V):").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.volt_input = ctk.CTkEntry(self.ctrl_frame, placeholder_text="0.00", width=120)
        self.volt_input.grid(row=0, column=1, padx=10, pady=10)
        self.volt_set_btn = ctk.CTkButton(self.ctrl_frame, text="Apply", width=80, command=self.apply_voltage,
                                          state="disabled")
        self.volt_set_btn.grid(row=0, column=2, padx=10, pady=10)

        # Current Input
        ctk.CTkLabel(self.ctrl_frame, text="Current Limit (A):").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.curr_input = ctk.CTkEntry(self.ctrl_frame, placeholder_text="0.00", width=120)
        self.curr_input.grid(row=1, column=1, padx=10, pady=10)
        self.curr_set_btn = ctk.CTkButton(self.ctrl_frame, text="Apply", width=80, command=self.apply_current,
                                          state="disabled")
        self.curr_set_btn.grid(row=1, column=2, padx=10, pady=10)

        # Protection Features Frame (OCP Switch)
        self.prot_frame = ctk.CTkFrame(self)
        self.prot_frame.pack(pady=10, fill="x", padx=20)

        self.ocp_switch = ctk.CTkSwitch(self.prot_frame, text="Enable OCP (Over-Current Protection)",
                                        command=self.toggle_ocp, state="disabled")
        self.ocp_switch.pack(padx=20, pady=15, anchor="w")

        # Output Toggle Button
        self.output_btn = ctk.CTkButton(self, text="⚡ OUTPUT ON", height=50, font=ctk.CTkFont(size=16, weight="bold"),
                                        fg_color="#3a3a3a", state="disabled", command=self.toggle_output)
        self.output_btn.pack(pady=20, fill="x", padx=20)

        # Scan for ports immediately upon opening application
        self.refresh_com_ports()

        # Safely shut down when closing window
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # --- PORT MANAGEMENT ---

    def refresh_com_ports(self):
        """Scans the operating system for physical/virtual serial ports."""
        ports = [port.device for port in serial.tools.list_ports.comports()]

        if ports:
            self.port_combobox.configure(values=ports)
            self.port_combobox.set(ports[0])
        else:
            self.port_combobox.configure(values=["None Found"])
            self.port_combobox.set("None Found")

    # --- ACTION METHODS ---

    def toggle_connection(self):
        if not self.connected:
            selected_port = self.port_combobox.get()

            if selected_port in ["None Found", "None"]:
                self.status_lbl.configure(text="Status: No Port Selected", text_color="#f56c6c")
                return

            self.client = ModbusSerialClient(
                port=selected_port,
                baudrate=9600,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1
            )

            if self.client.connect():
                self.connected = True
                self.status_lbl.configure(text="Status: Connected", text_color="#67c23a")
                self.conn_btn.configure(text="Disconnect", fg_color="#909399")
                self.port_combobox.configure(state="disabled")
                self.refresh_btn.configure(state="disabled")

                # Enable UI Controls
                self.volt_set_btn.configure(state="normal")
                self.curr_set_btn.configure(state="normal")
                self.ocp_switch.configure(state="normal")
                self.output_btn.configure(state="normal", fg_color="#67c23a")

                # Start background monitor loop thread safely
                self.running_monitor = True
                threading.Thread(target=self.monitor_loop, daemon=True).start()
            else:
                self.status_lbl.configure(text="Status: Connection Failed", text_color="#f56c6c")
        else:
            self.disconnect_device()

    def disconnect_device(self):
        self.running_monitor = False
        time.sleep(0.2)
        if self.connected and self.client:
            self.set_output_state(False)
            self.client.close()

        self.connected = False
        self.status_lbl.configure(text="Status: Disconnected", text_color="#e06666")
        self.conn_btn.configure(text="Connect Device", fg_color="#2b719e")
        self.port_combobox.configure(state="normal")
        self.refresh_btn.configure(state="normal")

        # Disable Controls & Clear Displays
        self.volt_set_btn.configure(state="disabled")
        self.curr_set_btn.configure(state="disabled")
        self.ocp_switch.configure(state="disabled")
        self.output_btn.configure(state="disabled", fg_color="#3a3a3a", text="⚡ OUTPUT ON")
        self.volt_display.configure(text="0.00 V")
        self.curr_display.configure(text="0.00 A")
        self.mode_display.configure(text="MODE: OFF", text_color="#909399")
        self.volt_input.configure(placeholder_text="0.00")
        self.curr_input.configure(placeholder_text="0.00")

    def toggle_output(self):
        self.set_output_state(not self.output_on)

    def set_output_state(self, turn_on):
        if not self.connected or not self.client: return
        val = 1 if turn_on else 0
        res = self.client.write_register(address=0x0001, value=val, device_id=1)
        if not res.isError():
            self.output_on = turn_on
            if self.output_on:
                self.output_btn.configure(text="🛑 STOP OUTPUT", fg_color="#d9534f")
            else:
                self.output_btn.configure(text="⚡ OUTPUT ON", fg_color="#67c23a")
                self.mode_display.configure(text="MODE: OFF", text_color="#909399")

    def apply_voltage(self):
        if not self.client: return
        try:
            val = float(self.volt_input.get())
            raw_val = int(val * 100)
            self.client.write_register(address=0x0030, value=raw_val, device_id=1)
            self.volt_input.delete(0, 'end')  # Clear entry on successful submission
        except ValueError:
            pass

    def apply_current(self):
        if not self.client: return
        try:
            val = float(self.curr_input.get())
            raw_val = int(val * 1000)  # Corrected multiplier scaling factor
            self.client.write_register(address=0x0031, value=raw_val, device_id=1)
            self.curr_input.delete(0, 'end')  # Clear entry on successful submission
        except ValueError:
            pass

    def toggle_ocp(self):
        if not self.connected or not self.client: return
        switch_val = self.ocp_switch.get()
        self.client.write_register(address=0x0043, value=switch_val, device_id=1)

    # --- BACKGROUND TELEMETRY LOOP ---
    def monitor_loop(self):
        """Asks device for telemetry data seamlessly in the background"""
        while self.running_monitor:
            if self.connected and self.client:

                # 1. Read Live Metrics (Volt & Current from 0x0010)
                res_metrics = self.client.read_holding_registers(address=0x0010, count=2, device_id=1)

                # 2. Read PS Status Register (0x0002) for CV/CC mode monitoring
                res_status = self.client.read_holding_registers(address=0x0002, count=1, device_id=1)

                # 3. Read Output Status (0x0001) and OCP Status (0x0043)
                res_output = self.client.read_holding_registers(address=0x0001, count=1, device_id=1)
                res_ocp = self.client.read_holding_registers(address=0x0043, count=1, device_id=1)

                # 4. Read Active Target Voltage and Current parameters (0x0030 & 0x0031)
                res_targets = self.client.read_holding_registers(address=0x0030, count=2, device_id=1)

                # Update live metrics displays
                if not res_metrics.isError() and len(res_metrics.registers) >= 2:
                    v = res_metrics.registers[0] / 100.0
                    i = res_metrics.registers[1] / 1000.0  # Synced to match current multiplier fix
                    self.volt_display.configure(text=f"{v:.2f} V")
                    self.curr_display.configure(text=f"{i:.2f} A")

                # Dynamically monitor and update text entry placeholders based on target values
                if not res_targets.isError() and len(res_targets.registers) >= 2:
                    target_v = res_targets.registers[0] / 100.0
                    target_i = res_targets.registers[1] / 1000.0
                    self.volt_input.configure(placeholder_text=f"{target_v:.2f}")
                    self.curr_input.configure(placeholder_text=f"{target_i:.2f}")

                # Sync Output Status Button UI dynamically from hardware state
                if not res_output.isError() and len(res_output.registers) >= 1:
                    hardware_output_on = bool(res_output.registers[0])
                    if hardware_output_on != self.output_on:
                        self.output_on = hardware_output_on
                        if self.output_on:
                            self.output_btn.configure(text="🛑 STOP OUTPUT", fg_color="#d9534f")
                        else:
                            self.output_btn.configure(text="⚡ OUTPUT ON", fg_color="#67c23a")
                            self.mode_display.configure(text="MODE: OFF", text_color="#909399")

                # Sync CC/CV Mode Display
                if not res_status.isError() and len(res_status.registers) >= 1 and self.output_on:
                    status_word = res_status.registers[0]
                    is_cc_mode = (status_word >> 6) & 1

                    if is_cc_mode:
                        self.mode_display.configure(text="MODE: CC (Constant Current)", text_color="#e6a23c")
                    else:
                        self.mode_display.configure(text="MODE: CV (Constant Voltage)", text_color="#67c23a")

                # Sync OCP Switch UI dynamically from hardware state
                if not res_ocp.isError() and len(res_ocp.registers) >= 1:
                    hardware_ocp_on = res_ocp.registers[0]

                    if hardware_ocp_on != self.ocp_switch.get():
                        if hardware_ocp_on == 1:
                            self.ocp_switch.select()
                        else:
                            self.ocp_switch.deselect()

            time.sleep(0.5)

    def on_close(self):
        self.disconnect_device()
        self.destroy()


if __name__ == "__main__":
    app = PowerSupplyGUI()
    app.mainloop()