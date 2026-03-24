import anthropic
import datetime
import os
import re

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
- 500-600 words of flowing, intelligent prose. No bullet dumps.
- Write with intellectual curiosity, depth, and a narrative arc like a brilliant friend explaining something fascinating.
- Use real names, real history, real research where relevant.
- Format:
 Line 1: # [Topic Area] · [Date e.g. March 10, 2026]
 Line 2: (blank)
 Line 3: ## [Specific Concept Name]: [Intriguing Subtitle]
 Line 4: (blank)
 Then 500-600 words of prose.
 End with: 💡 **One thing to try today:** [one concrete, specific action — not generic advice]
- Never use bullet points in the body.
- Rotate concepts — never repeat what's been written before in this series."""

# ── Text-to-Speech styles (injected into every note page) ──────────────────
TTS_CSS = """
 /* ── TTS Player ── */
 #tts-bar {
   position: sticky;
   top: 0;
   background: rgba(255,255,255,0.97);
   backdrop-filter: blur(4px);
   -webkit-backdrop-filter: blur(4px);
   border-bottom: 1px solid #eee;
   padding: 10px 0;
   margin: -20px 0 36px;
   font-family: sans-serif;
   display: flex;
   align-items: center;
   gap: 10px;
   font-size: 0.82rem;
   z-index: 50;
 }
 #tts-bar button {
   padding: 5px 14px;
   border: 1px solid #ddd;
   border-radius: 20px;
   cursor: pointer;
   font-size: 0.82rem;
   background: white;
   color: #444;
   transition: background 0.15s, border-color 0.15s;
   white-space: nowrap;
 }
 #tts-bar button:hover:not(:disabled) { background: #f5f5f5; border-color: #ccc; }
 #tts-bar button:disabled { opacity: 0.35; cursor: default; }
 #tts-bar button.active { background: #fffbea; border-color: #e0c060; }
 #tts-bar select {
   padding: 4px 6px;
   border: 1px solid #ddd;
   border-radius: 4px;
   font-size: 0.8rem;
   color: #555;
   cursor: pointer;
   background: white;
 }
 #tts-bar label { color: #999; font-size: 0.8rem; }
 #tts-progress { color: #bbb; font-size: 0.78rem; letter-spacing: 0.02em; }
 .tts-reading {
   background: #fffbea !important;
   border-radius: 3px;
   outline: 2px solid #f0d060;
   outline-offset: 2px;
   transition: background 0.25s;
 }"""

