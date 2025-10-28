import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

class TaskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Manager")
        self.root.geometry("840x300")
        
        # Initialize the database
        self.init_database()
        
        # Create GUI
        self.create_widgets()
        self.load_tasks()
    def init_database(self):
        db_folder = './Database'
        os.makedirs(db_folder, exist_ok=True)
        
        self.conn = sqlite3.connect('./Database/tasks.db')
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
        #                   --- Input frame ---
        #                    --- Labels ---
        self.label_title = tk.Label(self.root, text="Title")
        self.label_desc = tk.Label(self.root, text="Description")
        self.label_status = tk.Label(self.root, text="Status")
        self.label_quantity = tk.Label(self.root, text="Quantity")
        
        self.label_title.grid(row=0, column=0, padx=5, pady=5, sticky="n")
        self.label_desc.grid(row=1, column=0, padx=5, pady=5, sticky="n")
        self.label_status.grid(row=2, column=0, padx=5, pady=5, sticky="n")
        self.label_quantity.grid(row=3, column=0, padx=5, pady=5, sticky="n")
        
        #                     --- Entries ---
        self.e1 = tk.Entry(self.root)
        self.e2 = tk.Entry(self.root)
        self.e3 = tk.Entry(self.root)
        self.e4 = tk.Entry(self.root)
        
        self.e1.grid(row=0, column=1, padx=5, pady=0, sticky="wen")
        self.e2.grid(row=1, column=1, padx=5, pady=0, sticky="wen")
        self.e3.grid(row=2, column=1, padx=5, pady=0, sticky="wen")
        self.e4.grid(row=3, column=1, padx=5, pady=0, sticky="wen")
        
        #              --- Treeview for displaying tasks ---
        columns = ("id", "title", "description", "status", "quantity", "inStock")
        self.tree = ttk.Treeview(self.root, columns=columns, selectmode=tk.EXTENDED, show="headings", height=11)
        
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=100)
        
        self.tree.grid(row=0, column=2, rowspan=4, padx=10, pady=5, sticky="nsew")
        self.tree.bind('<ButtonRelease-1>', self.on_item_select)
        #                        --- Button frame ---
        submitTask_button = tk.Button(
            self.root,
            text="Submit",
            command=self.add_task, 
            activebackground="blue",
            activeforeground="white"
        )
        updateTask_button = tk.Button(
            self.root,
            text="Update", 
            command=self.update_task,
            activebackground="blue", 
            activeforeground="white"
        )

        completeTask_button = tk.Button(
            self.root,
            text="Complete task", 
            command=self.mark_complete,
            activebackground="blue", 
            activeforeground="white"
        )
        deleteTask_button = tk.Button(
            self.root,
            text="Delete task", 
            command=self.delete_task,
            activebackground="blue", 
            activeforeground="white"
        )
        
        submitTask_button.grid(row=4, column=0, columnspan=1, padx=5, pady=10, sticky="new")
        updateTask_button.grid(row=4, column=1, columnspan=1, padx=5, pady=10, sticky="new")
        completeTask_button.grid(row=4, column=2, columnspan=1, padx=5, pady=10, sticky="w")
        deleteTask_button.grid(row=4, column=2, columnspan=1, padx=5, pady=10, sticky="ne")
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
        #           ---Clear--
        for row in self.tree.get_children():
            self.tree.delete(row)
        #          ---Fetch all---
        self.cursor.execute("SELECT * FROM tasks")
        rows = self.cursor.fetchall()
        #       ---Insert each row---
        for row in rows:
            self.tree.insert("", tk.END, values=row)

    def on_item_select(self, event):
        item_id = self.tree.focus()
        item = self.tree.item(item_id)
        values = item['values']
        
        if not values:
            return
        
        self.e1.delete(0, tk.END)
        self.e1.insert(0, values[1]) 
        self.e2.delete(0, tk.END)
        self.e2.insert(0, values[2])  
        self.e3.delete(0, tk.END)
        self.e3.insert(0, values[3])
        self.e4.delete(0, tk.END)
        self.e4.insert(0, values[4])
        
        self.selected_id = values[0]  
        

    def update_task(self):
        task_id = self.selected_id

        title = self.e1.get().strip()
        description = self.e2.get().strip()
        status = self.e3.get().strip()
        quantity = self.e4.get().strip()

        sql_update_query = """
            UPDATE tasks
            SET title = ?, description = ?, status = ?, quantity = ?
            WHERE id = ?
        """
        self.cursor.execute(sql_update_query, (title, description, status, quantity, task_id))
        self.conn.commit()

        self.load_tasks()
        messagebox.showinfo("Success", "Task updated successfully!")

        del self.selected_id


    def delete_task(self):
        task_id = self.selected_id

        sql_update_query = """
            DELETE FROM tasks
            WHERE id = ?
        """
        self.cursor.execute(sql_update_query, (task_id,))
        self.conn.commit()

        self.load_tasks()
        messagebox.showinfo("Success", "Task deleted successfully!")

        del self.selected_id


    def mark_complete(self):
        task_id = self.selected_id

        status = "completed"

        sql_update_query = """
            UPDATE tasks
            SET status = ?
            WHERE id = ?
        """
        self.cursor.execute(sql_update_query, (status, task_id))
        self.conn.commit()

        self.load_tasks()
        messagebox.showinfo("Success", "Task completed successfully!")

        del self.selected_id

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = TaskApp(root)
    root.mainloop()

