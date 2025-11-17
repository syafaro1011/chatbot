from flask import Flask, request, jsonify, session, redirect, send_from_directory
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
WEB_DIR = BASE_DIR / "web"

app = Flask(__name__, static_folder=str(WEB_DIR), template_folder=str(WEB_DIR))

app.secret_key = "admin123"      
ADMIN_PASSWORD = "12345"         

PRODUK_FILE = BASE_DIR / "produk.json"
FAQ_FILE = BASE_DIR / "faq.json"

# ------------------------- Helpers -------------------------
def load_json(path):
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def require_admin():
    return "admin" in session

def is_learning():
    return session.get("learning") == True

# ------------------------- LOGIN -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.json
        pw = data.get("password", "")

        if pw == ADMIN_PASSWORD:
            session["admin"] = True
            return jsonify({"status": "ok"})
        else:
            return jsonify({"status": "error", "message": "Password salah"}), 401

    return send_from_directory(str(WEB_DIR), "login.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")


# ------------------------- Produk API -------------------------
@app.route("/produk", methods=["GET"])
def list_produk():
    data = load_json(PRODUK_FILE)
    return jsonify(data.get("produk", []))


@app.route("/produk/<string:nama>", methods=["GET"])
def detail_produk(nama):
    data = load_json(PRODUK_FILE)
    nama_low = nama.lower()
    for p in data.get("produk", []):
        if p.get("nama", "").lower() == nama_low or p.get("id", "").lower() == nama_low:
            return jsonify(p)
    return jsonify({"error": "Produk tidak ditemukan"}), 404


@app.route("/harga/<string:nama>", methods=["GET"])
def harga_produk(nama):
    data = load_json(PRODUK_FILE)
    nama_low = nama.lower()
    for p in data.get("produk", []):
        if p.get("nama", "").lower() == nama_low or p.get("id", "").lower() == nama_low:
            return jsonify({"nama": p["nama"], "harga": p["harga"]})
    return jsonify({"error": "Produk tidak ditemukan"}), 404


@app.route("/stok/<string:nama>", methods=["GET"])
def stok_produk(nama):
    data = load_json(PRODUK_FILE)
    nama_low = nama.lower()
    for p in data.get("produk", []):
        if p.get("nama", "").lower() == nama_low or p.get("id", "").lower() == nama_low:
            return jsonify({"nama": p["nama"], "stok": p["stok"]})
    return jsonify({"error": "Produk tidak ditemukan"}), 404


@app.route("/add_product", methods=["POST"])
def add_product():
    if not require_admin():
        return jsonify({"error": "Unauthorized"}), 403

    body = request.get_json()
    if not body:
        return jsonify({"error": "Body JSON kosong"}), 400

    data = load_json(PRODUK_FILE)
    arr = data.get("produk", [])

    required = ["id", "nama", "kategori", "harga", "stok", "deskripsi"]
    for r in required:
        if r not in body:
            return jsonify({"error": f"Field {r} dibutuhkan"}), 400

    arr.append(body)
    data["produk"] = arr
    save_json(PRODUK_FILE, data)
    return jsonify({"status": "success", "message": "Produk berhasil ditambahkan"})


@app.route("/edit_product", methods=["POST"])
def edit_product():
    if not require_admin():
        return jsonify({"error": "Unauthorized"}), 403

    body = request.get_json()
    if not body or "id" not in body:
        return jsonify({"error": "Field id dibutuhkan"}), 400

    data = load_json(PRODUK_FILE)
    for p in data.get("produk", []):
        if p.get("id") == body["id"]:
            for k, v in body.items():
                if k != "id":
                    p[k] = v
            save_json(PRODUK_FILE, data)
            return jsonify({"status": "success", "message": "Produk berhasil diupdate"})

    return jsonify({"error": "Produk tidak ditemukan"}), 404


@app.route("/delete_product", methods=["POST"])
def delete_product():
    if not require_admin():
        return jsonify({"error": "Unauthorized"}), 403

    body = request.get_json()
    if not body or "id" not in body:
        return jsonify({"error": "Field id dibutuhkan"}), 400

    data = load_json(PRODUK_FILE)
    new_list = [p for p in data.get("produk", []) if p.get("id") != body["id"]]
    data["produk"] = new_list
    save_json(PRODUK_FILE, data)
    return jsonify({"status": "success", "message": "Produk berhasil dihapus"})


