import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox, filedialog
from .ai import RicAI
import json
import os

class RicGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ric AI")
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", self.on_quit)

        self.ai = RicAI(kb_path="kb.json")

        self._create_widgets()
        self._layout()
        self._bind()

    def _create_widgets(self):
        # Chat display
        self.chat = scrolledtext.ScrolledText(self, state='disabled', wrap='word')
        # Entry
        self.entry = ttk.Entry(self)
        self.send_btn = ttk.Button(self, text="Send", command=self.on_send)
        # Right pane for KB and controls
        self.kb_frame = ttk.LabelFrame(self, text="Knowledge Base")
        self.kb_list = tk.Listbox(self.kb_frame, height=10)
        self.kb_refresh_btn = ttk.Button(self.kb_frame, text="Refresh", command=self.load_kb_to_list)
        self.kb_add_btn = ttk.Button(self.kb_frame, text="Add", command=self.add_kb_entry)
        self.kb_view_btn = ttk.Button(self.kb_frame, text="View", command=self.view_kb_entry)
        # Settings
        self.settings_frame = ttk.LabelFrame(self, text="Settings")
        self.creativity = tk.DoubleVar(value=0.8)
        self.creativity_scale = ttk.Scale(self.settings_frame, from_=0.0, to=1.0, orient='horizontal', variable=self.creativity)
        self.train_btn = ttk.Button(self.settings_frame, text="Train Markov", command=self.train_markov)
        # Mode (offline / online) and optional model loading
        self.mode_var = tk.StringVar(value='offline')
        ttk.Label(self.settings_frame, text="Mode:").pack(anchor='w', padx=6, pady=(8, 0))
        self.mode_off_rb = ttk.Radiobutton(self.settings_frame, text='Offline', value='offline', variable=self.mode_var, command=self.on_mode_change)
        self.mode_on_rb = ttk.Radiobutton(self.settings_frame, text='Online', value='online', variable=self.mode_var, command=self.on_mode_change)
        self.mode_off_rb.pack(anchor='w', padx=12)
        self.mode_on_rb.pack(anchor='w', padx=12)
        self.load_model_btn = ttk.Button(self.settings_frame, text="Load Model", command=self.on_load_model)
        self.load_model_btn.pack(padx=6, pady=4)
        self.model_status = ttk.Label(self.settings_frame, text='Model: unknown')
        self.model_status.pack(anchor='w', padx=6, pady=4)
        # Menu
        self.menu = tk.Menu(self)
        file_menu = tk.Menu(self.menu, tearoff=0)
        file_menu.add_command(label="Load KB...", command=self.load_kb_file)
        file_menu.add_command(label="Save KB As...", command=self.save_kb_file)
        file_menu.add_separator()
        file_menu.add_command(label="Export Chat...", command=self.export_chat)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.on_quit)
        self.menu.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(self.menu, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu.add_cascade(label="Help", menu=help_menu)
        self.config(menu=self.menu)

    def _layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)

        self.chat.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=8, pady=8)
        self.entry.grid(row=1, column=0, sticky='ew', padx=8, pady=6)
        self.send_btn.grid(row=1, column=1, sticky='ew', padx=8, pady=6)

        # KB frame on right
        self.kb_frame.place(relx=0.66, rely=0.55, relwidth=0.32, relheight=0.35)
        self.kb_list.pack(fill='both', expand=True, padx=6, pady=6)
        btns = ttk.Frame(self.kb_frame)
        btns.pack(fill='x', padx=6, pady=4)
        self.kb_refresh_btn.pack(in_=btns, side='left', padx=2)
        self.kb_add_btn.pack(in_=btns, side='left', padx=2)
        self.kb_view_btn.pack(in_=btns, side='left', padx=2)

        self.settings_frame.place(relx=0.66, rely=0.15, relwidth=0.32, relheight=0.35)
        ttk.Label(self.settings_frame, text="Creativity:").pack(anchor='w', padx=6, pady=6)
        self.creativity_scale.pack(fill='x', padx=6, pady=4)
        self.train_btn.pack(padx=6, pady=6)

        # Initialize model status and KB list
        self._update_model_status()
        self.load_kb_to_list()
        self._post_system("Ric AI initialized. Ask me something!")

    def _bind(self):
        self.entry.bind('<Return>', lambda e: self.on_send())

    def _post_system(self, text):
        self._append_message("Ric", text)

    def _append_message(self, who, text):
        self.chat.configure(state='normal')
        self.chat.insert('end', f"{who}: {text}\n")
        self.chat.configure(state='disabled')
        self.chat.see('end')

    def on_send(self):
        text = self.entry.get().strip()
        if not text:
            return
        self._append_message("You", text)
        self.entry.delete(0, 'end')
        self.after(150, lambda: self._get_and_show_reply(text))

    def _get_and_show_reply(self, text):
        resp = self.ai.respond(text, creativity=self.creativity.get())
        self._append_message("Ric", resp)

    def load_kb_to_list(self):
        self.kb_list.delete(0, 'end')
        for e in self.ai.kb:
            q = e.get('question', '')
            self.kb_list.insert('end', f"{e.get('id')}: {q}")

    def add_kb_entry(self):
        q = simpledialog.askstring("Add Knowledge", "Question:")
        if not q:
            return
        a = simpledialog.askstring("Add Knowledge", "Answer:")
        if a is None:
            return
        entry = self.ai.add_kb_entry(q, a)
        messagebox.showinfo("Added", f"Added entry id {entry.get('id')}")
        self.load_kb_to_list()

    def view_kb_entry(self):
        sel = self.kb_list.curselection()
        if not sel:
            messagebox.showwarning("Select", "Please select an entry to view")
            return
        idx = sel[0]
        entry = self.ai.kb[idx]
        messagebox.showinfo(f"Entry {entry.get('id')}", f"Q: {entry.get('question')}\n\nA: {entry.get('answer')}")

    def train_markov(self):
        self.ai.train_markov()
        messagebox.showinfo("Trained", "Markov model trained from KB")

    def _update_model_status(self):
        t = self.ai.transformer
        if not t.is_available():
            s = "Model: transformers lib not installed"
        elif t.is_loaded():
            s = f"Model: loaded ({t.model_name}) on {t.device}"
        else:
            s = "Model: available (not loaded)"
        try:
            self.model_status.config(text=s)
        except Exception:
            pass

    def on_mode_change(self):
        new_mode = self.mode_var.get()
        self.ai.set_mode(new_mode)
        self._update_model_status()
        self._post_system(f"Mode set to {new_mode}")

    def on_load_model(self):
        if not self.ai.transformer.is_available():
            messagebox.showerror("Missing dependency", "The 'transformers' package is not installed. See README for setup instructions.")
            return
        model = simpledialog.askstring("Load Model", "Model name (e.g., gpt2):", initialvalue='gpt2')
        if not model:
            return
        try:
            self.ai.load_transformer_model(model_name=model, device='cpu')
            messagebox.showinfo("Loaded", f"Model {model} loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        self._update_model_status()

    def load_kb_file(self):
        p = filedialog.askopenfilename(title="Open KB JSON", filetypes=[("JSON","*.json"), ("All","*")])
        if not p:
            return
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Save to app's kb path
            with open(self.ai.kb_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.ai.reload_kb()
            self.load_kb_to_list()
            messagebox.showinfo("Loaded", "Knowledge base loaded")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def save_kb_file(self):
        p = filedialog.asksaveasfilename(title="Save KB JSON", defaultextension='.json', filetypes=[("JSON","*.json")])
        if not p:
            return
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(self.ai.kb, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Saved", f"Saved KB to {p}")

    def export_chat(self):
        p = filedialog.asksaveasfilename(title="Export Chat", defaultextension='.txt', filetypes=[("Text","*.txt")])
        if not p:
            return
        with open(p, 'w', encoding='utf-8') as f:
            f.write(self.chat.get('1.0', 'end'))
        messagebox.showinfo("Exported", f"Chat exported to {p}")

    def show_about(self):
        messagebox.showinfo("About Ric AI", "Ric AI - simple local assistant. No external APIs used. (Python + Tkinter)\n\nOptional online mode: you can enable 'Online' mode and load a local transformer model (requires installing 'transformers' and 'torch'). See README for instructions.")

    def on_quit(self):
        if messagebox.askokcancel("Quit", "Do you really want to quit?"):
            self.destroy()


if __name__ == '__main__':
    app = RicGUI()
    app.mainloop()
