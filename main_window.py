# main_window.py (PyQt6)
from __future__ import annotations
import sys, time
from typing import Optional

from PyQt6 import QtCore, QtGui, QtWidgets

# Backend
from cloud_vault.db import (
    add_entry, update_entry, delete_entry, list_entries, get_entry, Vault
)

# ---------------- Table Model ----------------

class EntryTableModel(QtCore.QAbstractTableModel):
    COLS = ["Title", "URL", "Username", "Host", "Updated"]

    def __init__(self, vault: Vault):
        super().__init__()
        self.vault = vault
        self._rows = []  # list of dicts from list_entries()
        self.refresh()

    def refresh(self):
        self.beginResetModel()
        self._rows = list_entries(self.vault)
        self.endResetModel()

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.COLS)

    def data(self, index: QtCore.QModelIndex, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._rows)):
            return None
        r = self._rows[index.row()]
        col = index.column()
        if role in (QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.EditRole):
            if col == 0: return r["title"]
            if col == 1: return r["url"]
            if col == 2: return r["username"]
            if col == 3: return r["host"]
            if col == 4:
                # human-ish timestamp
                return time.strftime("%Y-%m-%d %H:%M", time.localtime(r["updated_at"]))
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if role != QtCore.Qt.ItemDataRole.DisplayRole: return None
        if orientation == QtCore.Qt.Orientation.Horizontal and 0 <= section < len(self.COLS):
            return self.COLS[section]
        return None

    def entry_id_at(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._rows):
            return self._rows[row]["id"]
        return None

# --------------- Add/Edit Dialog ---------------

class EntryDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, title="Add Entry", data=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        self.e_title = QtWidgets.QLineEdit()
        self.e_url = QtWidgets.QLineEdit()
        self.e_username = QtWidgets.QLineEdit()
        self.e_password = QtWidgets.QLineEdit()
        self.e_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.chk_show = QtWidgets.QCheckBox("Show")
        self.e_notes = QtWidgets.QPlainTextEdit()
        self.e_notes.setMinimumHeight(80)

        self.chk_show.toggled.connect(
            lambda on: self.e_password.setEchoMode(
                QtWidgets.QLineEdit.EchoMode.Normal if on else QtWidgets.QLineEdit.EchoMode.Password
            )
        )

        form = QtWidgets.QFormLayout()
        form.addRow("Title*", self.e_title)
        form.addRow("URL", self.e_url)
        pw_row = QtWidgets.QHBoxLayout()
        pw_row.addWidget(self.e_password, 1)
        pw_row.addWidget(self.chk_show)
        form.addRow("Username", self.e_username)
        form.addRow("Password", QtWidgets.QWidget())
        form.addRow(pw_row)
        form.addRow("Notes", self.e_notes)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        outer = QtWidgets.QVBoxLayout(self)
        outer.addLayout(form)
        outer.addWidget(btns)

        if data:
            self.e_title.setText(data.get("title", ""))
            self.e_url.setText(data.get("url", ""))
            self.e_username.setText(data.get("username", ""))
            # password stays blank unless editing with reveal (we’ll fetch on demand)
            self.e_notes.setPlainText(data.get("notes", ""))

    def values(self):
        title = self.e_title.text().strip()
        if not title:
            QtWidgets.QMessageBox.warning(self, "Missing", "Title is required.")
            return None
        return {
            "title": title,
            "url": self.e_url.text().strip(),
            "username": self.e_username.text(),
            "password": self.e_password.text(),
            "notes": self.e_notes.toPlainText(),
        }

# --------------- Main Window ---------------

