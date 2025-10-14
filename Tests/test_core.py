
import os, tempfile
from cloud_vault.db import init_vault, open_vault, add_entry, list_entries, get_entry, update_entry, delete_entry

def test_init_open_add_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "vault.db")
        v = init_vault(db, "master123")
        eid = add_entry(v, "Github", "https://github.com", "reedy", "s3cr3t", "2FA enabled")
        rows = list_entries(v)
        assert len(rows) == 1 and rows[0]["title"] == "Github"
        v2 = open_vault(db, "master123")
        e = get_entry(v2, eid, reveal_password=True)
        assert e["username"] == "reedy" and e["password"] == "s3cr3t"
        update_entry(v2, eid, password="newpw")
        e2 = get_entry(v2, eid, reveal_password=True)
        assert e2["password"] == "newpw"
        delete_entry(v2, eid)
        assert list_entries(v2) == []
