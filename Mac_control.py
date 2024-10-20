import sys
import os
import paramiko
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox

# 저장할 파일 이름 (JSON 경로 관리)
DATA_FILE = "ip_data.json"

def get_data_file_path():
    """
    JSON 파일을 실행 파일과 같은 경로에 저장 및 불러오기 위한 경로 반환.
    PyInstaller로 빌드된 EXE 파일의 경우와 일반 Python 스크립트에서 경로 처리.
    """
    if getattr(sys, 'frozen', False):  # PyInstaller로 빌드된 경우
        base_path = sys._MEIPASS  # PyInstaller가 빌드 시 사용하는 임시 폴더
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, DATA_FILE)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Network Management Tool")

        # 탭 위젯 생성
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 첫 번째 탭: Mac 리부팅
        self.reboot_tab = QWidget()
        self.create_reboot_tab()

        # 두 번째 탭: 새로운 기능 추가
        self.new_feature_tab = QWidget()
        self.create_new_feature_tab()

        # 탭 추가
        self.tabs.addTab(self.reboot_tab, "Mac Reboot")
        self.tabs.addTab(self.new_feature_tab, "New Feature")

        # 저장된 데이터를 불러옴
        self.load_data()

    def create_reboot_tab(self):
        layout = QVBoxLayout()

        # IP 입력 필드
        ip_label = QLabel("Enter IP Address:")
        self.ip_input = QLineEdit()
        layout.addWidget(ip_label)
        layout.addWidget(self.ip_input)

        # 사용자명 입력 필드
        username_label = QLabel("Enter Username:")
        self.username_input = QLineEdit()
        layout.addWidget(username_label)
        layout.addWidget(self.username_input)

        # 비밀번호 입력 필드
        password_label = QLabel("Enter Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)

        # IP 추가 버튼
        add_button = QPushButton("Add IP")
        add_button.clicked.connect(self.add_ip)
        layout.addWidget(add_button)

        # IP 리스트 섹션
        self.ip_list_widget = QListWidget()
        layout.addWidget(self.ip_list_widget)

        # IP 제거 버튼
        remove_button = QPushButton("Remove Selected IP")
        remove_button.clicked.connect(self.remove_ip)
        layout.addWidget(remove_button)

        # 재부팅 버튼
        reboot_button = QPushButton("Reboot Selected IPs")
        reboot_button.clicked.connect(self.reboot_macs)
        layout.addWidget(reboot_button)

        self.reboot_tab.setLayout(layout)

    def add_ip(self):
        ip_address = self.ip_input.text()
        username = self.username_input.text()
        password = self.password_input.text()

        if ip_address and username and password:
            # IP와 사용자명, 비밀번호를 리스트에 추가
            self.ip_list_widget.addItem(f"{ip_address} - {username} - {password}")
            self.ip_input.clear()
            self.username_input.clear()
            self.password_input.clear()

            # 데이터를 저장
            self.save_data()
        else:
            QMessageBox.warning(self, "Input Error", "Please enter a valid IP, username, and password.")

    def remove_ip(self):
        # 선택된 IP 삭제
        selected_items = self.ip_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select an IP address to remove.")
            return

        for item in selected_items:
            self.ip_list_widget.takeItem(self.ip_list_widget.row(item))

        # 데이터를 저장
        self.save_data()

    def reboot_macs(self):
        for i in range(self.ip_list_widget.count()):
            item_text = self.ip_list_widget.item(i).text()
            ip_address, username, password = item_text.split(" - ")

            if ip_address and username and password:
                print(f"Rebooting Mac at {ip_address}...")  # 디버그 출력
                self.ssh_reboot(ip_address, username, password)
            else:
                QMessageBox.warning(self, "Error", "IP address, username, or password missing.")

    def ssh_reboot(self, ip_address, username, password):
        try:
            # Paramiko SSH 연결 설정
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip_address, username=username, password=password)

            # SSH 명령 실행 (비밀번호와 함께 sudo를 사용하여 재부팅 명령 실행)
            command = f'echo {password} | sudo -S shutdown -r now'
            stdin, stdout, stderr = client.exec_command(command)
            stdout.channel.recv_exit_status()  # 명령 완료 대기

            print(f"Reboot command sent to {ip_address}")
            client.close()
        except Exception as e:
            print(f"Failed to reboot {ip_address}: {e}")
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to {ip_address}. Error: {str(e)}")


    def create_new_feature_tab(self):
        layout = QVBoxLayout()

        # 새 기능을 위한 간단한 UI
        label = QLabel("New Feature Coming Soon!")
        layout.addWidget(label)

        self.new_feature_tab.setLayout(layout)

    def save_data(self):
        """현재 IP 리스트 데이터를 JSON 파일로 저장"""
        data = []
        for i in range(self.ip_list_widget.count()):
            item_text = self.ip_list_widget.item(i).text()
            ip_address, username, password = item_text.split(" - ")
            data.append({
                'ip': ip_address,
                'username': username,
                'password': password
            })

        with open(get_data_file_path(), 'w') as f:
            json.dump(data, f)

    def load_data(self):
        """JSON 파일에서 데이터를 불러와 리스트에 추가"""
        try:
            with open(get_data_file_path(), 'r') as f:
                data = json.load(f)

            for entry in data:
                ip_address = entry['ip']
                username = entry['username']
                password = entry['password']
                self.ip_list_widget.addItem(f"{ip_address} - {username} - {password}")

        except (FileNotFoundError, json.JSONDecodeError):
            pass  # 파일이 없거나 문제가 있으면 무시

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
