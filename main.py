import sys
import struct
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QLineEdit, QCheckBox, QFileDialog, QMessageBox, QComboBox, QGroupBox

class Replay:
    FILE_SIG = bytes([0x53, 0x73, 0x2A, 0x52])
    CURRENT_SV = 4

    def __init__(self):
        self.debug = False
        self.file = None
        self.loaded = False
        self.read_start_offset = 0
        self.debug_txt = {}

        # Initialize replay data attributes
        self.unique_id = ""
        self.replay_id = ""
        self.pb_str = ""
        self.approach_rate = 0.0
        self.spawn_distance = 0.0
        self.fade_length = 0.0
        self.parallax = 0.0
        self.ui_parallax = 0.0
        self.grid_parallax = 0.0
        self.fov = 0.0
        self.cam_unlock = False
        self.edge_drift = 0.0
        self.additional_data = b''
        self.mods = ""
        self.speed = ""

    def replay_error(self, txt):
        if self.debug:
        # Handle error (implementation dependent on the specific application)
            print(f"Error: {txt}")

    def update_debug_text(self):
        if self.debug:
            debug_txt = "-- replay debug --\n"
            for k, v in self.debug_txt.items():
                debug_txt += f"{k}: {v}\n"
            if self.debug:
                print(debug_txt)

    def read_data(self, from_path=""):
        if self.debug:
            print("Reading data")
        self.loaded = False  # Ensure reset before reading new data
        if self.debug:
            self.update_debug_text()

        try:
            with open(from_path, 'rb') as file:
                self.file = file
                self._read_replay_file()
        except IOError as e:
            self.replay_error(str(e))

    def _read_replay_file(self):
        if self.file:
            sig = self.file.read(4)
            if sig != self.FILE_SIG:
                self.replay_error("Invalid file signature")
                return

            self.sv = struct.unpack('H', self.file.read(2))[0]
            self.file.read(8)  # Skipping unused bytes

            self.unique_id = self.file.readline().strip().decode('utf-8')
            self.replay_id = self.file.readline().strip().decode('utf-8')
            self.pb_str = self.file.readline().strip().decode('utf-8')

            # Reading additional data
            self.approach_rate = self._read_float()
            self.spawn_distance = self._read_float()
            self.fade_length = self._read_float()
            self.parallax = self._read_float()
            self.hitbox = self._parse_pb_str("hbox", 1.0)
            self.hit_window = self._parse_pb_str("hitw", 58)
            self.ui_parallax = self._read_float()
            self.grid_parallax = self._read_float()
            self.fov = self._read_float()
            self.cam_unlock = struct.unpack('B', self.file.read(1))[0] == 1
            self.edge_drift = self._read_float()

            # Read the rest of the file
            self.additional_data = self.file.read()

            if self.debug:
                print(f"Unique ID: {self.unique_id}")
                print(f"Replay ID: {self.replay_id}")
                print(f"PB String: {self.pb_str}")
                print(f"Approach Rate: {self.approach_rate}")
                print(f"Spawn Distance: {self.spawn_distance}")
                print(f"Fade Length: {self.fade_length}")
                print(f"Parallax: {self.parallax}")
                print(f"Hitbox: {self.hitbox}")
                print(f"Hit Window: {self.hit_window}")
                print(f"UI Parallax: {self.ui_parallax}")
                print(f"Grid Parallax: {self.grid_parallax}")
                print(f"FOV: {self.fov}")
                print(f"Camera Unlock: {self.cam_unlock}")
                print(f"Edge Drift: {self.edge_drift}")
                print("Replay data read successfully")

            # Parse mods from pb_str
            self.mods = self.pb_str
            self.speed = self._parse_speed(self.pb_str)

            self.loaded = True

    def _parse_pb_str(self, key, default):
        for part in self.pb_str.split(";"):
            if part.startswith(f"{key}:"):
                return float(part.split(":")[1])
        return default

    def _read_float(self):
        value = struct.unpack('f', self.file.read(4))[0]
        if self.debug:
            print(f"Read float value: {value}")
        return value

    def _write_float(self, value):
        return struct.pack('f', value)

    def _parse_speed(self, pb_str):
        for part in pb_str.split(";"):
            if part.startswith("s:"):
                return part[2:]
        return ""

    def save_data(self, to_path=""):
        if self.debug:
            print("Saving data")
        if self.loaded:
            try:
                with open(to_path, 'wb') as file:
                    file.write(self.FILE_SIG)
                    file.write(struct.pack('H', self.sv))
                    file.write(b'\x00' * 8)  # Writing 8 unused bytes

                    file.write(f"{self.unique_id}\n".encode('utf-8'))
                    file.write(f"{self.replay_id}\n".encode('utf-8'))

                    # Rebuild pb_str with updated mods and speed
                    pb_str_parts = [part for part in self.pb_str.split(";") if not part.startswith("m_") and not part.startswith("s:")]
                    if self.mods:
                        pb_str_parts.append(self.mods)
                    if self.speed:
                        pb_str_parts.append(f"s:{self.speed}")
                    file.write(f"{';'.join(pb_str_parts)}\n".encode('utf-8'))

                    file.write(self._write_float(self.approach_rate))
                    file.write(self._write_float(self.spawn_distance))
                    file.write(self._write_float(self.fade_length))
                    file.write(self._write_float(self.parallax))
                    file.write(self._write_float(self.ui_parallax))
                    file.write(self._write_float(self.grid_parallax))
                    file.write(self._write_float(self.fov))
                    file.write(struct.pack('B', 1 if self.cam_unlock else 0))
                    file.write(self._write_float(self.edge_drift))

                    # Write the rest of the original data
                    file.write(self.additional_data)

                    if self.debug:
                        print("Replay data saved successfully")
            except IOError as e:
                self.replay_error(str(e))

    def _get_speed_multiplier(self, speed):
        speed_mapping = {
            "---": 0.75,
            "--": 0.8,
            "-": 0.85,
            "+": 1.15,
            "++": 1.25,
            "+++": 1.35,
            "++++": 1.45
        }
        return 1.0 / speed_mapping.get(speed, 1.0)

    # Setters for changing replay data
    def set_approach_rate(self, value):
        self.approach_rate = value

    def set_spawn_distance(self, value):
        self.spawn_distance = value

    def set_fade_length(self, value):
        self.fade_length = value

    def set_parallax(self, value):
        self.parallax = value

    def set_ui_parallax(self, value):
        self.ui_parallax = value

    def set_grid_parallax(self, value):
        self.grid_parallax = value

    def set_fov(self, value):
        self.fov = value

    def set_cam_unlock(self, value):
        self.cam_unlock = value

    def set_edge_drift(self, value):
        self.edge_drift = value

    def set_speed(self, value):
        speed_mapping = {
            "Normal (1.0)": "=",
            "Speed --- (0.75)": "---",
            "Speed -- (0.8)": "--",
            "Speed - (0.85)": "-",
            "Speed + (1.15)": "+",
            "Speed ++ (1.25)": "++",
            "Speed +++ (1.35)": "+++",
            "Speed ++++ (1.45)": "++++"
        }
        self.speed = speed_mapping.get(value, "")

    # Methods for modifying mods
    def add_mod(self, mod):
        if mod not in self.mods:
            self.mods += f";{mod}"
            if self.debug:
                print(f"Added mod: {mod}")

    def remove_mod(self, mod):
        if mod in self.mods:
            self.mods = self.mods.replace(f";{mod}", "")
            if self.debug:
                print(f"Removed mod: {mod}")

class ReplayEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.replay = Replay()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Replay Editor")
        self.setAcceptDrops(True)
        self.setFixedSize(500, 500)  # Set fixed window size

        main_layout = QVBoxLayout()

        settings_group = QGroupBox("Settings:")
        settings_layout = QGridLayout()
        settings_group.setLayout(settings_layout)

        mods_group = QGroupBox("Mods:")
        mods_layout = QHBoxLayout()
        mods_group.setLayout(mods_layout)
        
        self.load_button = QPushButton('Load Replay File', self)
        self.load_button.setFixedHeight(150)
        self.load_button.setStyleSheet("QPushButton { border: 2px dashed gray; }")
        self.load_button.setText("Drop file / browse files")
        self.load_button.clicked.connect(self.load_file)

        self.save_button = QPushButton('Save Replay File', self)
        self.save_button.setFixedHeight(50)
        self.save_button.clicked.connect(self.save_file)

        # Settings layout
        settings_layout.addWidget(QLabel('Approach Rate:'), 0, 0)
        self.approach_rate_edit = QLineEdit(self)
        settings_layout.addWidget(self.approach_rate_edit, 0, 1)

        settings_layout.addWidget(QLabel('UI Parallax:'), 0, 2)
        self.ui_parallax_edit = QLineEdit(self)
        settings_layout.addWidget(self.ui_parallax_edit, 0, 3)

        settings_layout.addWidget(QLabel('Spawn Distance:'), 1, 0)
        self.spawn_distance_edit = QLineEdit(self)
        settings_layout.addWidget(self.spawn_distance_edit, 1, 1)

        settings_layout.addWidget(QLabel('Grid Parallax:'), 1, 2)
        self.grid_parallax_edit = QLineEdit(self)
        settings_layout.addWidget(self.grid_parallax_edit, 1, 3)

        settings_layout.addWidget(QLabel('Fade Length:'), 2, 0)
        self.fade_length_edit = QLineEdit(self)
        settings_layout.addWidget(self.fade_length_edit, 2, 1)

        settings_layout.addWidget(QLabel('FOV:'), 2, 2)
        self.fov_edit = QLineEdit(self)
        settings_layout.addWidget(self.fov_edit, 2, 3)

        settings_layout.addWidget(QLabel('Parallax:'), 3, 0)
        self.parallax_edit = QLineEdit(self)
        settings_layout.addWidget(self.parallax_edit, 3, 1)

        settings_layout.addWidget(QLabel('Speed:'), 3, 2)
        self.speed_combo = QComboBox(self)
        self.speed_combo.addItems([
            "Normal (1.0)",
            "Speed --- (0.75)",
            "Speed -- (0.8)",
            "Speed - (0.85)",
            "Speed + (1.15)",
            "Speed ++ (1.25)",
            "Speed +++ (1.35)",
            "Speed ++++ (1.45)"
        ])
        settings_layout.addWidget(self.speed_combo, 3, 3)

        # Mods layout
        self.earthquake_check = QCheckBox('Earthquake', self)
        mods_layout.addWidget(self.earthquake_check)
        self.chaos_check = QCheckBox('Chaos', self)
        mods_layout.addWidget(self.chaos_check)
        self.flashlight_check = QCheckBox('Flashlight', self)
        mods_layout.addWidget(self.flashlight_check)
        self.ghost_check = QCheckBox('Ghost', self)
        mods_layout.addWidget(self.ghost_check)
        self.hardrock_check = QCheckBox('Hardrock', self)
        mods_layout.addWidget(self.hardrock_check)

        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.load_button)
        buttons_layout.addWidget(self.save_button)

        main_layout.addWidget(settings_group)
        main_layout.addWidget(mods_group)
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.sspre'):
                self.load_file(file_path)
                break

    def load_file(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, 'Open Replay File', '', 'Replay Files (*.sspre)')
        if file_path:
            self.reset_fields()
            self.replay.read_data(file_path)
            if self.replay.loaded:
                self.populate_fields()

    def reset_fields(self):
        self.approach_rate_edit.clear()
        self.spawn_distance_edit.clear()
        self.fade_length_edit.clear()
        self.parallax_edit.clear()
        self.ui_parallax_edit.clear()
        self.grid_parallax_edit.clear()
        self.fov_edit.clear()
        self.speed_combo.setCurrentText("Normal (1.0)")
        self.earthquake_check.setChecked(False)
        self.chaos_check.setChecked(False)
        self.flashlight_check.setChecked(False)
        self.ghost_check.setChecked(False)
        self.hardrock_check.setChecked(False)

    def populate_fields(self):
        self.approach_rate_edit.setText(str(self.replay.approach_rate))
        self.spawn_distance_edit.setText(str(self.replay.spawn_distance))
        self.fade_length_edit.setText(str(self.replay.fade_length))
        self.parallax_edit.setText(str(self.replay.parallax))
        self.ui_parallax_edit.setText(str(self.replay.ui_parallax))
        self.grid_parallax_edit.setText(str(self.replay.grid_parallax))
        self.fov_edit.setText(str(self.replay.fov))
        self.speed_combo.setCurrentText(self._get_speed_label(self.replay.speed))
        self.update_mod_checkboxes()

    def _get_speed_label(self, speed):
        speed_mapping = {
            "=": "Normal (1.0)",
            "---": "Speed --- (0.75)",
            "--": "Speed -- (0.8)",
            "-": "Speed - (0.85)",
            "+": "Speed + (1.15)",
            "++": "Speed ++ (1.25)",
            "+++": "Speed +++ (1.35)",
            "++++": "Speed ++++ (1.45)"
        }
        return speed_mapping.get(speed, "Normal (1.0)")

    def save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save Replay File', '', 'Replay Files (*.sspre)')
        if file_path:
            try:
                self.replay.set_approach_rate(float(self.approach_rate_edit.text()))
                self.replay.set_spawn_distance(float(self.spawn_distance_edit.text()))
                self.replay.set_fade_length(float(self.fade_length_edit.text()))
                self.replay.set_parallax(float(self.parallax_edit.text()))
                self.replay.set_ui_parallax(float(self.ui_parallax_edit.text()))
                self.replay.set_grid_parallax(float(self.grid_parallax_edit.text()))
                self.replay.set_fov(float(self.fov_edit.text()))
                self.replay.set_speed(self.speed_combo.currentText())
                self.update_mods()
                self.replay.save_data(file_path)
                QMessageBox.information(self, 'Success', 'Replay file saved successfully.')
            except ValueError:
                QMessageBox.critical(self, 'Error', 'Invalid input for one or more fields.')

    def update_mod_checkboxes(self):
        mods = self.replay.mods.split(";")
        self.earthquake_check.setChecked("m_earthquake" in mods)
        self.chaos_check.setChecked("m_chaos" in mods)
        self.flashlight_check.setChecked("m_flashlight" in mods)
        self.ghost_check.setChecked("m_ghost" in mods)
        self.hardrock_check.setChecked("m_hardrock" in mods)

    def update_mods(self):
        self.replay.mods = ""
        mods = []
        if self.earthquake_check.isChecked():
            mods.append("m_earthquake")
        if self.chaos_check.isChecked():
            mods.append("m_chaos")
        if self.flashlight_check.isChecked():
            mods.append("m_flashlight")
        if self.ghost_check.isChecked():
            mods.append("m_ghost")
        if self.hardrock_check.isChecked():
            mods.append("m_hardrock")
        
        self.replay.mods = ";".join(mods)
        # Update pb_str with mods and speed
        pb_str_parts = [part for part in self.replay.pb_str.split(";") if not part.startswith("m_") and not part.startswith("s:")]
        if self.replay.mods:
            pb_str_parts.append(self.replay.mods)
        if self.replay.speed:
            pb_str_parts.append(f"s:{self.replay.speed}")
        self.replay.pb_str = ";".join(pb_str_parts)

def main():
    app = QApplication(sys.argv)
    editor = ReplayEditor()
    editor.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
