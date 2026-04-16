from datetime import datetime
import random
import time

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# =========================
# DEFAULT STATS
# =========================
def default_stats():
    return {
        "total_transactions": 0,
        "success": 0,
        "failed": 0,
        "request_count": 0,
        "publish_count": 0,
        "rpc_count": 0,
        "last_latency_ms": 0,
        "avg_latency_ms": 0,
        "throughput_per_minute": 0,
    }

pubsub_messages = []
communication_logs = []
stats = default_stats()
latency_samples = []

# =========================
# UTIL
# =========================
def now_text():
    return datetime.now().strftime("%H:%M:%S")

def push_log(model, event, detail, status="ok"):
    communication_logs.append({
        "time": now_text(),
        "model": model,
        "event": event,
        "detail": detail,
        "status": status,
    })

    if len(communication_logs) > 120:
        del communication_logs[0]

def update_latency(latency_ms):
    latency_samples.append(latency_ms)
    if len(latency_samples) > 80:
        del latency_samples[0]

    stats["last_latency_ms"] = latency_ms
    stats["avg_latency_ms"] = round(sum(latency_samples) / len(latency_samples))

def update_throughput():
    if not latency_samples:
        stats["throughput_per_minute"] = 0
        return

    avg_seconds = max((sum(latency_samples) / len(latency_samples)) / 1000, 0.001)
    stats["throughput_per_minute"] = round(60 / avg_seconds)

# =========================
# ROUTES
# =========================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send", methods=["POST"])
def send():
    payload = request.get_json(silent=True) or {}

    drink = payload.get("drink", "Americano")
    customer = payload.get("customer", "Guest")
    mode = str(payload.get("mode", "request")).lower()
    note = payload.get("note", "")

    method = str(payload.get("method", "pickup")).lower()  # pickup, dinein, delivery
    address = payload.get("address", "")

    try:
        quantity = int(payload.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 0

    started = time.perf_counter()

    # =========================
    # VALIDASI
    # =========================
    if mode not in {"request", "publish", "rpc"}:
        stats["failed"] += 1
        push_log("SYSTEM", "VALIDATION", "Mode tidak dikenal.", status="error")
        return jsonify({"ok": False, "error": "Mode komunikasi tidak valid."}), 400

    if quantity < 1:
        stats["failed"] += 1
        push_log("SYSTEM", "VALIDATION", "Quantity harus minimal 1.", status="error")
        return jsonify({"ok": False, "error": "Quantity minimal 1."}), 400

    if method not in {"pickup", "dinein", "delivery"}:
        stats["failed"] += 1
        push_log("SYSTEM", "VALIDATION", "Metode order tidak valid.", status="error")
        return jsonify({"ok": False, "error": "Metode order tidak valid."}), 400

    if method == "delivery" and not address:
        stats["failed"] += 1
        push_log("SYSTEM", "VALIDATION", "Alamat wajib untuk delivery.", status="error")
        return jsonify({"ok": False, "error": "Alamat wajib untuk delivery."}), 400

    # =========================
    # FORMAT ORDER
    # =========================
    order_text = f"{quantity}x {drink} oleh {customer} ({method})"

    if method == "delivery":
        order_text += f" ke {address}"

    if note:
        order_text += f" (catatan: {note})"

    stats["total_transactions"] += 1

    # =========================
    # REQUEST - RESPONSE
    # =========================
    if mode == "request":
        stats["request_count"] += 1

        push_log("REQ-RES", "REQUEST", f"Client kirim order: {order_text}")

        if method == "delivery":
            push_log("REQ-RES", "PROCESS", "Order Service memanggil Delivery Service")
        elif method == "pickup":
            push_log("REQ-RES", "PROCESS", "Order langsung ke Barista")
        elif method == "dinein":
            push_log("REQ-RES", "PROCESS", "Order diproses untuk dine-in")

        time.sleep(random.uniform(0.18, 0.45))

        push_log("REQ-RES", "RESPONSE", "Order berhasil diproses secara sinkron")

        result = {
            "ok": True,
            "model": "request",
            "response": f"✅ Order diproses (Request-Response)",
        }

    # =========================
    # PUBLISH - SUBSCRIBE
    # =========================
    elif mode == "publish":
        stats["publish_count"] += 1

        push_log("PUB-SUB", "PUBLISH", f"Client publish event: {order_text}")
        time.sleep(random.uniform(0.1, 0.25))

        pubsub_messages.append(f"🔔 Topic coffee.order: {order_text}")

        push_log("PUB-SUB", "SUBSCRIBE", "Kitchen Service menerima event")

        if method == "delivery":
            push_log("PUB-SUB", "SUBSCRIBE", "Delivery Service menerima event")

        push_log("PUB-SUB", "SUBSCRIBE", "Notification Service mengirim notifikasi")

        result = {
            "ok": True,
            "model": "publish",
            "response": "📡 Event berhasil dipublish ke subscriber",
        }

    # =========================
    # RPC
    # =========================
    elif mode == "rpc":
        stats["rpc_count"] += 1

        push_log("RPC", "CALL", f"OrderService -> PaymentService ({order_text})")
        time.sleep(random.uniform(0.22, 0.5))

        push_log("RPC", "RESULT", "Payment SUCCESS")

        push_log("RPC", "CALL", "OrderService -> KitchenService")
        time.sleep(random.uniform(0.1, 0.3))

        if method == "delivery":
            push_log("RPC", "CALL", "OrderService -> DeliveryService")
            push_log("RPC", "RESULT", "Delivery siap mengantar")

        push_log("RPC", "RESULT", "Order selesai diproses")

        result = {
            "ok": True,
            "model": "rpc",
            "response": "🔁 RPC chain berhasil dijalankan",
        }

    # =========================
    # FINAL
    # =========================
    stats["success"] += 1

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    update_latency(elapsed_ms)
    update_throughput()

    result["latency_ms"] = elapsed_ms
    return jsonify(result)

# =========================
# API DATA
# =========================
@app.route("/messages", methods=["GET"])
def get_messages():
    return jsonify(pubsub_messages[-40:])

@app.route("/log", methods=["GET"])
def get_log():
    return jsonify(communication_logs[-80:])

@app.route("/stats", methods=["GET"])
def get_stats():
    return jsonify(stats)

@app.route("/reset", methods=["POST"])
def reset():
    global stats
    pubsub_messages.clear()
    communication_logs.clear()
    latency_samples.clear()
    stats = default_stats()
    push_log("SYSTEM", "RESET", "Simulasi dibersihkan.")
    return jsonify({"ok": True})

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)