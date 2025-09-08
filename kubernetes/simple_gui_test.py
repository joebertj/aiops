#!/usr/bin/env python3
"""
Simple GUI Test for Debugging
"""

import tkinter as tk
from tkinter import ttk, messagebox

def main():
    """Simple test GUI"""
    root = tk.Tk()
    root.title("Simple GUI Test")
    root.geometry("600x400")
    
    # Test label
    label = ttk.Label(root, text="🚀 GUI Test - Can you see this?", font=('Arial', 16))
    label.pack(pady=20)
    
    # Test button
    def test_click():
        messagebox.showinfo("Test", "Button click works!")
    
    button = ttk.Button(root, text="Click Me!", command=test_click)
    button.pack(pady=20)
    
    # Test entry
    entry = ttk.Entry(root, width=40)
    entry.pack(pady=20)
    entry.insert(0, "Type here to test input")
    
    # Status
    status = ttk.Label(root, text="Status: GUI is working!", foreground='green')
    status.pack(pady=20)
    
    print("GUI window should appear now...")
    root.mainloop()

if __name__ == "__main__":
    main()