class VaultMainWindow(QtWidgets.QMainWindow):
    def __init__(self, vault: Vault, db_path: str, autoclipper_seconds: int = 15):
        super().__init__()
        self.vault = vault
        self.db_path = db_path
        self.autoclipper_seconds = autoclipper_seconds

        self.setWindowTitle("Lock Box — Vault")
        self.resize(900, 540)

        # Model + filter
        self.model = EntryTableModel(self.vault)
        self.proxy = QtCore.QSortFilterProxyModel(self)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)  # search all columns
        self.proxy.setSourceModel(self.model)

        # Table
        self.table = QtWidgets.QTableView()
        self.table.setModel(self.proxy)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)

        # Search
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search title, url, username, host…")
        self.search.textChanged.connect(self.proxy.setFilterFixedString)

        # Toolbar actions
        act_add = QtGui.QAction("Add", self)
        act_edit = QtGui.QAction("Edit", self)
        act_del = QtGui.QAction("Delete", self)
        act_copy = QtGui.QAction("Copy Password", self)
        act_refresh = QtGui.QAction("Refresh", self)
        act_lock = QtGui.QAction("Lock", self)

        act_add.triggered.connect(self.on_add)
        act_edit.triggered.connect(self.on_edit)
        act_del.triggered.connect(self.on_delete)
        act_copy.triggered.connect(self.on_copy_password)
        act_refresh.triggered.connect(self.on_refresh)
        act_lock.triggered.connect(self.on_lock)

        tb = self.addToolBar("Main")
        tb.addAction(act_add)
        tb.addAction(act_edit)
        tb.addAction(act_del)
        tb.addSeparator()
        tb.addAction(act_copy)
        tb.addSeparator()
        tb.addAction(act_refresh)
        tb.addSeparator()
        tb.addAction(act_lock)

        # Central layout
        central = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(central)
        lay.addWidget(self.search)
        lay.addWidget(self.table, 1)
        self.setCentralWidget(central)

        # Status bar
        self.statusBar().showMessage(f"Opened: {self.db_path}")

        # Keyboard shortcuts
        act_add.setShortcut(QtGui.QKeySequence.StandardKey.New)
        act_copy.setShortcut(QtGui.QKeySequence("Ctrl+Shift+C"))

    # ---- helpers ----
    def _selected_entry_id(self) -> Optional[int]:
        sel = self.table.selectionModel().selectedRows()
        if not sel: return None
        proxy_row = sel[0].row()
        src_row = self.proxy.mapToSource(self.proxy.index(proxy_row, 0)).row()
        return self.model.entry_id_at(src_row)

    def _confirm(self, title: str, text: str) -> bool:
        resp = QtWidgets.QMessageBox.question(
            self, title, text,
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        return resp == QtWidgets.QMessageBox.StandardButton.Yes

    # ---- actions ----
    def on_add(self):
        dlg = EntryDialog(self, "Add Entry")
        if dlg.exec():
            vals = dlg.values()
            if not vals: return
            add_entry(self.vault, **vals)  # AES-GCM handled in backend
            self.model.refresh()
            self.statusBar().showMessage("Entry added.", 3000)

    def on_edit(self):
        eid = self._selected_entry_id()
        if eid is None:
            QtWidgets.QMessageBox.information(self, "Select", "Select a row to edit.")
            return
        # Fetch with password/notes so dialog can optionally change them
        cur = get_entry(self.vault, eid, reveal_password=True)
        dlg = EntryDialog(self, "Edit Entry", data=cur)
        if dlg.exec():
            vals = dlg.values()
            if not vals: return
            # only send changed fields (basic approach: send all non-empty; passwords can be empty to keep old)
            updates = {k: v for k, v in vals.items() if v != ""}  # don't clear if left blank
            update_entry(self.vault, eid, **updates)
            self.model.refresh()
            self.statusBar().showMessage("Entry updated.", 3000)

    def on_delete(self):
        eid = self._selected_entry_id()
        if eid is None:
            QtWidgets.QMessageBox.information(self, "Select", "Select a row to delete.")
            return
        if self._confirm("Delete", "Delete the selected entry? This cannot be undone."):
            delete_entry(self.vault, eid)
            self.model.refresh()
            self.statusBar().showMessage("Entry deleted.", 3000)

    def on_copy_password(self):
        eid = self._selected_entry_id()
        if eid is None:
            QtWidgets.QMessageBox.information(self, "Select", "Select a row to copy its password.")
            return
        try:
            e = get_entry(self.vault, eid, reveal_password=True)
            pw = e.get("password") or ""
            if not pw:
                QtWidgets.QMessageBox.information(self, "Empty", "This entry has no password.")
                return
            cb = QtWidgets.QApplication.clipboard()
            cb.setText(pw)
            self.statusBar().showMessage(f"Password copied. Auto-clearing in {self.autoclipper_seconds}s…")

            QtCore.QTimer.singleShot(self.autoclipper_seconds * 1000, lambda: self._clear_clipboard_if_match(pw))
        except Exception as ex:
            QtWidgets.QMessageBox.critical(self, "Error", str(ex))

    def _clear_clipboard_if_match(self, pw: str):
        cb = QtWidgets.QApplication.clipboard()
        if cb.text() == pw:
            cb.clear()
            self.statusBar().showMessage("Clipboard cleared.", 3000)

    def on_refresh(self):
        self.model.refresh()
        self.statusBar().showMessage("Refreshed.", 2000)

    def on_lock(self):
        # Simple lock: close this window; your login window should still be open or re-create it.
        self.close()


# --------------- Standalone run (optional) ---------------
def _demo_run_without_login():
    # This optional runner expects you to wire in Vault yourself.
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.information(None, "Info", "Open via login.py in normal use.")
    sys.exit(0)

if __name__ == "__main__":
    _demo_run_without_login()
