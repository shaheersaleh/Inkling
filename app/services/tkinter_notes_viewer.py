import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import webbrowser
from datetime import datetime


class NotesViewer:
    def __init__(self):
        self.root = None
        self.sources_queue = queue.Queue()
        self.running = False
        
    def create_window(self):
        """Create the tkinter window for displaying notes"""
        self.root = tk.Tk()
        self.root.title("Digital Notes - Full Content Viewer")
        self.root.geometry("800x900")  # Increased size for full content
        self.root.configure(bg='#2E4057')  # indigo_dye color
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Custom.TFrame', background='#2E4057')
        style.configure('Custom.TLabel', background='#2E4057', foreground='white')
        style.configure('Header.TLabel', background='#2E4057', foreground='#6DB4EE', font=('Arial', 14, 'bold'))
        style.configure('Source.TLabel', background='#2E4057', foreground='#B8D4E3', font=('Arial', 10))
        
        # Main frame
        main_frame = ttk.Frame(self.root, style='Custom.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_label = ttk.Label(main_frame, text="📚 Source Notes", style='Header.TLabel')
        header_label.pack(pady=(0, 10))
        
        # Scrollable frame for sources
        canvas = tk.Canvas(main_frame, bg='#2E4057', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style='Custom.TFrame')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Initial message
        self.show_waiting_message()
        
        # Start checking for updates
        self.root.after(100, self.check_queue)
        
        return self.root
    
    def show_waiting_message(self):
        """Show waiting message when no sources are available"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        waiting_frame = ttk.Frame(self.scrollable_frame, style='Custom.TFrame')
        waiting_frame.pack(fill=tk.X, pady=20)
        
        waiting_label = ttk.Label(
            waiting_frame, 
            text="🤖 Ask a question in the chat to see\nrelevant source notes here!", 
            style='Source.TLabel',
            justify=tk.CENTER
        )
        waiting_label.pack(pady=20)
    
    def update_sources(self, sources_data):
        """Update the sources display with new data"""
        # Clear existing sources
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not sources_data or not sources_data.get('sources'):
            self.show_waiting_message()
            return
        
        sources = sources_data.get('sources', [])
        question = sources_data.get('question', 'Recent Query')
        
        # Question header
        question_frame = ttk.Frame(self.scrollable_frame, style='Custom.TFrame')
        question_frame.pack(fill=tk.X, pady=(0, 10))
        
        question_label = ttk.Label(
            question_frame,
            text=f"💭 Query: {question[:50]}..." if len(question) > 50 else f"💭 Query: {question}",
            style='Header.TLabel',
            wraplength=450
        )
        question_label.pack(anchor='w')
        
        # Sources
        for i, source in enumerate(sources, 1):
            self.create_source_widget(source, i)
    
    def create_source_widget(self, source, index):
        """Create a widget for displaying a single source note"""
        # Main source frame
        source_frame = ttk.LabelFrame(
            self.scrollable_frame, 
            text=f"📄 {source.get('title', 'Untitled')[:40]}",
            style='Custom.TFrame'
        )
        source_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Note info header
        info_frame = ttk.Frame(source_frame, style='Custom.TFrame')
        info_frame.pack(fill=tk.X, pady=5)
        
        # Subject and date in header
        if source.get('subject'):
            subject_label = ttk.Label(
                info_frame,
                text=f"📚 {source['subject']}",
                style='Source.TLabel',
                font=('Arial', 10, 'bold')
            )
            subject_label.pack(anchor='w')
        
        if source.get('created_at'):
            date_label = ttk.Label(
                info_frame,
                text=f"📅 {source['created_at']}",
                style='Source.TLabel'
            )
            date_label.pack(anchor='w')
        
        # Relevance score
        if source.get('similarity_score'):
            score = float(source['similarity_score'])
            score_text = f"🎯 Relevance: {score:.1%}"
            score_label = ttk.Label(
                info_frame,
                text=score_text,
                style='Source.TLabel'
            )
            score_label.pack(anchor='w')
        
        # Full content display (scrollable)
        content = source.get('content', '')
        if content:
            content_label = ttk.Label(
                source_frame,
                text="📝 Full Content:",
                style='Source.TLabel',
                font=('Arial', 10, 'bold')
            )
            content_label.pack(anchor='w', pady=(10, 5))
            
            content_text = scrolledtext.ScrolledText(
                source_frame,
                height=12,  # Increased height for full content
                width=60,   # Increased width
                bg='#F8F9FA',
                fg='#2E4057',
                font=('Arial', 10),
                wrap=tk.WORD,
                padx=10,
                pady=10
            )
            content_text.pack(fill=tk.BOTH, expand=True, pady=5)
            content_text.insert(tk.END, content)
            content_text.config(state=tk.DISABLED)
        
        # Action buttons frame
        buttons_frame = ttk.Frame(source_frame, style='Custom.TFrame')
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # View full note button
        if source.get('note_id'):
            view_btn = tk.Button(
                buttons_frame,
                text="🔗 View in Browser",
                bg='#6DB4EE',
                fg='white',
                font=('Arial', 9),
                command=lambda nid=source['note_id']: self.open_note_in_browser(nid)
            )
            view_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Copy content button
        copy_btn = tk.Button(
            buttons_frame,
            text="📋 Copy Content",
            bg='#2E4057',
            fg='white',
            font=('Arial', 9),
            command=lambda: self.copy_to_clipboard(content)
        )
        copy_btn.pack(side=tk.LEFT)
    
    def open_note_in_browser(self, note_id):
        """Open the full note in the web browser"""
        url = f"http://localhost:5002/notes/{note_id}"
        webbrowser.open(url)
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()  # Now it stays on the clipboard after the window is closed
            
            # Show brief feedback
            self.show_notification("📋 Content copied to clipboard!")
        except Exception as e:
            print(f"Failed to copy to clipboard: {e}")
    
    def show_notification(self, message):
        """Show a brief notification in the window"""
        if not self.root:
            return
            
        # Create notification label
        notification = tk.Label(
            self.root,
            text=message,
            bg='#6DB4EE',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=10,
            pady=5
        )
        notification.place(relx=0.5, rely=0.1, anchor='center')
        
        # Remove after 2 seconds
        self.root.after(2000, notification.destroy)
    
    def check_queue(self):
        """Check for new sources data from the queue"""
        try:
            while True:
                sources_data = self.sources_queue.get_nowait()
                self.update_sources(sources_data)
        except queue.Empty:
            pass
        
        if self.running:
            self.root.after(100, self.check_queue)
    
    def add_sources(self, sources_data):
        """Add new sources data to the queue"""
        self.sources_queue.put(sources_data)
    
    def start(self):
        """Start the tkinter window in a separate thread"""
        self.running = True
        
        def run_tkinter():
            root = self.create_window()
            try:
                root.mainloop()
            except tk.TclError:
                pass
            finally:
                self.running = False
        
        thread = threading.Thread(target=run_tkinter, daemon=True)
        thread.start()
        return thread
    
    def stop(self):
        """Stop the tkinter window"""
        self.running = False
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except tk.TclError:
                pass


# Global instance
notes_viewer = NotesViewer()


def start_notes_viewer():
    """Start the notes viewer window"""
    return notes_viewer.start()


def update_notes_display(sources_data):
    """Update the notes display with new sources"""
    notes_viewer.add_sources(sources_data)


def stop_notes_viewer():
    """Stop the notes viewer window"""
    notes_viewer.stop()
