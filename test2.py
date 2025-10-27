import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class TaskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Manager")
        self.root.geometry("800x280")
        
        # Initialize the database
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
        #                   --- 1 Input frame ---
        #                    --- 1.2 Labels ---
        self.label_title = tk.Label(self.root, text="Title")
        self.label_desc = tk.Label(self.root, text="Description")
        self.label_status = tk.Label(self.root, text="Status")
        self.label_quantity = tk.Label(self.root, text="Quantity")
        
        self.label_title.grid(row=0, column=0, padx=5, pady=5, sticky="n")
        self.label_desc.grid(row=1, column=0, padx=5, pady=5, sticky="n")
        self.label_status.grid(row=2, column=0, padx=5, pady=5, sticky="n")
        self.label_quantity.grid(row=3, column=0, padx=5, pady=5, sticky="n")
        
        #                     --- 1.3 Entries ---
        self.e1 = tk.Entry(self.root)
        self.e2 = tk.Entry(self.root)
        self.e3 = tk.Entry(self.root)
        self.e4 = tk.Entry(self.root)
        
        self.e1.grid(row=0, column=1, padx=5, pady=0, sticky="wen")
        self.e2.grid(row=1, column=1, padx=5, pady=0, sticky="wen")
        self.e3.grid(row=2, column=1, padx=5, pady=0, sticky="wen")
        self.e4.grid(row=3, column=1, padx=5, pady=0, sticky="wen")
        
        self.root.grid_columnconfigure(1, weight=1)
        
        #              --- 1.4 Treeview for displaying tasks ---
        columns = ("id", "title", "description", "status", "quantity", "inStock")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=100)
        
        self.tree.grid(row=0, column=2, rowspan=4, padx=10, pady=5, sticky="nsew")
        self.root.grid_columnconfigure(2, weight=3)
        self.root.grid_rowconfigure(4, weight=1)
        
        #                        --- 1.5 Button frame ---
        submit_button = tk.Button(
            self.root,
            text="Submit",
            command=self.add_task, 
            activebackground="blue",
            activeforeground="white"
        )
        update_button = tk.Button(
            self.root, text="Update", 
            activebackground="blue", activeforeground="white"
        )
        
        submit_button.grid(row=4, column=0, columnspan=1, padx=5, pady=10, sticky="new")
        update_button.grid(row=4, column=1, columnspan=1, padx=5, pady=10, sticky="new")
    
    def add_task(self):
        title = self.e1.get().strip()
        description = self.e2.get().strip()
        status = self.e3.get().strip()
        quantity = self.e4.get().strip()

        self.cursor.execute("INSERT INTO tasks (title, description, status, quantity) VALUES (?, ?, ?, ?)", (title, description, status, quantity))
        self.conn.commit()
            
        self.e1.delete(0, tk.END)
        self.e2.delete(0, tk.END)
        self.e3.delete(0, tk.END)
        self.e4.delete(0, tk.END)
        self.load_tasks()
        messagebox.showinfo("Success", "Task added!")
        return

    def load_tasks(self):
        pass

    def on_item_select(self, event):
        pass

    def update_task(self):
        pass

    def delete_task(self):
        pass

    def mark_complete(self):
        pass

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = TaskApp(root)
    root.mainloop()

