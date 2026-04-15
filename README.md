# Equinox AI Assistant 🏋️‍♂️

An AI-powered gym assistant that simulates an Equinox-style member experience.  
Built with **Python, OpenAI, Gradio, and SQLite**, this app allows users to interact with a smart assistant to explore workouts, classes, events, and manage guest passes.

---

## 🚀 Features

### 🏋️ Workout Recommendations
- Get exercises by body part (legs, arms, shoulders)
- Backed by a structured SQLite database

### 📅 Class Scheduling
- Query weekly class schedules (9AM–8PM)
- Filter by:
  - Day (`"today"`, `"monday"`, etc.)
  - Class type (`"cycling"`, `"yoga"`, `"boxing"`)
  - Time (`"7:00 PM"`)

### 🎉 Events Calendar
- View Equinox-style events throughout the week
- Examples:
  - Member mixers
  - Recovery workshops
  - Nutrition talks

### 🎟️ Guest Pass Management
- Check remaining guest passes
- Purchase additional passes (mock checkout flow)

### 🔊 Voice Responses
- AI-generated speech using OpenAI TTS

### 🖼️ Image Generation
- AI-generated visuals based on user queries (fitness-themed)

---

## 🧠 How It Works

This project uses **OpenAI function/tool calling** to dynamically decide when to query the database.

Flow:
1. User sends a message via Gradio UI
2. LLM determines if a tool is needed
3. Tool is executed (SQLite query)
4. Result is returned to LLM
5. Final response is generated
6. Optional:
   - Voice output (TTS)
   - Image generation (DALL·E)

---

## 🏗️ Tech Stack

- **Python**
- **OpenAI API**
  - Chat Completions (tool calling)
  - Text-to-Speech
  - Image Generation
- **Gradio** (UI)
- **SQLite** (data storage)
- **Pillow** (image handling)

---

## 📁 Project Structure