# ------------------------- FAQ API -------------------------
@app.route("/faq", methods=["GET"])
def list_faq():
    data = load_json(FAQ_FILE)
    return jsonify(data.get("faq", []))


@app.route("/add_faq", methods=["POST"])
def add_faq():
    if not require_admin():
        return jsonify({"error": "Unauthorized"}), 403

    body = request.get_json()
    if not body or "question" not in body or "answer" not in body:
        return jsonify({"error": "Field question & answer dibutuhkan"}), 400

    data = load_json(FAQ_FILE)
    arr = data.get("faq", [])
    arr.append({"question": body["question"].lower(), "answer": body["answer"]})
    data["faq"] = arr
    save_json(FAQ_FILE, data)
    return jsonify({"status": "success"})


# ------------------------- Chat endpoint (Decision Tree) -------------------------
@app.route("/chat", methods=["POST"])
def chat():
    body = request.get_json() or {}
    message = (body.get("message") or body.get("question") or "").strip()
    if not message:
        return jsonify({"reply": "Silakan kirim pesan"}), 400

    msg = message.lower()

    # ---------------------- MODE LEARNING ----------------------
    if session.get("learning") == True:
        answer = message.strip()
        question = session.get("last_question")

        if question:
            data = load_json(FAQ_FILE)
            arr = data.get("faq", [])

            arr.append({
                "question": question.lower(),
                "answer": answer
            })

            save_json(FAQ_FILE, {"faq": arr})

        # reset mode belajar
        session["learning"] = False
        session["last_question"] = None

        return jsonify({"reply": "Terima kasih! Saya sudah belajar 😊"})


    # ---------------------- INTENT DETECTION ----------------------
    if "harga" in msg:
        data = load_json(PRODUK_FILE)
        for p in data.get("produk", []):
            if p["nama"].lower() in msg or p.get("id", "").lower() in msg:
                return jsonify({"reply": f"Harga {p['nama']} adalah Rp {p['harga']}"})
        return jsonify({"reply": "Produk apa yang ingin Anda cek harganya?"})

    if "stok" in msg or "ready" in msg:
        data = load_json(PRODUK_FILE)
        for p in data.get("produk", []):
            if p["nama"].lower() in msg or p.get("id", "").lower() in msg:
                return jsonify({"reply": f"Stok {p['nama']} tersedia {p['stok']} pcs."})
        return jsonify({"reply": "Produk apa yang ingin Anda cek stoknya?"})

    if "produk" in msg or "daftar" in msg or "list" in msg or "tersedia" in msg:
        data = load_json(PRODUK_FILE)
        daftar = "\n".join([
            f"- {p['nama']} Rp {p['harga']} (stok: {p['stok']})"
            for p in data.get("produk", [])
        ])
        return jsonify({"reply": f"Daftar produk kami:\n{daftar}"})

    if "deskripsi" in msg or "jelaskan" in msg:
        data = load_json(PRODUK_FILE)
        for p in data.get("produk", []):
            if p["nama"].lower() in msg or p.get("id", "").lower() in msg:
                return jsonify({"reply": p.get("deskripsi", "Tidak ada deskripsi")})
        return jsonify({"reply": "Deskripsi produk apa yang ingin Anda tahu?"})


    # ---------------------- FAQ MATCH ----------------------
    faq = load_json(FAQ_FILE)
    for f in faq.get("faq", []):
        if f.get("question", "").lower() in msg:
            return jsonify({"reply": f.get("answer")})


    # ---------------------- FALLBACK (LEARNING MODE) ----------------------
    session["learning"] = True
    session["last_question"] = msg
    return jsonify({"reply": "Maaf, saya belum tahu jawabannya, jadi jawabannya apa?"})




# ------------------------- Web Routes -------------------------
@app.route('/')
def home():
    return send_from_directory(str(WEB_DIR), "index.html")

@app.route('/admin')
def admin():
    if not require_admin():
        return redirect("/login")
    return send_from_directory(str(WEB_DIR), "dashboard.html")

@app.route('/web/<path:path>')
def send_web(path):
    return send_from_directory(str(WEB_DIR), path)



# ------------------------- Run -------------------------
if __name__ == '__main__':
    if not PRODUK_FILE.exists():
        save_json(PRODUK_FILE, {"produk": []})
    if not FAQ_FILE.exists():
        save_json(FAQ_FILE, {"faq": []})

    app.run(host='0.0.0.0', port=5000, debug=True)

