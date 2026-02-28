#!/usr/bin/env python3
"""🔥 Roast Master AI — Backend with Voice Support"""

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import json, urllib.request, urllib.error, random
from config import *

app = Flask(__name__)
conversations = {}

ROAST_INDICATORS = [
    "tu ", "tere ", "tera ", "teri ", "tujh", "tumh",
    "you ", "your ", "you're", "youre",
    "stupid", "dumb", "idiot", "ugly", "boring", "lame",
    "useless", "trash", "worst", "terrible", "pathetic",
    "pagal", "bewakoof", "gadha", "ullu", "bakwas",
    "mendhak","salla", "shut up", "chup", "nikal", "bhag", "loser", "noob",
]

FALLBACK_ROASTS = [
    "Bhai tu itna boring hai, tera alarm clock bhi snooze maar ke so jaata hai! 😴🔥",
    "Teri personality itni dry hai ki Sahara desert bhi tujhse tips maangta hai! 🏜️😂",
    "Tera brain Google pe search karo toh 404 Not Found aata hai! 🧠❌🔥",
    "Tu selfie leta hai toh camera bhi cry karta hai! 📸😭🔥",
    "Teri IQ aur room temperature mein race hai room temperature jeet raha hai! 🌡️💀",
    "Tujhe dekhke lagta hai evolution ne reverse gear laga diya! 🐒🔙💀",
    "Tera future itna dark hai ki flashlight bhi kaam nahi karti! 🔦💀",
    "Tu itna fake hai ki China bhi tujhe reject kar de! 🏷️🔥",
    "Tera love life aur Bermuda Triangle same hai dono mein sab kho jaata hai! 💔😂",
    "Tu itna slow hai Internet Explorer bhi tujhe bhai jaldi kar bolta hai! 🐌💀",
    "Bhai tere jokes sunke comedy ka funeral hota hai! ⚰️😂",
    "Tu itna irrelevant hai tera phone bhi tujhe notifications nahi deta! 📱💀",
]

FALLBACK_COUNTERS = [
    "Tu MUJHE roast karega? 😂 Pehle mirror dekh permanent roast! 🪞🔥💀 FATALITY!",
    "HAHAHA! Tera roast itna weak hai jitna tera WiFi basement mein! 📶💀 MIC DROP!",
    "AWWW! Baby ne roast try kiya! 🍼😂 Cute aur USELESS! 🔥 FATALITY!",
    "Tu mujhse panga? Main roasting ka Thanos hoon tu toh extra bhi nahi! 💀🔥 WASTED!",
    "Sher aaya roast karne! Par tu sher nahi tu Sheru hai friendly wala! 🐕🔥",
    "Tera roast sunke AC bhi band kar doon toh garmi nahi lagegi! ❄️💀 FATALITY!",
]

MOOD_PROMPTS = {
    "savage": "\nMOOD: MAXIMUM SAVAGE! Most BRUTAL! Add FATALITY!",
    "funny": "\nMOOD: COMEDIAN! Bollywood references! Kapil Sharma style! Hilarious!",
    "desi_parent": "\nMOOD: DISAPPOINTED INDIAN PARENT! 'Sharma ji ka beta...', 'Padhai kar', guilt trips!",
    "rapper": "\nMOOD: DESI RAPPER! Rhymes, bars, diss track style! Drop bars!",
    "intellectual": "\nMOOD: INTELLECTUAL ROAST! Big words, scientific burns, philosophical!",
    "street": "\nMOOD: MUMBAI TAPORI! Street slang, auto-rickshaw vibes, desi street energy!",
}


def check_ollama():
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            models = [m['name'] for m in data.get('models', [])]
            return any(OLLAMA_MODEL in m for m in models)
    except:
        return False


def is_user_roasting(msg):
    msg = msg.lower()
    return sum(1 for i in ROAST_INDICATORS if i in msg) >= 2


