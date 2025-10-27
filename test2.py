import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class TaskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Manager")
        self.root.geometry("600x400")
        
        # Initialize database
        self.init_database()
        
        # Create GUI
        self.create_widgets()
        self.load_tasks()
    
    def init_database(self):
        self.conn = sqlite3.connect('test.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute()
        self.conn.commit()
    
    def create_widgets(self):
        test = 0
        # Input frame
       
        # Treeview for displaying tasks
       
        # Button frame
        

    def add_task(self):
        test = 0

    def load_tasks(self):
        test = 0

    def on_item_select(self, event):
        test = 0

    def update_task(self):
        test = 0

    def delete_task(self):
        test = 0

    def mark_complete(self):
        test = 0
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskApp(root)
    root.mainloop()