import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import socket
import base64
import os
import threading

BUFFER_SIZE = 1048576

class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Client GUI")
        self.client_socket = None
        self.connected = False
        self.registered = False

        # servIp
        tk.Label(root, text="Server IP:").grid(row=0, column=0)
        self.server_ip_entry = tk.Entry(root)
        self.server_ip_entry.grid(row=0, column=1)

        # servPort
        tk.Label(root, text="Server Port:").grid(row=1, column=0)
        self.server_port_entry = tk.Entry(root)
        self.server_port_entry.grid(row=1, column=1)

        # handle
        tk.Label(root, text="Handle:").grid(row=2, column=0)
        self.handle_entry = tk.Entry(root)
        self.handle_entry.grid(row=2, column=1)

        # connectbtn
        self.connect_button = tk.Button(root, text="Connect", command=self.connect_to_server)
        self.connect_button.grid(row=3, column=0, columnspan=2)

        # RegisterBtn
        self.register_button = tk.Button(root, text="Register", command=self.register_handle)
        self.register_button.grid(row=4, column=0, columnspan=2)

        # uploadBtn
        self.upload_button = tk.Button(root, text="Upload File", command=self.upload_file)
        self.upload_button.grid(row=5, column=0, columnspan=2)

        # DIRbtn
        self.dir_button = tk.Button(root, text="Directory List", command=self.request_dir_list)
        self.dir_button.grid(row=6, column=0, columnspan=2)

        # downloadbtn
        self.download_button = tk.Button(root, text="Download File", command=self.download_file)
        self.download_button.grid(row=7, column=0, columnspan=2)

        # commandInp
        tk.Label(root, text="Enter Command:").grid(row=8, column=0)
        self.command_entry = tk.Entry(root)
        self.command_entry.grid(row=8, column=1)
        self.command_button = tk.Button(root, text="Enter", command=self.send_command)
        self.command_button.grid(row=8, column=2)

        # unicastInp
        tk.Label(root, text="Unicast Handle:").grid(row=9, column=0)
        self.unicast_handle_entry = tk.Entry(root)
        self.unicast_handle_entry.grid(row=9, column=1)
        tk.Label(root, text="Message:").grid(row=10, column=0)
        self.unicast_message_entry = tk.Entry(root)
        self.unicast_message_entry.grid(row=10, column=1)
        self.unicast_button = tk.Button(root, text="Send Unicast", command=self.send_unicast)
        self.unicast_button.grid(row=10, column=2)

        # broadcstUInp
        tk.Label(root, text="Broadcast Message:").grid(row=11, column=0)
        self.broadcast_message_entry = tk.Entry(root)
        self.broadcast_message_entry.grid(row=11, column=1)
        self.broadcast_button = tk.Button(root, text="Send Broadcast", command=self.send_broadcast)
        self.broadcast_button.grid(row=11, column=2)

        # outputBox
        self.output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=15)
        self.output_area.grid(row=12, column=0, columnspan=3)

    def connect_to_server(self):
        if self.connected:
            messagebox.showinfo("Info", "Already connected to the server.")
            return

        try:
            server_ip = self.server_ip_entry.get()
            server_port = int(self.server_port_entry.get())
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, server_port))
            self.connected = True
            self.output_area.insert(tk.END, f"Connected to server at {server_ip}:{server_port}\n")
            self.listen_for_unicast()  
        except Exception as e:
            messagebox.showerror("Error", f"Could not connect to the server: {e}")

    def register_handle(self):
        if not self.connected:
            messagebox.showerror("Error", "You must connect to a server first.")
            return

        handle = self.handle_entry.get()
        if not handle:
            messagebox.showerror("Error", "Handle cannot be empty.")
            return

        try:
            self.client_socket.send(f"/register {handle}".encode('utf-8'))
            response = self.client_socket.recv(BUFFER_SIZE).decode('utf-8')
            self.output_area.insert(tk.END, f"{response}\n")
            self.registered = True
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while registering: {e}")

    def send_command(self):
        command = self.command_entry.get()
        if not command:
            messagebox.showerror("Error", "Command cannot be empty.")
            return

        if command.startswith("/join"):
            self.handle_join_command(command)
        else:
            self.send_generic_command(command)

    def handle_join_command(self, command):
        try:
            _, server_ip, server_port = command.split()
            server_port = int(server_port)

            if self.client_socket:
                self.client_socket.close()

            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, server_port))
            self.connected = True

            self.server_ip_entry.delete(0, tk.END)
            self.server_ip_entry.insert(0, server_ip)
            self.server_port_entry.delete(0, tk.END)
            self.server_port_entry.insert(0, str(server_port))

            self.output_area.insert(tk.END, f"Connected to {server_ip}:{server_port}\n")
            self.listen_for_unicast()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to join server: {e}")
            
    def handle_leave_command(self):
        if not self.connected:
            messagebox.showerror("Error", "You are not connected to any server.")
            return

        try:
            self.client_socket.send("/leave".encode('utf-8'))
            self.client_socket.close()
            self.connected = False
            self.output_area.insert(tk.END, "Client left the session.\n")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while leaving the session: {e}")

    def send_generic_command(self, command):
        if not self.connected:
            messagebox.showerror("Error", "You must connect to a server first.")
            return

        def send_and_receive():
            try:
                self.client_socket.send(command.encode('utf-8'))
                response = self.client_socket.recv(BUFFER_SIZE).decode('utf-8')
                self.output_area.insert(tk.END, f"{response}\n")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while sending the command: {e}")

        threading.Thread(target=send_and_receive).start()

    def send_unicast(self):
        if not self.connected:
            messagebox.showerror("Error", "You must connect to a server first.")
            return

        target_handle = self.unicast_handle_entry.get()
        message = self.unicast_message_entry.get()
        if not target_handle or not message:
            messagebox.showerror("Error", "Both handle and message must be provided for unicast.")
            return

        try:
            self.client_socket.send(f"/unicast {target_handle} {message}".encode('utf-8'))
            response = self.client_socket.recv(BUFFER_SIZE).decode('utf-8')
            self.output_area.insert(tk.END, f"Unicast sent to {target_handle}: {response}\n")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while sending the unicast message: {e}")

    def send_broadcast(self):
        if not self.connected:
            messagebox.showerror("Error", "You must connect to a server first.")
            return

        message = self.broadcast_message_entry.get()
        if not message:
            messagebox.showerror("Error", "Broadcast message cannot be empty.")
            return

        try:
            self.client_socket.send(f"/broadcast {message}".encode('utf-8'))
            response = self.client_socket.recv(BUFFER_SIZE).decode('utf-8')
            self.output_area.insert(tk.END, f"Broadcast sent: {response}\n")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while sending the broadcast message: {e}")

    def upload_file(self):
        if not self.registered:
            messagebox.showerror("Error", "You must register a handle first.")
            return

        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        try:
            file_name = os.path.basename(file_path)
            self.client_socket.send(f"/store {file_name}".encode('utf-8'))
            with open(file_path, 'rb') as file:
                file_data = file.read()
                self.client_socket.send(file_data)
            self.output_area.insert(tk.END, f"File {file_name} uploaded successfully.\n")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while uploading: {e}")

    def request_dir_list(self):
        if not self.registered:
            messagebox.showerror("Error", "You must register a handle first.")
            return

        try:
            self.client_socket.send("/dir".encode('utf-8'))
            response = self.client_socket.recv(BUFFER_SIZE).decode('utf-8')
            self.output_area.insert(tk.END, f"Directory List:\n{response}\n")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while requesting directory list: {e}")

    def download_file(self):
        if not self.registered:
            messagebox.showerror("Error", "You must register a handle first.")
            return

        file_name = filedialog.asksaveasfilename()
        if not file_name:
            return

        try:
            self.client_socket.send(f"/get {file_name}".encode('utf-8'))
            response = self.client_socket.recv(BUFFER_SIZE).decode('utf-8')

            if response == "FILE_NOT_FOUND":
                messagebox.showerror("Error", "File not found on the server.")
                return

            padding = len(response) % 4
            if padding:
                response += '=' * (4 - padding)
            file_data = base64.b64decode(response)
            with open(file_name, 'wb') as file:
                file.write(file_data)
            self.output_area.insert(tk.END, f"File {file_name} downloaded successfully.\n")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while downloading: {e}")

    def listen_for_unicast(self):
        def listen():
            while True:
                try:
                    message = self.client_socket.recv(BUFFER_SIZE).decode('utf-8')
                    if message:
                        self.output_area.insert(tk.END, f"Unicast/Broadcast Message: {message}\n")
                except Exception as e:
                    break

        threading.Thread(target=listen, daemon=True).start()

    def close_connection(self):
        if self.client_socket:
            self.client_socket.send("/leave".encode('utf-8'))
            self.client_socket.close()
            self.connected = False
            self.output_area.insert(tk.END, "Disconnected from the server.\n")

    def on_closing(self):
        self.close_connection()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
