import os
import json
import base64
import sqlite3
from io import BytesIO
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
from PIL import Image

# =========================
# Equinox ChatBot
# =========================

# Initialization
load_dotenv(override=True)
DB = "workouts.db"

openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")

MODEL = "gpt-4.1-mini"
openai = OpenAI()

system_message = """
You are a helpful assistant for the Equinox Gym app.

You can help users with:
- workouts by body part
- class schedules by day, time, or class type
- weekly Equinox events
- guest pass lookup
- guest pass purchases

Use tools whenever the user is asking for specific stored information.
Keep answers clear, direct, and helpful.
"""

print(system_message)

# =========================
# Database setup
# =========================

with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS workouts")
    cursor.execute("DROP TABLE IF EXISTS classes")
    cursor.execute("DROP TABLE IF EXISTS events")
    cursor.execute("DROP TABLE IF EXISTS guest_passes")

    cursor.execute("""
        CREATE TABLE workouts (
            part TEXT PRIMARY KEY,
            exercises TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            time TEXT,
            class_name TEXT,
            instructor TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            time TEXT,
            event_name TEXT,
            location TEXT,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE guest_passes (
            user_email TEXT PRIMARY KEY,
            full_name TEXT,
            passes_remaining INTEGER
        )
    """)

    conn.commit()

# =========================
# Seed data
# =========================

workout_descriptions = {
    "legs": ["squat", "calf raises", "leg extensions"],
    "arms": ["triceps", "dips", "curls"],
    "shoulders": ["army press", "dumbbell raises", "shrugs"]
}

weekly_classes = [
    ("monday", "9:00 AM", "Beats Ride", "Ava"),
    ("monday", "12:00 PM", "Sculpted Yoga", "Mia"),
    ("monday", "6:00 PM", "Boxing", "Jordan"),
    ("monday", "7:00 PM", "Pilates Fusion", "Emma"),

    ("tuesday", "10:00 AM", "Precision Run", "Noah"),
    ("tuesday", "1:00 PM", "Barre", "Sophia"),
    ("tuesday", "5:00 PM", "HIIT", "Liam"),
    ("tuesday", "7:00 PM", "Cycling", "Olivia"),

    ("wednesday", "9:00 AM", "Yoga Flow", "Ella"),
    ("wednesday", "12:00 PM", "Boxing", "Mason"),
    ("wednesday", "6:00 PM", "Beats Ride", "Lucas"),
    ("wednesday", "7:00 PM", "Strength", "Chloe"),

    ("thursday", "10:00 AM", "Mat Pilates", "Grace"),
    ("thursday", "1:00 PM", "Cycling", "Ethan"),
    ("thursday", "6:00 PM", "HIIT", "Harper"),
    ("thursday", "7:00 PM", "Sculpted Yoga", "Isla"),

    ("friday", "9:00 AM", "Precision Run", "Jack"),
    ("friday", "12:00 PM", "Barre", "Lily"),
    ("friday", "5:00 PM", "Boxing", "Leo"),
    ("friday", "7:00 PM", "Yoga Flow", "Zoe"),

    ("saturday", "10:00 AM", "Beats Ride", "Mila"),
    ("saturday", "12:00 PM", "Pilates Fusion", "James"),
    ("saturday", "2:00 PM", "HIIT", "Nora"),
    ("saturday", "5:00 PM", "Cycling", "Henry"),

    ("sunday", "9:00 AM", "Yoga Flow", "Aria"),
    ("sunday", "11:00 AM", "Mat Pilates", "Benjamin"),
    ("sunday", "1:00 PM", "Barre", "Scarlett"),
    ("sunday", "4:00 PM", "Recovery Mobility", "Layla"),
]

weekly_events = [
    ("monday", "6:30 PM", "Member Mixer", "Lounge", "Connect with members after evening classes."),
    ("tuesday", "7:30 PM", "Trainer Q&A", "Main Floor", "Meet Equinox trainers and ask programming questions."),
    ("wednesday", "6:00 PM", "Recovery Workshop", "Studio B", "Mobility, recovery, and reset session."),
    ("thursday", "7:00 PM", "Performance Nutrition Talk", "Lounge", "Nutrition tips for training and recovery."),
    ("friday", "6:30 PM", "Friday Night Flow", "Yoga Studio", "Special candlelit yoga session."),
    ("saturday", "11:00 AM", "Precision Run Clinic", "Treadmill Area", "Running form and treadmill performance workshop."),
    ("sunday", "12:00 PM", "Wellness Reset", "Studio A", "Guided stretch and recovery-focused community event."),
]

default_members = [
    ("farhan@example.com", "Farhan Shahbaz", 3),
    ("alex@example.com", "Alex Carter", 1),
]

# =========================
# Insert functions
# =========================

def insert_workouts(workout_descriptions):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()

        for part, exercises in workout_descriptions.items():
            cursor.execute(
                "INSERT OR REPLACE INTO workouts (part, exercises) VALUES (?, ?)",
                (part.lower(), json.dumps(exercises))
            )

        conn.commit()