# ── Text-to-Speech script (injected before </body> on every note page) ───────
TTS_JS = """<script>
(function () {
  if (!window.speechSynthesis) return;

  var synth = window.speechSynthesis;
  var els = [], idx = 0, playing = false, paused = false;

  /* ── Voice priority: most natural / least robotic first ──
     Falls back gracefully on any OS / browser                */
  var PREFERRED_VOICES = [
    'Google UK English Female',          // Chrome – best quality
    'Google US English',                 // Chrome – very natural
    'Microsoft Aria Online (Natural) - English (United States)',   // Edge
    'Microsoft Jenny Online (Natural) - English (United States)',  // Edge
    'Samantha',                          // macOS – high quality
    'Karen',                             // macOS Australian – smooth
    'Daniel',                            // macOS British – warm
    'Moira',                             // macOS Irish – pleasant
    'Tessa',                             // macOS South African – clear
    'Rishi'                              // macOS Indian English – natural
  ];

  function pickVoice() {
    var voices = synth.getVoices();
    for (var i = 0; i < PREFERRED_VOICES.length; i++) {
      var v = voices.find(function (x) { return x.name === PREFERRED_VOICES[i]; });
      if (v) return v;
    }
    // Fallback: any voice with "Natural" or "Online" in the name
    var natural = voices.find(function (v) { return /natural|online/i.test(v.name) && v.lang.startsWith('en'); });
    if (natural) return natural;
    // Fallback: en-GB or en-AU (tend to sound warmer than en-US defaults)
    var regional = voices.find(function (v) { return v.lang === 'en-GB' || v.lang === 'en-AU'; });
    if (regional) return regional;
    // Final fallback: any English
    return voices.find(function (v) { return v.lang.startsWith('en'); }) || null;
  }

  /* ── Collect readable elements (skip footer / back-link) ── */
  function collect() {
    return Array.from(document.querySelectorAll('h1, h2, p')).filter(function (el) {
      return !el.closest('footer') &&
             !el.classList.contains('back') &&
             el.innerText.trim().length > 0;
    });
  }

  /* ── Build the sticky player bar ── */
  var bar = document.createElement('div');
  bar.id = 'tts-bar';
  bar.innerHTML =
    '<button id="tts-play">🔊 Listen</button>' +
    '<button id="tts-stop" disabled>⏹ Stop</button>' +
    '<label>Speed:&nbsp;<select id="tts-rate">' +
      '<option value="0.75">0.75×</option>' +
      '<option value="0.9" selected>0.9×</option>' +
      '<option value="1">1×</option>' +
      '<option value="1.2">1.2×</option>' +
    '</select></label>' +
    '<span id="tts-progress"></span>';
  document.body.insertBefore(bar, document.body.firstChild);

  var playBtn = document.getElementById('tts-play');
  var stopBtn = document.getElementById('tts-stop');
  var rateEl  = document.getElementById('tts-rate');
  var progEl  = document.getElementById('tts-progress');

  /* ── Highlight current element ── */
  function highlight(el) {
    els.forEach(function (e) { e.classList.remove('tts-reading'); });
    if (el) {
      el.classList.add('tts-reading');
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  /* ── Speak from a given index ── */
  function speakAt(i) {
    synth.cancel();
    if (i >= els.length) { finish(); return; }
    idx = i;
    highlight(els[i]);
    progEl.textContent = (i + 1) + ' / ' + els.length;

    var utt = new SpeechSynthesisUtterance(els[i].innerText);
    var voice = pickVoice();
    if (voice) utt.voice = voice;
    utt.rate  = parseFloat(rateEl.value);
    utt.pitch = 0.95;   // slightly lower pitch = warmer, less sharp
    utt.onend = function () { if (playing) speakAt(idx + 1); };
    utt.onerror = function (e) { if (e.error !== 'interrupted') speakAt(idx + 1); };
    synth.speak(utt);
  }

  /* ── Reset to idle state ── */
  function finish() {
    playing = false; paused = false;
    highlight(null);
    playBtn.textContent = '🔊 Listen';
    playBtn.classList.remove('active');
    stopBtn.disabled = true;
    progEl.textContent = '';
  }

  /* ── Play / Pause / Resume ── */
  playBtn.addEventListener('click', function () {
    if (!playing && !paused) {
      els = collect();
      playing = true;
      playBtn.textContent = '⏸ Pause';
      playBtn.classList.add('active');
      stopBtn.disabled = false;
      speakAt(0);
    } else if (playing) {
      synth.pause();
      paused = true; playing = false;
      playBtn.textContent = '▶ Resume';
      playBtn.classList.remove('active');
    } else {
      synth.resume();
      paused = false; playing = true;
      playBtn.textContent = '⏸ Pause';
      playBtn.classList.add('active');
    }
  });

  /* ── Stop ── */
  stopBtn.addEventListener('click', function () {
    synth.cancel();
    finish();
  });

  /* ── Cancel on page exit ── */
  window.addEventListener('beforeunload', function () { synth.cancel(); });
})();
</script>"""


