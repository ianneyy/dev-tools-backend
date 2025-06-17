from flask import Flask, jsonify, request
import mysql.connector
import google.generativeai as genai
import os


gemini_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_key)



app = Flask(__name__)

# Connect to Aiven MySQL with SSL

def generate_description(name):

    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
    Generate a one-sentence description of the following development tool.
    The description should be concise, informative, and non-promotional.

    Tool: {name}


    """
    response = model.generate_content(prompt)
    return response.text.strip()

def extract_name_from_link(link):


    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
Given this URL: "{link}", return only the name of the development tool or product it leads to.
Avoid including extra text or explanation. Just return the name in title case if possible.
If the name is unclear, make your best guess based on the domain.

Example:
- Input: "https://ui.shadcn.com"
  Output: Shadcn
- Input: "https://vitejs.dev"
  Output: Vite
- Input: "https://tailwindcss.com"
  Output: Tailwind CSS

Now do the same for this:
{link}
"""

    response = model.generate_content(prompt)
    return response.text.strip()

def categorize_tool(name_or_link):


    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
Given the following tool name or URL:

"{name_or_link}"

Choose the most appropriate category from this fixed list:
- components
- api
- color
- developer
- illustration
- animation

Return only one word — the category that best matches the tool.

Examples:
- Input: "https://ui.shadcn.com" → Output: components
- Input: "Postman" → Output: api
- Input: "coolors.co" → Output: color
- Input: "https://readme.com" → Output: developer
- Input: "undraw.co" → Output: illustration
- Input: "lottiefiles.com" → Output: animation

Now categorize:
{name_or_link}
"""

    response = model.generate_content(prompt)
    return response.text.strip().lower()



def get_db_connection():
    return mysql.connector.connect(
        host = os.getenv("DB_HOST"),
        port = int(os.getenv("DB_PORT", 3306)),
        user = os.getenv("DB_USERNAME"),
        password = os.getenv("DB_PASSWORD"),
        database = os.getenv("DB_NAME"),
       
        ssl_disabled=False  # required for Aiven!
    )


@app.route('/tools')
def get_tools():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tools")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

@app.route('/create', methods=['POST'])
def insert_tools():
    data = request.get_json()
    url = data.get('url')

    name = extract_name_from_link(url)
    description = generate_description(name)
    category = categorize_tool(url)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tools (name, description, link, category) VALUES (%s, %s, %s, %s)",
        (name, description, url, category)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Tool inserted successfully"}), 201

if __name__ == '__main__':
    app.run(debug=True)