def call_ollama_stream(messages):
    payload = {
        "model": OLLAMA_MODEL, "messages": messages, "stream": True,
        "options": {"temperature": TEMPERATURE, "num_predict": MAX_TOKENS, "repeat_penalty": REPEAT_PENALTY}
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/chat", data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        for line in resp:
            if line:
                chunk = json.loads(line.decode('utf-8'))
                token = chunk.get("message", {}).get("content", "")
                if token: yield token
                if chunk.get("done", False): break


def call_ollama(messages):
    payload = {
        "model": OLLAMA_MODEL, "messages": messages, "stream": False,
        "options": {"temperature": TEMPERATURE, "num_predict": MAX_TOKENS, "repeat_penalty": REPEAT_PENALTY}
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/chat", data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode())
        return result.get("message", {}).get("content", "")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/check')
def api_check():
    return jsonify({"ollama_available": check_ollama(), "model": OLLAMA_MODEL})


@app.route('/api/welcome', methods=['POST'])
def api_welcome():
    data = request.json
    user_name = data.get('user_name', 'Bhai')
    session_id = data.get('session_id', 'default')

    if check_ollama():
        try:
            conversations[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
            msgs = conversations[session_id]
            msgs.append({"role": "user", "content":
                f"[User arrived! Name: '{user_name}'. Give SAVAGE welcome! Roast their NAME! 2-3 brutal lines!]\nUser: Hi mera naam {user_name} hai"
            })
            response = call_ollama(msgs)
            msgs.append({"role": "assistant", "content": response})
            return jsonify({"response": response, "source": "ollama"})
        except:
            pass

    fallbacks = [
        f"'{user_name}'? 😂 Yeh naam hai ya punishment? Parents ne bhi roast kar diya! 🔥💀",
        f"{user_name}! 😂 Google pe search kiya toh aaya Did you mean Nobody? 💀🔥",
        f"Oh {user_name}! Naam sunke laga special hoga par tu toh GENERIC nikla! 🔥💀",
    ]
    return jsonify({"response": random.choice(fallbacks), "source": "fallback"})


@app.route('/api/stream', methods=['POST'])
def api_stream():
    data = request.json
    msg = data.get('message', '').strip()
    user_name = data.get('user_name', 'Bhai')
    session_id = data.get('session_id', 'default')
    roast_count = data.get('roast_count', 0)
    counters = data.get('counter_attempts', 0)
    savage = data.get('savage_mode', False)
    mood = data.get('mood', 'savage')

    is_counter = is_user_roasting(msg)

    def generate():
        if check_ollama():
            try:
                if session_id not in conversations:
                    conversations[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
                msgs = conversations[session_id]

                extra = ""
                if is_counter:
                    extra = f"\n⚠️ USER TRYING TO ROAST YOU! Failed {counters+1} times! DESTROY 10x HARDER! Add FATALITY💀!"
                if savage:
                    extra += "\n🔥SAVAGE MODE! MAXIMUM BRUTALITY!"

                mood_extra = MOOD_PROMPTS.get(mood, "")
                context = f"[User:{user_name}|Roasts:{roast_count}|Fails:{counters}|Savage:{'YES' if savage else 'No'}{extra}{mood_extra}]\nUser: {msg}"
                msgs.append({"role": "user", "content": context})

                full = ""
                for token in call_ollama_stream(msgs):
                    full += token
                    yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"

                msgs.append({"role": "assistant", "content": full})
                if len(msgs) > 24:
                    conversations[session_id] = [msgs[0]] + msgs[-20:]

                yield f"data: {json.dumps({'token': '', 'done': True, 'is_counter': is_counter})}\n\n"
                return
            except:
                pass

        response = random.choice(FALLBACK_COUNTERS if is_counter else FALLBACK_ROASTS)
        yield f"data: {json.dumps({'token': response, 'done': True, 'is_counter': is_counter})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/reset', methods=['POST'])
def api_reset():
    sid = request.json.get('session_id', 'default')
    conversations.pop(sid, None)
    return jsonify({"status": "reset"})


if __name__ == '__main__':
    print("\n🔥🔥🔥 ROAST MASTER AI — Voice Edition 🔥🔥🔥")
    print(f"🌐 http://localhost:{FLASK_PORT}")
    print(f"🤖 Model: {OLLAMA_MODEL}\n")
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT, host='0.0.0.0')