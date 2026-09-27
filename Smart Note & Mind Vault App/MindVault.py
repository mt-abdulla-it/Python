import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import datetime
import json

# Database path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "mind_vault.db")

# Default Categories
CATEGORIES = ["General", "Work", "Ideas", "Code", "Learning", "Personal"]

def init_db():
    """Initializes the SQLite database schema and populates sample notes if empty."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            tags TEXT DEFAULT '',
            content TEXT DEFAULT '',
            is_favorite INTEGER DEFAULT 0,
            is_pinned INTEGER DEFAULT 0,
            is_archived INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.commit()

    # Check if empty; if so, insert welcome notes
    cursor.execute("SELECT COUNT(*) FROM notes")
    if cursor.fetchone()[0] == 0:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sample_notes = [
            (
                "🚀 Welcome to MindVault!",
                "General",
                "welcome, guide, setup",
                "MindVault is your intelligent, elegant personal note-taking and knowledge vault.\n\n"
                "✨ Features:\n"
                "• Categorize notes into Work, Ideas, Code, Learning, and Personal.\n"
                "• Search instantly across titles, content, and tags.\n"
                "• Pin important notes to keep them on top.\n"
                "• Favorite notes for quick access.\n"
                "• Export notes to Markdown (.md) or Text (.txt).\n"
                "• View real-time word count & character count.\n\n"
                "Press Ctrl+N for a new note, and Ctrl+S to quickly save!",
                1, 1, 0, now, now
            ),
            (
                "🐍 Python Snippets & Cheat Sheet",
                "Code",
                "python, tips, code",
                "# Quick Python Tips\n\n"
                "1. List Comprehensions:\n"
                "   squares = [x**2 for x in range(10)]\n\n"
                "2. Dictionary Unpacking:\n"
                "   merged = {**dict1, **dict2}\n\n"
                "3. SQLite Connection Pattern:\n"
                "   with sqlite3.connect('db.sqlite') as conn:\n"
                "       cursor = conn.cursor()\n"
                "       cursor.execute('SELECT * FROM table')",
                1, 0, 0, now, now
            ),
            (
                "💡 Creative Project Ideas",
                "Ideas",
                "brainstorming, app, future",
                "1. AI Powered Daily Journaling Assistant\n"
                "2. Desktop Widget for Real-Time Crypto & Stock Tickers\n"
                "3. Automated PDF Report Generator for Small Businesses\n"
                "4. Offline Markdown Editor with Instant Live Preview",
                0, 0, 0, now, now
            )
        ]
        cursor.executemany('''
            INSERT INTO notes (title, category, tags, content, is_favorite, is_pinned, is_archived, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_notes)
        conn.commit()

    conn.close()

class MindVaultApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MindVault - Smart Note & Knowledge Manager")
        self.root.geometry("1100x720")
        self.root.minsize(950, 600)

        # Color Theme (Catppuccin Mocha Palette)
        self.BG_DARK = "#181825"        # Main deep background
        self.BG_SIDEBAR = "#1e1e2e"     # Left sidebar
        self.BG_MIDDLE = "#232334"      # Notes list panel
        self.BG_EDITOR = "#181825"      # Main editor background
        self.BG_CARD = "#2b2b3d"        # Note item cards
        self.BG_CARD_SEL = "#36374f"    # Selected note card
        self.BG_INPUT = "#313244"       # Text inputs
        
        self.ACCENT_BLUE = "#89b4fa"    # Primary buttons/highlights
        self.ACCENT_GREEN = "#a6e3a1"   # Save / Success
        self.ACCENT_YELLOW = "#f9e2af"  # Favorite / Pin
        self.ACCENT_RED = "#f38ba8"     # Delete / Warning
        self.TEXT_MAIN = "#cdd6f4"      # Primary text color
        self.TEXT_MUTED = "#a6adc8"     # Subtitle / placeholder text
        self.BORDER_COLOR = "#45475a"   # Subtitle borders

        self.root.configure(bg=self.BG_DARK)

        # State Variables
        self.current_note_id = None
        self.active_nav_filter = "all"  # "all", "fav", "pin", "archive", or category name
        self.search_query = ""

        # UI Setup
        self._setup_styles()
        self._build_layout()

        # Database Init & Initial Load
        init_db()
        self.refresh_notes_list()
        self.select_first_note_or_clear()

        # Keyboard Shortcuts
        self.root.bind("<Control-n>", lambda e: self.create_new_note())
        self.root.bind("<Control-s>", lambda e: self.save_current_note())
        self.root.bind("<Control-f>", lambda e: self.entry_search.focus_set())

    def _setup_styles(self):
        """Configure ttk widget styles."""
        self.style = ttk.Style()
        self.style.theme_use("default")

        # Combobox style
        self.style.configure("TCombobox",
                             fieldbackground=self.BG_INPUT,
                             background=self.BG_CARD,
                             foreground=self.TEXT_MAIN,
                             bordercolor=self.BORDER_COLOR,
                             arrowcolor=self.TEXT_MAIN,
                             padding=5)
        self.style.map("TCombobox",
                       fieldbackground=[("readonly", self.BG_INPUT)],
                       selectbackground=[("readonly", self.BG_CARD)],
                       selectforeground=[("readonly", self.TEXT_MAIN)])

    def _build_layout(self):
        """Constructs 3-column layout: Sidebar, Note List, Editor Panel."""
        # Main Container
        self.main_container = tk.Frame(self.root, bg=self.BG_DARK)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # ==========================================
        # COLUMN 1: LEFT SIDEBAR
        # ==========================================
        self.sidebar_frame = tk.Frame(self.main_container, bg=self.BG_SIDEBAR, width=220)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)

        # App Logo / Header
        header_frame = tk.Frame(self.sidebar_frame, bg=self.BG_SIDEBAR, pady=18, padx=15)
        header_frame.pack(fill=tk.X)

        lbl_logo = tk.Label(header_frame, text="🧠 MindVault", font=("Segoe UI", 16, "bold"),
                            bg=self.BG_SIDEBAR, fg=self.ACCENT_BLUE)
        lbl_logo.pack(anchor="w")

        lbl_sub = tk.Label(header_frame, text="Smart Knowledge Base", font=("Segoe UI", 8),
                           bg=self.BG_SIDEBAR, fg=self.TEXT_MUTED)
        lbl_sub.pack(anchor="w")

        # New Note Button
        btn_new = tk.Button(self.sidebar_frame, text="➕  New Note", font=("Segoe UI", 10, "bold"),
                            bg=self.ACCENT_BLUE, fg="#11111b", activebackground="#74c7ec",
                            activeforeground="#11111b", bd=0, relief=tk.FLAT, cursor="hand2",
                            pady=8, command=self.create_new_note)
        btn_new.pack(fill=tk.X, padx=15, pady=(0, 15))

        # Navigation Links
        nav_label = tk.Label(self.sidebar_frame, text="VIEWS", font=("Segoe UI", 8, "bold"),
                             bg=self.BG_SIDEBAR, fg=self.TEXT_MUTED)
        nav_label.pack(anchor="w", padx=15, pady=(5, 5))

        self.nav_buttons = {}
        nav_items = [
            ("all", "📝  All Notes"),
            ("fav", "⭐  Favorites"),
            ("pin", "📌  Pinned Notes"),
            ("archive", "📥  Archive")
        ]

        for key, text in nav_items:
            btn = tk.Button(self.sidebar_frame, text=text, font=("Segoe UI", 10),
                            bg=self.BG_SIDEBAR, fg=self.TEXT_MAIN, activebackground=self.BG_CARD,
                            activeforeground=self.ACCENT_BLUE, bd=0, relief=tk.FLAT, anchor="w",
                            padx=15, pady=6, cursor="hand2",
                            command=lambda k=key: self.set_nav_filter(k))
            btn.pack(fill=tk.X)
            self.nav_buttons[key] = btn

        # Categories Section
        cat_label = tk.Label(self.sidebar_frame, text="CATEGORIES", font=("Segoe UI", 8, "bold"),
                             bg=self.BG_SIDEBAR, fg=self.TEXT_MUTED)
        cat_label.pack(anchor="w", padx=15, pady=(15, 5))

        for cat in CATEGORIES:
            cat_key = f"cat_{cat}"
            btn = tk.Button(self.sidebar_frame, text=f"🏷️  {cat}", font=("Segoe UI", 9),
                            bg=self.BG_SIDEBAR, fg=self.TEXT_MAIN, activebackground=self.BG_CARD,
                            activeforeground=self.ACCENT_BLUE, bd=0, relief=tk.FLAT, anchor="w",
                            padx=15, pady=5, cursor="hand2",
                            command=lambda c=cat: self.set_nav_filter(f"cat_{c}"))
            btn.pack(fill=tk.X)
            self.nav_buttons[cat_key] = btn

        # Sidebar Footer: Stats Button
        btn_stats = tk.Button(self.sidebar_frame, text="📊 Vault Analytics", font=("Segoe UI", 9),
                              bg=self.BG_CARD, fg=self.TEXT_MAIN, activebackground=self.ACCENT_BLUE,
                              activeforeground="#11111b", bd=0, relief=tk.FLAT, cursor="hand2",
                              pady=6, command=self.show_analytics_dialog)
        btn_stats.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=15)

        # Highlighting initial nav
        self._update_nav_highlight()

        # ==========================================
        # COLUMN 2: NOTES LIST PANEL
        # ==========================================
        self.list_panel = tk.Frame(self.main_container, bg=self.BG_MIDDLE, width=300)
        self.list_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.list_panel.pack_propagate(False)

        # Search Bar Box
        search_frame = tk.Frame(self.list_panel, bg=self.BG_MIDDLE, pady=15, padx=12)
        self.search_var = tk.StringVar()

        self.entry_search = tk.Entry(search_frame, textvariable=self.search_var,
                                     font=("Segoe UI", 10), bg=self.BG_INPUT, fg=self.TEXT_MAIN,
                                     insertbackground=self.TEXT_MAIN, bd=0, relief=tk.FLAT)
        self.entry_search.pack(fill=tk.X, ipady=6, ipadx=8)
        self.entry_search.insert(0, "🔍 Search notes...")
        self.search_var.trace_add("write", lambda *args: self.on_search_change())
        self.entry_search.bind("<FocusIn>", self._clear_search_placeholder)
        self.entry_search.bind("<FocusOut>", self._restore_search_placeholder)

        # Count Indicator
        self.lbl_notes_count = tk.Label(self.list_panel, text="0 Notes", font=("Segoe UI", 8, "bold"),
                                        bg=self.BG_MIDDLE, fg=self.TEXT_MUTED)
        self.lbl_notes_count.pack(anchor="w", padx=15, pady=(0, 5))

        # Canvas & Scrollbar for Card List
        list_container = tk.Frame(self.list_panel, bg=self.BG_MIDDLE)
        list_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 10))

        self.canvas = tk.Canvas(list_container, bg=self.BG_MIDDLE, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)

        self.cards_inner_frame = tk.Frame(self.canvas, bg=self.BG_MIDDLE)
        self.cards_inner_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.cards_inner_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mouse wheel scrolling on notes list
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # ==========================================
        # COLUMN 3: MAIN NOTE EDITOR PANEL
        # ==========================================
        self.editor_panel = tk.Frame(self.main_container, bg=self.BG_EDITOR)
        self.editor_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Editor Toolbar Header
        self.toolbar = tk.Frame(self.editor_panel, bg=self.BG_SIDEBAR, pady=10, padx=15)
        self.toolbar.pack(fill=tk.X)

        # Category Dropdown
        tk.Label(self.toolbar, text="Category:", font=("Segoe UI", 9),
                 bg=self.BG_SIDEBAR, fg=self.TEXT_MUTED).pack(side=tk.LEFT, padx=(0, 5))
        
        self.combo_category = ttk.Combobox(self.toolbar, values=CATEGORIES, state="readonly", width=12)
        self.combo_category.pack(side=tk.LEFT, padx=(0, 15))
        self.combo_category.set("General")

        # Tags Entry
        tk.Label(self.toolbar, text="Tags:", font=("Segoe UI", 9),
                 bg=self.BG_SIDEBAR, fg=self.TEXT_MUTED).pack(side=tk.LEFT, padx=(0, 5))

        self.entry_tags = tk.Entry(self.toolbar, font=("Segoe UI", 9), bg=self.BG_INPUT,
                                   fg=self.TEXT_MAIN, insertbackground=self.TEXT_MAIN, bd=0, relief=tk.FLAT, width=20)
        self.entry_tags.pack(side=tk.LEFT, ipady=4, ipadx=5, padx=(0, 15))

        # Action Buttons on Top Toolbar
        self.btn_fav = tk.Button(self.toolbar, text="⭐", font=("Segoe UI", 11),
                                 bg=self.BG_CARD, fg=self.TEXT_MUTED, activebackground=self.BG_CARD_SEL,
                                 bd=0, relief=tk.FLAT, cursor="hand2", width=3, command=self.toggle_favorite)
        self.btn_fav.pack(side=tk.RIGHT, padx=3)

        self.btn_pin = tk.Button(self.toolbar, text="📌", font=("Segoe UI", 11),
                                 bg=self.BG_CARD, fg=self.TEXT_MUTED, activebackground=self.BG_CARD_SEL,
                                 bd=0, relief=tk.FLAT, cursor="hand2", width=3, command=self.toggle_pin)
        self.btn_pin.pack(side=tk.RIGHT, padx=3)

        self.btn_export = tk.Button(self.toolbar, text="📤 Export", font=("Segoe UI", 9, "bold"),
                                    bg=self.BG_CARD, fg=self.TEXT_MAIN, activebackground=self.ACCENT_BLUE,
                                    activeforeground="#11111b", bd=0, relief=tk.FLAT, cursor="hand2",
                                    padx=10, pady=3, command=self.export_note)
        self.btn_export.pack(side=tk.RIGHT, padx=3)

        self.btn_save = tk.Button(self.toolbar, text="💾 Save", font=("Segoe UI", 9, "bold"),
                                   bg=self.ACCENT_GREEN, fg="#11111b", activebackground="#a6e3a1",
                                   bd=0, relief=tk.FLAT, cursor="hand2", padx=12, pady=3,
                                   command=self.save_current_note)
        self.btn_save.pack(side=tk.RIGHT, padx=3)

        self.btn_delete = tk.Button(self.toolbar, text="🗑️", font=("Segoe UI", 11),
                                    bg=self.BG_CARD, fg=self.ACCENT_RED, activebackground=self.ACCENT_RED,
                                    activeforeground="#11111b", bd=0, relief=tk.FLAT, cursor="hand2", width=3,
                                    command=self.delete_current_note)
        self.btn_delete.pack(side=tk.RIGHT, padx=3)

        # Title Input Field
        title_frame = tk.Frame(self.editor_panel, bg=self.BG_EDITOR, padx=20, pady=10)
        title_frame.pack(fill=tk.X)

        self.entry_title = tk.Entry(title_frame, font=("Segoe UI", 16, "bold"),
                                    bg=self.BG_EDITOR, fg=self.TEXT_MAIN, insertbackground=self.TEXT_MAIN,
                                    bd=0, relief=tk.FLAT)
        self.entry_title.pack(fill=tk.X, ipady=4)
        self.entry_title.insert(0, "Untitled Note")

        # Divider line
        divider = tk.Frame(self.editor_panel, bg=self.BORDER_COLOR, height=1)
        divider.pack(fill=tk.X, padx=20)

        # Main Text Editor Area
        editor_container = tk.Frame(self.editor_panel, bg=self.BG_EDITOR, padx=20, pady=10)
        editor_container.pack(fill=tk.BOTH, expand=True)

        self.txt_editor = tk.Text(editor_container, font=("Consolas", 11),
                                  bg=self.BG_EDITOR, fg=self.TEXT_MAIN, insertbackground=self.TEXT_MAIN,
                                  selectbackground=self.BG_CARD_SEL, selectforeground=self.TEXT_MAIN,
                                  bd=0, relief=tk.FLAT, undo=True, wrap=tk.WORD)
        self.txt_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        editor_scroll = ttk.Scrollbar(editor_container, orient="vertical", command=self.txt_editor.yview)
        editor_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_editor.configure(yscrollcommand=editor_scroll.set)

        self.txt_editor.bind("<KeyRelease>", self._update_status_bar)

        # Status Bar at Bottom
        self.statusbar = tk.Frame(self.editor_panel, bg=self.BG_SIDEBAR, pady=6, padx=20)
        self.statusbar.pack(fill=tk.X)

        self.lbl_status_words = tk.Label(self.statusbar, text="Words: 0 | Chars: 0", font=("Segoe UI", 9),
                                         bg=self.BG_SIDEBAR, fg=self.TEXT_MUTED)
        self.lbl_status_words.pack(side=tk.LEFT)

        self.lbl_status_time = tk.Label(self.statusbar, text="Ready", font=("Segoe UI", 9),
                                        bg=self.BG_SIDEBAR, fg=self.TEXT_MUTED)
        self.lbl_status_time.pack(side=tk.RIGHT)

    # ==========================================
    # LOGIC & EVENT HANDLERS
    # ==========================================

    def _on_mousewheel(self, event):
        """Scroll cards list on mouse wheel."""
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            # Linux scroll events
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def _clear_search_placeholder(self, event):
        if self.entry_search.get() == "🔍 Search notes...":
            self.entry_search.delete(0, tk.END)
            self.entry_search.config(fg=self.TEXT_MAIN)

    def _restore_search_placeholder(self, event):
        if not self.entry_search.get().strip():
            self.entry_search.delete(0, tk.END)
            self.entry_search.insert(0, "🔍 Search notes...")
            self.entry_search.config(fg=self.TEXT_MUTED)

    def on_search_change(self):
        val = self.search_var.get().strip()
        if val == "🔍 Search notes...":
            self.search_query = ""
        else:
            self.search_query = val
        self.refresh_notes_list()

    def set_nav_filter(self, key):
        self.active_nav_filter = key
        self._update_nav_highlight()
        self.refresh_notes_list()
        self.select_first_note_or_clear()

    def _update_nav_highlight(self):
        for k, btn in self.nav_buttons.items():
            if k == self.active_nav_filter:
                btn.config(bg=self.BG_CARD_SEL, fg=self.ACCENT_BLUE, font=("Segoe UI", 10, "bold"))
            else:
                btn.config(bg=self.BG_SIDEBAR, fg=self.TEXT_MAIN, font=("Segoe UI", 10))

    def refresh_notes_list(self):
        """Fetches filtered notes from DB and dynamically builds UI cards."""
        if not hasattr(self, 'cards_inner_frame'):
            return

        # Clear existing card widgets
        for widget in self.cards_inner_frame.winfo_children():
            widget.destroy()

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        query = "SELECT id, title, category, tags, content, is_favorite, is_pinned, updated_at FROM notes WHERE 1=1"
        params = []

        # Filter handling
        if self.active_nav_filter == "fav":
            query += " AND is_favorite = 1 AND is_archived = 0"
        elif self.active_nav_filter == "pin":
            query += " AND is_pinned = 1 AND is_archived = 0"
        elif self.active_nav_filter == "archive":
            query += " AND is_archived = 1"
        elif self.active_nav_filter.startswith("cat_"):
            cat_name = self.active_nav_filter.replace("cat_", "")
            query += " AND category = ? AND is_archived = 0"
            params.append(cat_name)
        else:  # "all"
            query += " AND is_archived = 0"

        # Search query filter
        if self.search_query:
            query += " AND (title LIKE ? OR content LIKE ? OR tags LIKE ?)"
            like_str = f"%{self.search_query}%"
            params.extend([like_str, like_str, like_str])

        # Order by pinned first, then updated_at desc
        query += " ORDER BY is_pinned DESC, updated_at DESC"

        cursor.execute(query, params)
        notes = cursor.fetchall()
        conn.close()

        self.lbl_notes_count.config(text=f"{len(notes)} Note{'s' if len(notes) != 1 else ''}")

        for note in notes:
            n_id, title, category, tags, content, is_fav, is_pin, updated_at = note
            self._create_note_card(n_id, title, category, content, is_fav, is_pin, updated_at)

    def _create_note_card(self, n_id, title, category, content, is_fav, is_pin, updated_at):
        """Builds a single styled card widget for note list."""
        is_selected = (n_id == self.current_note_id)
        card_bg = self.BG_CARD_SEL if is_selected else self.BG_CARD

        card = tk.Frame(self.cards_inner_frame, bg=card_bg, pady=8, padx=10, cursor="hand2")
        card.pack(fill=tk.X, pady=4)

        # Highlight border if selected
        if is_selected:
            card.config(highlightbackground=self.ACCENT_BLUE, highlightthickness=1)

        # Title Row
        title_row = tk.Frame(card, bg=card_bg)
        title_row.pack(fill=tk.X)

        icons_text = ""
        if is_pin: icons_text += "📌 "
        if is_fav: icons_text += "⭐ "

        display_title = title if title.strip() else "Untitled Note"
        lbl_title = tk.Label(title_row, text=f"{icons_text}{display_title}", font=("Segoe UI", 10, "bold"),
                             bg=card_bg, fg=self.ACCENT_BLUE if is_selected else self.TEXT_MAIN, anchor="w")
        lbl_title.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Category Badge
        cat_badge = tk.Label(title_row, text=category, font=("Segoe UI", 7, "bold"),
                             bg=self.BG_INPUT, fg=self.TEXT_MUTED, padx=5, pady=1)
        cat_badge.pack(side=tk.RIGHT)

        # Snippet (first 2 lines truncated)
        snippet_text = content.replace("\n", " ").strip()
        if len(snippet_text) > 55:
            snippet_text = snippet_text[:55] + "..."
        if not snippet_text:
            snippet_text = "No additional text..."

        lbl_snippet = tk.Label(card, text=snippet_text, font=("Segoe UI", 9),
                               bg=card_bg, fg=self.TEXT_MUTED, anchor="w", justify=tk.LEFT)
        lbl_snippet.pack(fill=tk.X, pady=(3, 3))

        # Date Footer
        lbl_date = tk.Label(card, text=updated_at, font=("Segoe UI", 8),
                            bg=card_bg, fg=self.BORDER_COLOR, anchor="w")
        lbl_date.pack(fill=tk.X)

        # Click event binding to card and children
        for widget in (card, title_row, lbl_title, cat_badge, lbl_snippet, lbl_date):
            widget.bind("<Button-1>", lambda e, nid=n_id: self.load_note_into_editor(nid))

    def select_first_note_or_clear(self):
        """Loads the first note in current view or opens a blank slate."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        query = "SELECT id FROM notes WHERE is_archived = 0 ORDER BY is_pinned DESC, updated_at DESC LIMIT 1"
        cursor.execute(query)
        row = cursor.fetchone()
        conn.close()

        if row:
            self.load_note_into_editor(row[0])
        else:
            self.create_new_note()

    def load_note_into_editor(self, note_id):
        """Loads note data into right editor pane."""
        self.current_note_id = note_id

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT title, category, tags, content, is_favorite, is_pinned, is_archived, updated_at FROM notes WHERE id = ?", (note_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return

        title, category, tags, content, is_fav, is_pin, is_arch, updated_at = row

        # Set input fields
        self.entry_title.delete(0, tk.END)
        self.entry_title.insert(0, title)

        self.combo_category.set(category if category in CATEGORIES else "General")

        self.entry_tags.delete(0, tk.END)
        self.entry_tags.insert(0, tags)

        self.txt_editor.delete("1.0", tk.END)
        self.txt_editor.insert("1.0", content)

        # Update Fav / Pin Button Visuals
        self.btn_fav.config(fg=self.ACCENT_YELLOW if is_fav else self.TEXT_MUTED)
        self.btn_pin.config(fg=self.ACCENT_YELLOW if is_pin else self.TEXT_MUTED)

        # Refresh list highlight
        self.refresh_notes_list()
        self._update_status_bar()
        self.lbl_status_time.config(text=f"Last updated: {updated_at}")

    def save_current_note(self):
        """Saves or inserts current note to database."""
        title = self.entry_title.get().strip() or "Untitled Note"
        category = self.combo_category.get()
        tags = self.entry_tags.get().strip()
        content = self.txt_editor.get("1.0", tk.END).strip()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        if self.current_note_id is None:
            # Create new
            cursor.execute('''
                INSERT INTO notes (title, category, tags, content, is_favorite, is_pinned, is_archived, created_at, updated_at)
                VALUES (?, ?, ?, ?, 0, 0, 0, ?, ?)
            ''', (title, category, tags, content, now_str, now_str))
            self.current_note_id = cursor.lastrowid
        else:
            # Update existing
            cursor.execute('''
                UPDATE notes
                SET title = ?, category = ?, tags = ?, content = ?, updated_at = ?
                WHERE id = ?
            ''', (title, category, tags, content, now_str, self.current_note_id))

        conn.commit()
        conn.close()

        self.lbl_status_time.config(text=f"Saved at {now_str}")
        self.refresh_notes_list()

    def create_new_note(self):
        """Resets editor fields for new note."""
        self.current_note_id = None
        self.entry_title.delete(0, tk.END)
        self.entry_title.insert(0, "Untitled Note")
        self.combo_category.set("General")
        self.entry_tags.delete(0, tk.END)
        self.txt_editor.delete("1.0", tk.END)

        self.btn_fav.config(fg=self.TEXT_MUTED)
        self.btn_pin.config(fg=self.TEXT_MUTED)

        self.entry_title.focus_set()
        self.entry_title.select_range(0, tk.END)
        self._update_status_bar()
        self.lbl_status_time.config(text="New unsaved note")

    def toggle_favorite(self):
        if self.current_note_id is None:
            return
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT is_favorite FROM notes WHERE id = ?", (self.current_note_id,))
        row = cursor.fetchone()
        if row:
            new_val = 1 if row[0] == 0 else 0
            cursor.execute("UPDATE notes SET is_favorite = ? WHERE id = ?", (new_val, self.current_note_id))
            conn.commit()
            self.btn_fav.config(fg=self.ACCENT_YELLOW if new_val else self.TEXT_MUTED)
        conn.close()
        self.refresh_notes_list()

    def toggle_pin(self):
        if self.current_note_id is None:
            return
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT is_pinned FROM notes WHERE id = ?", (self.current_note_id,))
        row = cursor.fetchone()
        if row:
            new_val = 1 if row[0] == 0 else 0
            cursor.execute("UPDATE notes SET is_pinned = ? WHERE id = ?", (new_val, self.current_note_id))
            conn.commit()
            self.btn_pin.config(fg=self.ACCENT_YELLOW if new_val else self.TEXT_MUTED)
        conn.close()
        self.refresh_notes_list()

    def delete_current_note(self):
        if self.current_note_id is None:
            return
        
        confirm = messagebox.askyesno("Delete Note", "Are you sure you want to delete this note permanently?")
        if confirm:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE id = ?", (self.current_note_id,))
            conn.commit()
            conn.close()

            self.select_first_note_or_clear()

    def export_note(self):
        """Exports the active note to a Markdown or TXT file."""
        title = self.entry_title.get().strip() or "Untitled"
        content = self.txt_editor.get("1.0", tk.END).strip()
        category = self.combo_category.get()
        tags = self.entry_tags.get().strip()

        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown Files", "*.md"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=f"{title.replace(' ', '_')}.md"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n")
                f.write(f"**Category:** {category}  \n")
                if tags:
                    f.write(f"**Tags:** {tags}  \n")
                f.write("---\n\n")
                f.write(content)
            messagebox.showinfo("Export Successful", f"Note exported successfully to:\n{file_path}")

    def _update_status_bar(self, event=None):
        content = self.txt_editor.get("1.0", tk.END)
        chars = len(content) - 1  # Exclude trailing newline
        words = len(content.split())
        self.lbl_status_words.config(text=f"Words: {words:,} | Chars: {chars:,}")

    def show_analytics_dialog(self):
        """Displays popup window showing vault stats and breakdown."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*), SUM(is_favorite), SUM(is_pinned) FROM notes WHERE is_archived = 0")
        total_notes, fav_count, pin_count = cursor.fetchone()
        fav_count = fav_count or 0
        pin_count = pin_count or 0

        cursor.execute("SELECT category, COUNT(*) FROM notes WHERE is_archived = 0 GROUP BY category")
        cat_data = cursor.fetchall()

        cursor.execute("SELECT content FROM notes WHERE is_archived = 0")
        all_contents = cursor.fetchall()
        total_words = sum(len(row[0].split()) for row in all_contents)

        conn.close()

        # Build Dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Vault Analytics")
        dialog.geometry("380x420")
        dialog.configure(bg=self.BG_DARK)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="📊 Vault Analytics & Summary", font=("Segoe UI", 13, "bold"),
                 bg=self.BG_DARK, fg=self.ACCENT_BLUE, pady=12).pack()

        stats_frame = tk.Frame(dialog, bg=self.BG_CARD, padx=15, pady=15)
        stats_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(stats_frame, text=f"• Total Active Notes:  {total_notes}", font=("Segoe UI", 10),
                 bg=self.BG_CARD, fg=self.TEXT_MAIN, anchor="w").pack(fill=tk.X, pady=2)
        tk.Label(stats_frame, text=f"• Favorite Notes:  ⭐ {fav_count}", font=("Segoe UI", 10),
                 bg=self.BG_CARD, fg=self.TEXT_MAIN, anchor="w").pack(fill=tk.X, pady=2)
        tk.Label(stats_frame, text=f"• Pinned Notes:  📌 {pin_count}", font=("Segoe UI", 10),
                 bg=self.BG_CARD, fg=self.TEXT_MAIN, anchor="w").pack(fill=tk.X, pady=2)
        tk.Label(stats_frame, text=f"• Total Words Logged:  📝 {total_words:,}", font=("Segoe UI", 10),
                 bg=self.BG_CARD, fg=self.TEXT_MAIN, anchor="w").pack(fill=tk.X, pady=2)

        tk.Label(dialog, text="Category Breakdown:", font=("Segoe UI", 10, "bold"),
                 bg=self.BG_DARK, fg=self.TEXT_MUTED, anchor="w").pack(fill=tk.X, padx=20, pady=(15, 5))

        cat_frame = tk.Frame(dialog, bg=self.BG_CARD, padx=15, pady=10)
        cat_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        for cat, count in cat_data:
            row = tk.Frame(cat_frame, bg=self.BG_CARD)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=f"🏷️ {cat}", font=("Segoe UI", 10), bg=self.BG_CARD, fg=self.TEXT_MAIN).pack(side=tk.LEFT)
            tk.Label(row, text=f"{count} notes", font=("Segoe UI", 10, "bold"), bg=self.BG_CARD, fg=self.ACCENT_BLUE).pack(side=tk.RIGHT)

        tk.Button(dialog, text="Close", font=("Segoe UI", 10, "bold"), bg=self.ACCENT_BLUE, fg="#11111b",
                  bd=0, relief=tk.FLAT, cursor="hand2", padx=20, pady=5, command=dialog.destroy).pack(pady=10)

def main():
    root = tk.Tk()
    app = MindVaultApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