def insert_classes(classes):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO classes (day, time, class_name, instructor) VALUES (?, ?, ?, ?)",
            classes
        )
        conn.commit()

def insert_events(events):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO events (day, time, event_name, location, description) VALUES (?, ?, ?, ?, ?)",
            events
        )
        conn.commit()

def insert_members(members):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT OR REPLACE INTO guest_passes (user_email, full_name, passes_remaining) VALUES (?, ?, ?)",
            members
        )
        conn.commit()

insert_workouts(workout_descriptions)
insert_classes(weekly_classes)
insert_events(weekly_events)
insert_members(default_members)

# =========================
# Helpers
# =========================

def get_today_name():
    return datetime.now().strftime("%A").lower()

# =========================
# Database tool functions
# =========================

def get_workout_description(part):
    print(f"DATABASE TOOL CALLED: Getting description for {part}", flush=True)

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT exercises FROM workouts WHERE part = ?",
            (part.lower(),)
        )
        result = cursor.fetchone()

    if not result:
        return f"No workout available for {part}."

    exercises = json.loads(result[0])
    return f"{part.capitalize()} workout: {', '.join(exercises)}"

def get_classes(day=None, class_name=None, time=None):
    print(f"DATABASE TOOL CALLED: get_classes(day={day}, class_name={class_name}, time={time})", flush=True)

    query = "SELECT day, time, class_name, instructor FROM classes WHERE 1=1"
    params = []

    if day:
        if day.lower() == "today":
            day = get_today_name()
        query += " AND LOWER(day) = ?"
        params.append(day.lower())

    if class_name:
        query += " AND LOWER(class_name) LIKE ?"
        params.append(f"%{class_name.lower()}%")

    if time:
        query += " AND time = ?"
        params.append(time)

    query += " ORDER BY day, time"

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()

    if not results:
        return "No matching classes found."

    lines = [
        f"{day.title()} at {time} — {class_name} with {instructor}"
        for day, time, class_name, instructor in results
    ]
    return "\n".join(lines)

def get_events(day=None):
    print(f"DATABASE TOOL CALLED: get_events(day={day})", flush=True)

    query = "SELECT day, time, event_name, location, description FROM events WHERE 1=1"
    params = []

    if day:
        if day.lower() == "today":
            day = get_today_name()
        query += " AND LOWER(day) = ?"
        params.append(day.lower())

    query += " ORDER BY day, time"

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()

    if not results:
        return "No events found."

    lines = [
        f"{day.title()} at {time} — {event_name} ({location}). {description}"
        for day, time, event_name, location, description in results
    ]
    return "\n".join(lines)

def get_guest_passes(user_email):
    print(f"DATABASE TOOL CALLED: get_guest_passes(user_email={user_email})", flush=True)

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT full_name, passes_remaining FROM guest_passes WHERE user_email = ?",
            (user_email.lower(),)
        )
        result = cursor.fetchone()

    if not result:
        return "Member not found."

    full_name, passes_remaining = result
    return f"{full_name} has {passes_remaining} guest pass(es) remaining."

def purchase_guest_passes(full_name, user_email, card_last4, quantity):
    print(f"DATABASE TOOL CALLED: purchase_guest_passes(user_email={user_email}, quantity={quantity})", flush=True)

    if quantity <= 0:
        return "Quantity must be greater than 0."

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT passes_remaining FROM guest_passes WHERE user_email = ?",
            (user_email.lower(),)
        )
        result = cursor.fetchone()

        if result:
            new_total = result[0] + quantity
            cursor.execute(
                """
                UPDATE guest_passes
                SET full_name = ?, passes_remaining = ?
                WHERE user_email = ?
                """,
                (full_name, new_total, user_email.lower())
            )
        else:
            new_total = quantity
            cursor.execute(
                """
                INSERT INTO guest_passes (user_email, full_name, passes_remaining)
                VALUES (?, ?, ?)
                """,
                (user_email.lower(), full_name, new_total)
            )

        conn.commit()

    return f"Purchase successful. {full_name} now has {new_total} guest pass(es) on file. Card ending in {card_last4} was charged."

print(get_workout_description("legs"))
print(get_classes(day="tuesday", time="7:00 PM"))
print(get_events(day="friday"))
print(get_guest_passes("farhan@example.com"))

# =========================
# Tool schemas
# =========================

get_workout_description_tool = {
    "name": "get_workout_description",
    "description": "Get the list of exercises for a specific body part.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The body part the user wants exercises for, such as legs, arms, or shoulders."
            }
        },
        "required": ["part"],
        "additionalProperties": False
    }
}

get_classes_tool = {
    "name": "get_classes",
    "description": "Get Equinox classes by day, class type, or time.",
    "parameters": {
        "type": "object",
        "properties": {
            "day": {
                "type": "string",
                "description": "Day of week such as monday, tuesday, or today"
            },
            "class_name": {
                "type": "string",
                "description": "Class type such as cycling, yoga, boxing, barre, hiit, pilates"
            },
            "time": {
                "type": "string",
                "description": "Class time such as 7:00 PM"
            }
        },
        "additionalProperties": False
    }
}