def generate_note():
    today = datetime.date.today()
    weekday = today.weekday()
    topic_label, topic_instruction = TOPICS[weekday]
    date_str = today.strftime("%B %-d, %Y")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_prompt = f"""Today is {date_str} ({today.strftime('%A')}).

Write today's learning note on the topic: **{topic_instruction}**

Remember: 500-600 words, prose only, end with the one thing to try."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )

    note_content = message.content[0].text
    return note_content, topic_label, date_str, today


def markdown_to_html(md):
    html = ""
    for line in md.split("\n"):
        if line.startswith("## "):
            html += f"<h2>{line[3:]}</h2>\n"
        elif line.startswith("# "):
            html += f"<h1>{line[2:]}</h1>\n"
        elif line.strip() == "":
            html += "<br>\n"
        else:
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            html += f"<p>{line}</p>\n"
    return html


def save_note_html(content, topic_label, date_str, today):
    os.makedirs("notes", exist_ok=True)
    slug = topic_label.lower().replace(" ", "-").replace("&", "and")
    filename = f"notes/{today.strftime('%Y-%m-%d')}-{slug}.html"

    body_html = markdown_to_html(content)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
 <meta charset="UTF-8">
 <meta name="viewport" content="width=device-width, initial-scale=1.0">
 <title>{topic_label} · {date_str}</title>
 <style>
 body {{ font-family: Georgia, serif; max-width: 680px; margin: 60px auto; padding: 0 24px; color: #1a1a1a; line-height: 1.8; }}
 h1 {{ font-size: 1.4rem; color: #555; font-weight: normal; border-bottom: 1px solid #eee; padding-bottom: 12px; }}
 h2 {{ font-size: 1.6rem; margin-top: 8px; line-height: 1.3; }}
 p {{ margin: 1.2em 0; font-size: 1.05rem; }}
 strong {{ background: #fffbea; padding: 1px 3px; }}
 .back {{ display: inline-block; margin-top: 48px; font-size: 0.9rem; color: #888; text-decoration: none; font-family: sans-serif; }}
 .back:hover {{ color: #333; }}
 footer {{ margin-top: 60px; font-size: 0.8rem; color: #aaa; font-family: sans-serif; border-top: 1px solid #eee; padding-top: 16px; }}
{TTS_CSS}
 </style>
</head>
<body>
{body_html}
<a class="back" href="../index.html">← All notes</a>
<footer>Gaurav's Daily Learning Notes · Auto-generated every morning</footer>
{TTS_JS}
</body>
</html>"""

    with open(filename, "w") as f:
        f.write(html)

    print(f"Note saved: {filename}")
    return filename, slug


def update_index(notes_dir="notes"):
    files = sorted(
        [f for f in os.listdir(notes_dir) if f.endswith(".html") and f != "index.html"],
        reverse=True
    )

    items = ""
    for f in files:
        date_part = f[:10]
        try:
            d = datetime.datetime.strptime(date_part, "%Y-%m-%d")
            display = d.strftime("%B %-d, %Y")
        except:
            display = date_part
        topic = f[11:].replace("-", " ").replace(".html", "").title()
        items += f' <li><a href="notes/{f}">{display} — {topic}</a></li>\n'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
 <meta charset="UTF-8">
 <meta name="viewport" content="width=device-width, initial-scale=1.0">
 <title>Gaurav's Daily Learning Notes</title>
 <style>
 body {{ font-family: Georgia, serif; max-width: 680px; margin: 60px auto; padding: 0 24px; color: #1a1a1a; line-height: 1.8; }}
 h1 {{ font-size: 2rem; margin-bottom: 4px; }}
 .subtitle {{ color: #777; font-size: 1rem; margin-bottom: 40px; font-family: sans-serif; }}
 ul {{ list-style: none; padding: 0; }}
 li {{ border-bottom: 1px solid #f0f0f0; padding: 12px 0; }}
 a {{ color: #1a1a1a; text-decoration: none; font-size: 1.05rem; }}
 a:hover {{ color: #0066cc; }}
 footer {{ margin-top: 60px; font-size: 0.8rem; color: #aaa; font-family: sans-serif; border-top: 1px solid #eee; padding-top: 16px; }}
 </style>
</head>
<body>
 <h1>📚 Gaurav's Daily Learning Notes</h1>
 <p class="subtitle">One idea every morning — Productivity · Sales · CS · B2B Tech · AI · Philosophy · Science</p>
 <ul>
{items} </ul>
 <footer>Auto-generated every morning using Claude AI · <a href="https://github.com/gaurav-gps-growth/learning-notes">View source</a></footer>
</body>
</html>"""

    with open("index.html", "w") as f:
        f.write(html)

    print("index.html updated")


if __name__ == "__main__":
    print("Generating today's learning note...")
    content, topic_label, date_str, today = generate_note()
    filename, slug = save_note_html(content, topic_label, date_str, today)
    update_index()
    print("\n--- PREVIEW ---\n")
    print(content[:300] + "...")
    print("\nDone!")
