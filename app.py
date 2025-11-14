from flask import Flask, request, jsonify, render_template
import json

app = Flask(__name__)

# Load data dari file
def load_data():
    with open("knowledge.json", "r", encoding="utf-8") as f:
        return json.load(f)

data = load_data()

# State per user berdasarkan IP
session_state = {}

# Fungsi mencari jawaban
def cari_jawaban(pertanyaan):
    pertanyaan = pertanyaan.lower()
    for item in data["pertanyaan"]:
        if item["tanya"].lower() in pertanyaan:
            return item["jawab"]
    return None  # tidak ditemukan

# -------------------------------
#  ENDPOINT CHAT
# -------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    user_data = request.get_json()
    pesan = user_data.get("message", "").strip()
    user_ip = request.remote_addr

    # Jika user sedang memberi jawaban untuk pertanyaan baru
    if user_ip in session_state:
        original_question = session_state[user_ip]["pertanyaan"]

        # Simpan jawaban ke file
        data["pertanyaan"].append({
            "tanya": original_question,
            "jawab": pesan
        })

        with open("knowledge.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        del session_state[user_ip]

        return jsonify({"reply": "Terima kasih! Saya sudah belajar jawaban baru."})

    # Proses normal chat
    jawaban = cari_jawaban(pesan)
    if jawaban:
        return jsonify({"reply": jawaban})

    # Tidak ditemukan → langsung masuk mode belajar
    session_state[user_ip] = {
        "pertanyaan": pesan
    }

    return jsonify({
        "reply": "Maaf, saya belum tahu jawabannya, jadi jawabannya apa?"
    })

# -------------------------------
#  ENDPOINT TRAIN
# -------------------------------
@app.route("/train", methods=["GET"])
def train():
    global data
    data = load_data()
    return jsonify({"status": "Data berhasil dimuat ulang", "count": len(data["pertanyaan"])})

# -------------------------------
#  ENDPOINT ADD MANUAL
# -------------------------------
@app.route("/add", methods=["POST"])
def add_data():
    user_data = request.get_json()
    tanya = user_data.get("tanya")
    jawab = user_data.get("jawab")

    if not tanya or not jawab:
        return jsonify({"error": "Harus ada 'tanya' dan 'jawab'"}), 400

    data["pertanyaan"].append({"tanya": tanya, "jawab": jawab})
    with open("knowledge.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return jsonify({"status": "Berhasil ditambahkan"})

# -------------------------------
#  FRONTEND
# -------------------------------
@app.route("/web")
def web():
    return render_template("index.html")

@app.route("/")
def index():
    return jsonify({"info": "Chatbot JSON API aktif."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
