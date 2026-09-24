from flask import Flask, render_template_string, jsonify, request
import main
import json

app = Flask(__name__)

# HTML Template with Kick/Mute UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Fb Group Control Panel</title>
    <style>
        body { font-family: sans-serif; padding: 20px; background-color: #f4f4f9; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        .input-group { margin-bottom: 15px; }
        input { padding: 8px; width: 70%; }
        button { padding: 8px 15px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 4px; }
        button:hover { background: #0056b3; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; border-bottom: 1px solid #ddd; text-align: left; }
        .btn-kick { background: #dc3545; }
        .btn-mute { background: #ffc107; color: black; }
        #status { margin-top: 10px; font-weight: bold; color: green; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Facebook Group Admin Panel</h1>
        
        <div class="input-group">
            <label>Enter Group ID:</label>
            <input type="text" id="groupIdInput" placeholder="e.g., 123456789">
            <button onclick="fetchMembers()">Fetch Members</button>
        </div>

        <div id="status"></div>

        <table id="membersTable">
            <thead>
                <tr>
                    <th>User ID</th>
                    <th>Name (Optional)</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody id="membersBody">
                <!-- Members will be loaded here -->
            </tbody>
        </table>
    </div>

    <script>
        async function fetchMembers() {
            const groupId = document.getElementById('groupIdInput').value;
            if(!groupId) return alert("Please enter Group ID");

            document.getElementById('status').innerText = "Fetching members...";
            
            try {
                // Note: In a real scenario, you might need to ensure bot is logged in first.
                // For simplicity, we call the endpoint which triggers main.get_members_for_admin
                const response = await fetch(`/get_members/${groupId}`);
                const data = await response.json();

                const tbody = document.getElementById('membersBody');
                tbody.innerHTML = "";

                if(data.members) {
                    data.members.forEach(uid => {
                        const row = `
                            <tr>
                                <td>${uid}</td>
                                <td><span id="name-${uid}">Loading...</span></td>
                                <td>
                                    <button class="btn-mute" onclick="muteUser('${groupId}', '${uid}')">Mute</button>
                                    <button class="btn-kick" onclick="kickUser('${groupId}', '${uid}')">Kick</button>
                                </td>
                            </tr>
                        `;
                        tbody.innerHTML += row;
                    });
                    document.getElementById('status').innerText = `Loaded ${data.members.length} members.`;
                } else {
                    document.getElementById('status').innerText = "No members found or error.";
                }
            } catch (error) {
                console.error(error);
                document.getElementById('status').innerText = "Error fetching data.";
            }
        }

        async function kickUser(groupId, uid) {
            const response = await fetch(`/kick/${groupId}/${uid}`);
            const result = await response.json();
            alert(result.message);
        }

        async function muteUser(groupId, uid) {
            const response = await fetch(`/mute/${groupId}/${uid}`);
            const result = await response.json();
            alert(result.message);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_members/<string:group_id>')
def get_members(group_id):
    try:
        members = main.get_members_for_admin(group_id)
        return jsonify({"members": members})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/kick/<string:group_id>/<string:uid>')
def kick_member(group_id, uid):
    try:
        # Ensure bot is initialized
        if not main.bot_instance:
            main.start_bot()
        
        success = main.bot_instance.kick_member(group_id, uid)
        msg = "Kicked successfully" if success else "Failed to kick"
        return jsonify({"message": msg})
    except Exception as e:
        return jsonify({"message": str(e)})

@app.route('/mute/<string:group_id>/<string:uid>')
def mute_member(group_id, uid):
    try:
        if not main.bot_instance:
            main.start_bot()
            
        success = main.bot_instance.mute_member(group_id, uid)
        msg = "Muted successfully" if success else "Failed to mute"
        return jsonify({"message": msg})
    except Exception as e:
        return jsonify({"message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
