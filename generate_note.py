import anthropic
import datetime
import os
import sys

# Topic rotation by day
TOPICS = {
    0: ("Productivity", "Productivity Book Summary — a key concept or framework from a classic or modern productivity book. Never repeat books or concepts already covered."),
    1: ("Sales", "Sales Framework — a specific, named sales methodology, technique, or mental model used by top B2B sellers. Never repeat frameworks already covered."),
    2: ("Customer Success", "Customer Success — a specific concept, metric, motion, or philosophy from the world of CS and account management. Never repeat concepts already covered."),
    3: ("B2B Tech", "B2B Tech Update — a specific emerging technology, platform shift, or product category reshaping B2B software today. Never repeat topics already covered."),
    4: ("AI", "AI Learnings — a specific AI concept, architecture, technique, research finding, or real-world application. Never repeat topics already covered."),
    5: ("Philosophy", "Philosophy — a specific philosophical concept, thought experiment, or thinker's idea with practical relevance today. Never repeat topics already covered."),
    6: ("Science & Wonder", "Science/Physics/Astrophysics/Nature Trivia — a specific, fascinating concept or discovery from the natural sciences. Never repeat topics already covered."),
}

SYSTEM_PROMPT = """You are Gaurav's daily learning assistant. Your job is to write a rich, engaging daily learning note on ONE specific concept within the given topic.

Rules:
- 500–600 words of flowing, intelligent prose. No bullet dumps.
- Write with intellectual curiosity, depth, and a narrative arc — like a brilliant friend explaining something fascinating.
- Use real names, real history, real research where relevant.
- Format:
  Line 1: # [Topic Area] · [Date e.g. March 10, 2026]
  Line 2: (blank)
  Line 3: ## [Specific Concept Name]: [Intriguing Subtitle]
  Line 4: (blank)
  Then 500–600 words of prose.
  End with: 💡 **One thing to try today:** [one concrete, specific action — not generic advice]
- Never use bullet points in the body.
- Rotate concepts — never repeat what's been written before in this series."""

def generate_note():
    today = datetime.date.today()
    weekday = today.weekday()  # 0=Mon, 6=Sun
    topic_label, topic_instruction = TOPICS[weekday]
    date_str = today.strftime("%B %-d, %Y")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_prompt = f"""Today is {date_str} ({today.strftime('%A')}).

Write today's learning note on the topic: **{topic_instruction}**

Remember: 500–600 words, prose only, end with the 💡 one thing to try."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )

    note_content = message.content[0].text
    return note_content, topic_label, date_str, today

def save_note(content, topic_label, date_str, today):
    # Save to dated markdown file
    filename = f"notes/{today.strftime('%Y-%m-%d')}-{topic_label.lower().replace(' ', '-').replace('&', 'and')}.md"
    os.makedirs("notes", exist_ok=True)
    
    with open(filename, "w") as f:
        f.write(content)
    
    print(f"✅ Note saved: {filename}")
    return filename

def update_index(notes_dir="notes"):
    """Rebuild index.md listing all notes newest first."""
    files = sorted(
        [f for f in os.listdir(notes_dir) if f.endswith(".md") and f != "index.md"],
        reverse=True
    )
    
    lines = ["# Gaurav's Daily Learning Notes\n\n"]
    lines.append("A daily note on Productivity, Sales, Customer Success, B2B Tech, AI, Philosophy, and Science.\n\n")
    lines.append("---\n\n")
    
    for f in files:
        date_part = f[:10]  # YYYY-MM-DD
        try:
            d = datetime.datetime.strptime(date_part, "%Y-%m-%d")
            display = d.strftime("%B %-d, %Y")
        except:
            display = date_part
        topic = f[11:].replace("-", " ").replace(".md", "").title()
        lines.append(f"- [{display} — {topic}]({f})\n")
    
    with open(f"{notes_dir}/index.md", "w") as f:
        f.writelines(lines)
    
    print("✅ Index updated")

if __name__ == "__main__":
    print("🧠 Generating today's learning note...")
    content, topic_label, date_str, today = generate_note()
    filename = save_note(content, topic_label, date_str, today)
    update_index()
    print("\n--- PREVIEW ---\n")
    print(content[:300] + "...")
    print("\n✅ Done!")
