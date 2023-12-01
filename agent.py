import socket
import pickle
import threading
import time
import platform
import subprocess
import re
import atexit

SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345

def get_system_info():
    system_info = {}
    system_info['System'] = platform.system()
    system_info['Node Name'] = platform.node()
    system_info['Version'] = platform.version()
    system_info['Machine'] = platform.machine()
    system_info['Processor'] = platform.processor()
    try:
        installed_ram, used_ram = get_ram_info()
        system_info['Installed RAM'] = installed_ram
        system_info['Used RAM'] = used_ram
    except Exception as e:
        print(f"Error getting RAM information: {e}")
        system_info['Installed RAM'] = 'N/A'
        system_info['Used RAM'] = 'N/A'
    system_info['Hostname'] = socket.gethostname()
    try:
        system_info['IP Address'] = socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        system_info['IP Address'] = 'N/A'
    return system_info

def get_ram_info():
    try:
        total_ram_command = r'Get-WmiObject Win32_PhysicalMemory | Measure-Object Capacity -Sum | Select-Object -ExpandProperty Sum'
        used_ram_command = r'Get-Counter "\Memory\Available MBytes" | Select-Object -ExpandProperty CounterSamples | Select-Object -ExpandProperty CookedValue'
        total_ram_result = subprocess.run(['powershell', '-Command', total_ram_command], capture_output=True, text=True, check=True)
        used_ram_result = subprocess.run(['powershell', '-Command', used_ram_command], capture_output=True, text=True, check=True)
        total_ram_bytes_str = re.search(r'\d+', total_ram_result.stdout)
        used_ram_mb_str = re.search(r'\d+', used_ram_result.stdout)
        if total_ram_bytes_str and used_ram_mb_str:
            total_ram_bytes = int(total_ram_bytes_str.group())
            used_ram_mb = int(used_ram_mb_str.group())
            total_ram_gb = total_ram_bytes / (1024 ** 3)
            used_ram_gb = round(used_ram_mb / 1024)
            return f"{total_ram_gb:.2f} GB", f"{used_ram_gb} GB"
        else:
            raise ValueError(f"Failed to extract numeric values from PowerShell output: {total_ram_result.stdout}, {used_ram_result.stdout}")
    except Exception as e:
        print(f"Error getting RAM information on Windows: {e}")
        return 'N/A', 'N/A'

def send_system_info_to_server():
    while True:
        try:
            system_info = get_system_info()
            data = {'system_info': system_info}
            serialized_data = pickle.dumps(data)
            with socket.create_connection((SERVER_IP, SERVER_PORT)) as s:
                s.sendall(serialized_data)
        except Exception as e:
            print(f"Error sending data to server: {e}")
        time.sleep(60)

def exit_thread():
    print("Exiting agent thread.")

if __name__ == "__main__":
    atexit.register(exit_thread)
    threading.Thread(target=send_system_info_to_server).start()
