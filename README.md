# Capstone-The-Lock-Box

# Cloud Vault Core (Weeks 3–4)

Backend scaffold for your Windows desktop password vault (no UI yet).
Includes:
- **Argon2id** KDF (argon2-cffi) to derive a master key from password
- **AES-GCM** for authenticated encryption (cryptography)
- **SQLite** schema + safe PRAGMAs
- CRUD for entries (title/url/username/password/notes)
- Simple CLI demo to init/open vault and add/list entries
- Unit tests (pytest)

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate  # on Windows
pip install -r requirements.txt
```

## CLI usage (For testing without UI)
```bash
# Initialize a new vault
python -m cloud_vault.cli init --db vault.db --user "Reed" --pw "MASTER_PASSWORD"

# Add an entry
python -m cloud_vault.cli add --db vault.db --pw "MASTER_PASSWORD"     --title "Github" --url "https://github.com" --username "reedy" --password "s3cr3t" --notes "2FA enabled"

# List entries (titles + usernames; passwords decrypted only if --reveal)
python -m cloud_vault.cli list --db vault.db --pw "MASTER_PASSWORD"
python -m cloud_vault.cli show --db vault.db --pw "MASTER_PASSWORD" --id 1 --reveal
```

## Notes
- The vault stores a random **vault_key** encrypted ("wrapped") by a master key derived with Argon2id.
- Each sensitive field is encrypted with **fresh nonces** using AES-GCM.
- **No plaintext** is written to disk by this code beyond what you pass on the command line (avoid using `--pw` in real use; supply via prompt).
- Add the Qt UI in Week 5–6 and call these functions from your slots.
- REMINDER login.py and main_window.py are 1 level up in the file tree from the other files, those 2 files sit in the CAPTONE folder and not the cloud_vault
