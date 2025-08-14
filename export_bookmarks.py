import json
import sqlite3
import base64
import shutil
from pathlib import Path

# === PERCORSI ===
BOOKMARKS_SOURCE = Path(r"C:\Users\Utente\AppData\Local\Chromium\User Data\Default\Bookmarks")
FAVICONS_DB = Path(r"C:\Users\Utente\AppData\Local\Chromium\User Data\Default\Favicons")

OUTPUT_FOLDER = Path(__file__).parent / "toSync"
OUTPUT_FILE = "bookmarks_data.js"


# === LETTURA BOOKMARKS ===
try:
    with open(BOOKMARKS_SOURCE, "r", encoding="utf-8") as f:
        bookmarks_data = json.load(f)
except FileNotFoundError:
    print(f"❌ Errore: file non trovato: {BOOKMARKS_SOURCE}")
    exit(1)
except json.JSONDecodeError as e:
    print(f"❌ Errore nel parsing del JSON: {e}")
    exit(1)


# === LETTURA FAVICONS DAL DB ===
favicon_map = {}
if FAVICONS_DB.exists():
    try:

        temp_db = Path(__file__).parent / "Favicons_copy"
        shutil.copy2(FAVICONS_DB, temp_db)
        conn = sqlite3.connect(temp_db)

        cursor = conn.cursor()
        cursor.execute("""
            SELECT page_url, favicon_bitmaps.image_data
            FROM icon_mapping
            JOIN favicons ON icon_mapping.icon_id = favicons.id
            JOIN favicon_bitmaps ON favicons.id = favicon_bitmaps.icon_id
        """)
        for page_url, image_data in cursor.fetchall():
            if image_data:
                b64_icon = base64.b64encode(image_data).decode('utf-8')
                favicon_map[page_url] = f"data:image/png;base64,{b64_icon}"
        conn.close()
    except Exception as e:
        print(f"⚠️ Errore nella lettura del DB Favicons: {e}")
else:
    print(f"⚠️ Database Favicons non trovato: {FAVICONS_DB}")

# === FUNZIONE RICORSIVA PER AGGIUNGERE LE ICONE ===
def add_favicons(node):
    if isinstance(node, dict):
        if node.get("type") == "url":
            url = node.get("url")
            if url in favicon_map:
                node["favicon"] = favicon_map[url]
        for child in node.values():
            add_favicons(child)
    elif isinstance(node, list):
        for child in node:
            add_favicons(child)

add_favicons(bookmarks_data)

# === CREAZIONE DEL TESTO JS ===
js_content = "window.BOOKMARKS_JSON = "
js_content += json.dumps(bookmarks_data, ensure_ascii=False, indent=2)
js_content += ";\n"

# === SCRITTURA DEL FILE DI OUTPUT ===
OUTPUT_FOLDER.mkdir(exist_ok=True)
output_path = OUTPUT_FOLDER / OUTPUT_FILE

with open(output_path, "w", encoding="utf-8") as f:
    f.write(js_content)

print(f"✅ File JS generato in: {output_path}")
