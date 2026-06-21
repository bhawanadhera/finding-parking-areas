from flask import Flask, render_template, jsonify, request
import sqlite3
import math

app = Flask(__name__)

# ================= DB =================

def get_db():
    conn = sqlite3.connect("parking.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS parking_spots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        lat REAL,
        lng REAL,
        slots INTEGER,
        status TEXT
    )
    """)

    count = conn.execute("SELECT COUNT(*) FROM parking_spots").fetchone()[0]

    if count == 0:
        sample_data = [
            ("Dolmen Mall Parking", 24.8138, 67.0295, 45, "open"),
            ("Clifton Parking", 24.8150, 67.0308, 12, "limited"),
            ("Sea View Parking", 24.8200, 67.0280, 0, "full"),
            ("Boat Basin Parking", 24.8175, 67.0240, 30, "open"),
        ]

        conn.executemany("""
        INSERT INTO parking_spots (name, lat, lng, slots, status)
        VALUES (?, ?, ?, ?, ?)
        """, sample_data)

    conn.commit()
    conn.close()


# ================= DISTANCE =================

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return int(R * c)


# ================= ROUTES =================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/parking")
def get_parking():

    user_lat_str = request.args.get("lat")
    user_lng_str = request.args.get("lng")

    if not user_lat_str or not user_lng_str:
        return jsonify({"error": "Latitude and longitude are required."}), 400

    try:
        user_lat = float(user_lat_str)
        user_lng = float(user_lng_str)
    except ValueError:
        return jsonify({"error": "Latitude and longitude must be valid numbers."}), 400

    conn = get_db()
    rows = conn.execute("SELECT * FROM parking_spots").fetchall()
    conn.close()

    spots = []

    for row in rows:
        dist = haversine(user_lat, user_lng, row["lat"], row["lng"])

        spots.append({
            "id": row["id"],
            "name": row["name"],
            "lat": row["lat"],
            "lng": row["lng"],
            "slots": row["slots"],
            "status": row["status"],
            "distance": dist
        })

    spots.sort(key=lambda x: x["distance"])

    return jsonify({"spots": spots})


# ================= RUN =================

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="localhost")  # use localhost not 127.0.0.1