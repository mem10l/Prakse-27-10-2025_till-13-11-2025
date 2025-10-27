import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox
import sqlite3

def button_clicked():
    return addTask()

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
        self.conn = sqlite3.connect('tasks.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                quantity INTEGER,
                inStock INTEGER
            )
        ''')
        self.conn.commit()
    
    def create_widgets(self):
        # Input frame
        # Labels
        self.label_title = tk.Label(self.root, text="Title")
        self.label_desc = tk.Label(self.root, text="Description")
        self.label_status = tk.Label(self.root, text="status")
        self.label_quantity = tk.Label(self.root, text="quantity")
        self.label_title.grid(row=0, column=0)
        self.label_desc.grid(row=1, column=0)
        self.label_status.grid(row=2, column=0)
        self.label_quantity.grid(row=3, column=0)
        # Entries
        self.e1 = tk.Entry(self.root)
        self.e2 = tk.Entry(self.root)
        self.e3 = tk.Entry(self.root)
        self.e4 = tk.Entry(self.root)
        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        self.e3.grid(row=2, column=1)
        self.e4.grid(row=3, column=1)
        # Treeview for displaying tasks
        button = tk.Button(
            root,
            text="Click Me",
            command=button_clicked,         
            activebackground="blue",         
            activeforeground="white"         
        )
        button.grid(row=4, column=0, rowspan= 1, columnspan=2, pady=20)
        
       
        # Button frame
        
    def add_task(self):
        global addTask
        def addTask():
            return 

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