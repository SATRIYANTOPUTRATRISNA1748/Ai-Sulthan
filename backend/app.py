import os
import json
import requests
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)


#  API Keys

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip() or "API AI"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip() or "APi Ai"


client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)


#  File JSON Path

BASE_DIR = os.path.dirname(__file__)
QNA_FILE = os.path.abspath(os.path.join(BASE_DIR, "DATABASE QNA"))
YOU_JSON = os.path.abspath(os.path.join(BASE_DIR, ""))  # perbaikan: sebelumnya kosong!
EMBED_FILE = os.path.abspath(os.path.join(BASE_DIR, "DATABASE FOR SWITCH YOUR MACHINE LEARNING"))
MODEL = SentenceTransformer('all-MiniLM-L6-v2')

chat_history = []

# JSON Loader/Saver

def load_json(path):
    if not os.path.exists(path):
        save_json(path, [])
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"⚠️ Error process {os.path.basename(path)}: {e}")
        return []

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Fail FIle {os.path.basename(path)}: {e}")


# Database QNA

data = load_json(QNA_FILE)
forum_data = load_json(YOU_JSON)
embeddings_data = load_json(EMBED_FILE) if os.path.exists(EMBED_FILE) else []
if not os.path.exists(EMBED_FILE):
    save_json(EMBED_FILE, embeddings_data)

forum_embeddings = np.array(MODEL.encode(forum_data)) if forum_data else np.array([])

# Simple Marchine Learning(You Can Delete The Code If You Have Marchine Learning)

def add_to_log(user_msg, ai_reply):
    embeddings_data.append({"user": user_msg, "ai": ai_reply})
    save_json(EMBED_FILE, embeddings_data)

def get_best_answer(user_input):
    if not forum_data:
        return None, None
    query_vec = MODEL.encode([user_input])
    sims = cosine_similarity(query_vec, forum_embeddings)[0]
    best_idx = np.argmax(sims)
    if sims[best_idx] > 0.5:
        return forum_data[best_idx], best_idx
    return None, None

def update_embeddings():
    global forum_embeddings
    forum_embeddings = np.array(MODEL.encode(forum_data))
    save_json(YOU_JSON, forum_data)


# Ai Example For Mix Your AI and Ai Smart and Famous

def call_openai(messages):
    if not client:
        print("⚠️ OpenAI API key Not Found.")
        return None
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print("⚠️ OpenAI Error:", e)
        return None

def call_groq(messages):
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload_groq = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": m["role"], "content": str(m["content"])} for m in messages]
        }

        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload_groq,
            timeout=20
        )
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("⚠️ Groq AI Error:", e)
        return None

# Routes

FRONTEND = os.path.abspath("../frontend")
BACKEND = os.path.abspath("../backend")

@app.after_request
def add_headers(response):
    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Server"] = "Flask"
    return response

@app.route("/")
def index():
    return send_from_directory(FRONTEND, "data.html")

@app.route("/<path:filename>")
def serve_static(filename):
  
    for folder in [FRONTEND, BACKEND]:
        file_path = os.path.join(folder, filename)
        if os.path.exists(file_path):
            return send_from_directory(folder, filename)
    return jsonify({"error": "File tidak ditemukan"}), 404


# Chat Endpoint

@app.route("/chat", methods=["POST"])
def chat():
    global chat_history

    payload = request.get_json(silent=True) or {}
    user_msg = (payload.get("message") or "").strip().lower()
    if not user_msg:
        return jsonify({"reply": "Pesan kosong."})

    chat_history.append({"role": "user", "content": user_msg})

    # 1️ Check Database QNA
    for item in data:
        if user_msg == item.get("tanya", "").strip().lower():
            answer = item.get("jawab", "")
            chat_history.append({"role": "assistant", "content": answer})
            add_to_log(user_msg, answer)
            return jsonify({"reply": answer})

    # 2️ Check Your Machine Learning
    answer, best_idx = get_best_answer(user_msg)
    if answer:
        chat_history.append({"role": "assistant", "content": answer})
        add_to_log(user_msg, answer)
        return jsonify({"reply": answer, "index": int(best_idx)})

    # 3️ Fallback Ai Smart{You can change no should open ai or grock}
    system_prompt = {"role": "system", "content": "Jawab hanya berdasarkan konteks database."}
    messages = [system_prompt, *chat_history]

    reply = call_openai(messages) or call_groq(messages)

    if reply:
        chat_history.append({"role": "assistant", "content": reply})
        add_to_log(user_msg, reply)
        return jsonify({"reply": reply})

    # 4️⃣ Fall All
    default_reply = "Your Massage"
    chat_history.append({"role": "assistant", "content": default_reply})
    add_to_log(user_msg, default_reply)
    return jsonify({"reply": default_reply})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


