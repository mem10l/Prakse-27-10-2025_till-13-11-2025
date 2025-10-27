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
        self.conn = sqlite3.connect('tasks.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        self.conn.commit()
    
    def create_widgets(self):
        # Input frame
        input_frame = ttk.Frame(self.root)
        input_frame.pack(pady=10, padx=10, fill='x')
        
        ttk.Label(input_frame, text="Title:").grid(row=0, column=0, sticky='w')
        self.title_entry = ttk.Entry(input_frame, width=30)
        self.title_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(input_frame, text="Description:").grid(row=1, column=0, sticky='w')
        self.desc_entry = ttk.Entry(input_frame, width=30)
        self.desc_entry.grid(row=1, column=1, padx=5)
        
        ttk.Button(input_frame, text="Add Task", command=self.add_task).grid(row=0, column=2, padx=5)
        ttk.Button(input_frame, text="Update Task", command=self.update_task).grid(row=1, column=2, padx=5)

        # Treeview for displaying tasks
        self.tree = ttk.Treeview(self.root, columns=('ID', 'Title', 'Description', 'Status'), show='headings')
        self.tree.heading('ID', text='ID')
        self.tree.heading('Title', text='Title')
        self.tree.heading('Description', text='Description')
        self.tree.heading('Status', text='Status')
        
        self.tree.column('ID', width=50)
        self.tree.column('Title', width=150)
        self.tree.column('Description', width=200)
        self.tree.column('Status', width=100)
        
        self.tree.pack(pady=10, padx=10, fill='both', expand=True)
        self.tree.bind('<ButtonRelease-1>', self.on_item_select)
        
        # Button frame
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=5)

        ttk.Button(button_frame, text="Delete Task", command=self.delete_task).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Mark Complete", command=self.mark_complete).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Refresh", command=self.load_tasks).pack(side='left', padx=5)
    
    def add_task(self):
        title = self.title_entry.get().strip()
        description = self.desc_entry.get().strip()
        
        if not title:
            messagebox.showwarning("Warning", "Title is required!")
            return
        
        self.cursor.execute("INSERT INTO tasks (title, description) VALUES (?, ?)", (title, description))
        self.conn.commit()
        
        self.title_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.load_tasks()
        messagebox.showinfo("Success", "Task added!")
    
    def load_tasks(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.cursor.execute("SELECT * FROM tasks")
        for row in self.cursor.fetchall():
            self.tree.insert('', 'end', values=row)
    
    def on_item_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            self.title_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)
            self.title_entry.insert(0, values[1])
            self.desc_entry.insert(0, values[2])
    
    def update_task(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a task to update!")
            return
        
        item = self.tree.item(selection[0])
        task_id = item['values'][0]
        title = self.title_entry.get().strip()
        description = self.desc_entry.get().strip()
        
        if not title:
            messagebox.showwarning("Warning", "Title is required!")
            return
        
        self.cursor.execute("UPDATE tasks SET title=?, description=? WHERE id=?", (title, description, task_id))
        self.conn.commit()
        self.load_tasks()
        messagebox.showinfo("Success", "Task updated!")
    
    def delete_task(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a task to delete!")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected task?"):
            item = self.tree.item(selection[0])
            task_id = item['values'][0]
            self.cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            self.conn.commit()
            self.load_tasks()
    
    def mark_complete(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a task!")
            return
        
        item = self.tree.item(selection[0])
        task_id = item['values'][0]
        self.cursor.execute("UPDATE tasks SET status='completed' WHERE id=?", (task_id,))
        self.conn.commit()
        self.load_tasks()
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = TaskApp(root)
    root.mainloop()