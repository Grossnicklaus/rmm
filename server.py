import socket
import pickle
import threading
import tkinter as tk
from tkinter import ttk
import subprocess
import platform
import os

AGENT_PORT = 12345

class RemoteSpecsServerGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Remote System Specs Server")
        self.master.geometry("800x400")

        self.frame = ttk.Frame(master)
        self.frame.pack(expand=1, fill="both")

        self.agent_list_label = tk.Label(self.frame, text="Agent List")
        self.agent_list_label.pack(pady=10)

        self.agent_listbox = tk.Listbox(self.frame)
        self.agent_listbox.pack(expand=1, fill="both", padx=10, pady=5)
        self.agent_listbox.bind("<<ListboxSelect>>", self.show_agent_info)

        self.info_frame = ttk.Frame(self.frame)
        self.info_frame.pack(expand=1, fill="both")

        self.connect_var = tk.StringVar()
        self.connect_var.set("Connect")

        self.connect_button = tk.Menubutton(self.info_frame, textvariable=self.connect_var, relief="raised")
        self.connect_button.grid(row=0, column=0, padx=5)

        self.connect_menu = tk.Menu(self.connect_button, tearoff=0)
        self.connect_button["menu"] = self.connect_menu
        self.connect_menu.add_command(label="Start RDP", command=self.start_rdp)
        self.connect_menu.add_command(label="Start Remote Shell", command=self.start_remote_shell)

        self.info_label = tk.Label(self.info_frame, text="System Information")
        self.info_label.grid(row=0, column=1, pady=10)

        self.info_text = tk.Text(self.info_frame, wrap="word", width=40, height=12)
        self.info_text.grid(row=1, column=1, padx=10, pady=5)

        self.agents = []
        self.update_agent_list()

    def update_agent_list(self):
        self.agent_listbox.delete(0, tk.END)
        for agent_name, _ in self.agents:
            self.agent_listbox.insert(tk.END, agent_name)

    def show_agent_info(self, event):
        selected_index = self.agent_listbox.curselection()
        if selected_index:
            selected_agent = self.agents[selected_index[0]]
            system_info = selected_agent[1]['system_info']
        
            formatted_info = "System Information:\n"
            for key, value in system_info.items():
                if isinstance(value, dict):
                    formatted_info += f"{key}:\n"
                    for sub_key, sub_value in value.items():
                        formatted_info += f"  {sub_key}: {sub_value}\n"
                else:
                    formatted_info += f"{key}: {value}\n"

        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, formatted_info)
        self.info_text.config(state=tk.DISABLED)



    def start_rdp(self):
        selected_index = self.agent_listbox.curselection()
        if selected_index:
            selected_agent = self.agents[selected_index[0]]
            agent_name = selected_agent[0]
            subprocess.run(['mstsc', '/v:{0}'.format(agent_name)])

    def start_remote_shell(self):
        selected_index = self.agent_listbox.curselection()
        if selected_index:
            selected_agent = self.agents[selected_index[0]]
            agent_name = selected_agent[0]
            subprocess.run(['C:\\Users\\No\\Desktop\\RMM\\psexec.exe', f'\\\\{agent_name}', 'cmd.exe'])


    def start_server(self):
        threading.Thread(target=self._server).start()

    def _server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', AGENT_PORT))
        server_socket.listen(5)

        print(f"Server listening on 0.0.0.0:{AGENT_PORT}")

        while True:
            client_socket, addr = server_socket.accept()
            threading.Thread(target=self.handle_agent, args=(client_socket, addr)).start()

    def handle_agent(self, client_socket, addr):
        try:
            data = client_socket.recv(4096)
            if not data:
                return

            agent_info = pickle.loads(data)
            agent_name = agent_info['system_info']['Hostname']

            existing_agent = next((agent for agent, _ in self.agents if agent == agent_name), None)
            if existing_agent:
                self.agents.remove((existing_agent, _))

            self.agents.append((agent_name, agent_info))

            self.update_agent_list()

            print(f"Connection from {addr}")
            print(f"Received System Information:\n{agent_info}")

        except Exception as e:
            print(f"Error handling agent connection: {e}")
        finally:
            client_socket.close()

if __name__ == "__main__":
    root = tk.Tk()
    server_gui = RemoteSpecsServerGUI(root)
    server_gui.start_server()
    root.mainloop()