get_events_tool = {
    "name": "get_events",
    "description": "Get club events for a specific day or the full week.",
    "parameters": {
        "type": "object",
        "properties": {
            "day": {
                "type": "string",
                "description": "Day of week such as friday or today"
            }
        },
        "additionalProperties": False
    }
}

get_guest_passes_tool = {
    "name": "get_guest_passes",
    "description": "Get how many guest passes a member has remaining.",
    "parameters": {
        "type": "object",
        "properties": {
            "user_email": {
                "type": "string",
                "description": "The member email address"
            }
        },
        "required": ["user_email"],
        "additionalProperties": False
    }
}

purchase_guest_passes_tool = {
    "name": "purchase_guest_passes",
    "description": "Purchase additional Equinox guest passes for a member.",
    "parameters": {
        "type": "object",
        "properties": {
            "full_name": {
                "type": "string",
                "description": "Member full name"
            },
            "user_email": {
                "type": "string",
                "description": "Member email address"
            },
            "card_last4": {
                "type": "string",
                "description": "Last 4 digits of the credit card"
            },
            "quantity": {
                "type": "integer",
                "description": "Number of guest passes to purchase"
            }
        },
        "required": ["full_name", "user_email", "card_last4", "quantity"],
        "additionalProperties": False
    }
}

tools = [
    {"type": "function", "function": get_workout_description_tool},
    {"type": "function", "function": get_classes_tool},
    {"type": "function", "function": get_events_tool},
    {"type": "function", "function": get_guest_passes_tool},
    {"type": "function", "function": purchase_guest_passes_tool},
]

# =========================
# Audio + image helpers
# =========================

def talker(message):
    response = openai.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="onyx",
        input=message
    )

    audio_path = "reply.mp3"
    with open(audio_path, "wb") as f:
        f.write(response.content)

    return audio_path

def artist(topic):
    image_response = openai.images.generate(
        model="dall-e-3",
        prompt=f"A realistic luxury fitness-themed image representing {topic} at Equinox",
        size="1024x1024",
        n=1,
        response_format="b64_json",
    )

    image_base64 = image_response.data[0].b64_json
    image_data = base64.b64decode(image_base64)
    return Image.open(BytesIO(image_data))

# =========================
# Tool handling
# =========================

def handle_tool_calls_and_return_workouts(message):
    responses = []
    workouts = []

    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if function_name == "get_workout_description":
            part = arguments.get("part")
            workouts.append(part)
            result = get_workout_description(part)

        elif function_name == "get_classes":
            day = arguments.get("day")
            class_name = arguments.get("class_name")
            time = arguments.get("time")

            if class_name:
                workouts.append(class_name)

            result = get_classes(day=day, class_name=class_name, time=time)

        elif function_name == "get_events":
            day = arguments.get("day")
            result = get_events(day=day)

        elif function_name == "get_guest_passes":
            user_email = arguments.get("user_email")
            result = get_guest_passes(user_email=user_email)

        elif function_name == "purchase_guest_passes":
            full_name = arguments.get("full_name")
            user_email = arguments.get("user_email")
            card_last4 = arguments.get("card_last4")
            quantity = arguments.get("quantity")

            result = purchase_guest_passes(
                full_name=full_name,
                user_email=user_email,
                card_last4=card_last4,
                quantity=quantity
            )

        else:
            result = "Unknown tool call."

        responses.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })

    return responses, workouts

# =========================
# Chat logic
# =========================

def chat(history):
    messages = [{"role": "system", "content": system_message}] + history

    response = openai.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools
    )

    workouts = []
    image = None

    while response.choices[0].finish_reason == "tool_calls":
        assistant_message = response.choices[0].message
        responses, workouts = handle_tool_calls_and_return_workouts(assistant_message)

        messages.append({
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in assistant_message.tool_calls
            ]
        })

        messages.extend(responses)

        response = openai.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools
        )

    reply = response.choices[0].message.content or "I’m sorry, I could not generate a response."
    updated_history = history + [{"role": "assistant", "content": reply}]
    audio_path = talker(reply)

    if workouts:
        image = artist(workouts[0])

    return updated_history, audio_path, image

def put_message_in_chatbot(message, history):
    history = history or []
    return "", history + [{"role": "user", "content": message}]

# =========================
# UI definition
# =========================

with gr.Blocks() as ui:
    with gr.Row():
        chatbot = gr.Chatbot(height=500, type="messages")
        image_output = gr.Image(height=500, interactive=False)

    with gr.Row():
        audio_output = gr.Audio(autoplay=True)

    with gr.Row():
        message = gr.Textbox(label="Chat with our AI Assistant:")

    message.submit(
        put_message_in_chatbot,
        inputs=[message, chatbot],
        outputs=[message, chatbot]
    ).then(
        chat,
        inputs=chatbot,
        outputs=[chatbot, audio_output, image_output]
    )

ui.launch(inbrowser=True, auth=("farhan", "shahbaz"))
