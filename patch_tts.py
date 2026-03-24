"""
patch_tts.py — Retrofits the TTS player into all existing note HTML files.
Run once after deploying generate_note.py with TTS support.
Safe to re-run: skips files that already have the TTS player.
"""
import os
import re

# ── TTS CSS (same as in generate_note.py) ────────────────────────────────────
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

# ── TTS JS (same as in generate_note.py) ─────────────────────────────────────
TTS_JS = """<script>
(function () {
  if (!window.speechSynthesis) return;

  var synth = window.speechSynthesis;
  var els = [], idx = 0, playing = false, paused = false;

  var PREFERRED_VOICES = [
    'Google UK English Female',
    'Google US English',
    'Microsoft Aria Online (Natural) - English (United States)',
    'Microsoft Jenny Online (Natural) - English (United States)',
    'Samantha',
    'Karen',
    'Daniel',
    'Moira',
    'Tessa',
    'Rishi'
  ];

  function pickVoice() {
    var voices = synth.getVoices();
    for (var i = 0; i < PREFERRED_VOICES.length; i++) {
      var v = voices.find(function (x) { return x.name === PREFERRED_VOICES[i]; });
      if (v) return v;
    }
    var natural = voices.find(function (v) { return /natural|online/i.test(v.name) && v.lang.startsWith('en'); });
    if (natural) return natural;
    var regional = voices.find(function (v) { return v.lang === 'en-GB' || v.lang === 'en-AU'; });
    if (regional) return regional;
    return voices.find(function (v) { return v.lang.startsWith('en'); }) || null;
  }

  function collect() {
    return Array.from(document.querySelectorAll('h1, h2, p')).filter(function (el) {
      return !el.closest('footer') &&
             !el.classList.contains('back') &&
             el.innerText.trim().length > 0;
    });
  }

  var bar = document.createElement('div');
  bar.id = 'tts-bar';
  bar.innerHTML =
    '<button id="tts-play">\U0001f50a Listen</button>' +
    '<button id="tts-stop" disabled>\u23f9 Stop</button>' +
    '<label>Speed:\u00a0<select id="tts-rate">' +
      '<option value="0.75">0.75\u00d7</option>' +
      '<option value="0.9" selected>0.9\u00d7</option>' +
      '<option value="1">1\u00d7</option>' +
      '<option value="1.2">1.2\u00d7</option>' +
    '</select></label>' +
    '<span id="tts-progress"></span>';
  document.body.insertBefore(bar, document.body.firstChild);

  var playBtn = document.getElementById('tts-play');
  var stopBtn = document.getElementById('tts-stop');
  var rateEl  = document.getElementById('tts-rate');
  var progEl  = document.getElementById('tts-progress');

  function highlight(el) {
    els.forEach(function (e) { e.classList.remove('tts-reading'); });
    if (el) {
      el.classList.add('tts-reading');
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

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
    utt.pitch = 0.95;
    utt.onend = function () { if (playing) speakAt(idx + 1); };
    utt.onerror = function (e) { if (e.error !== 'interrupted') speakAt(idx + 1); };
    synth.speak(utt);
  }

  function finish() {
    playing = false; paused = false;
    highlight(null);
    playBtn.textContent = '\U0001f50a Listen';
    playBtn.classList.remove('active');
    stopBtn.disabled = true;
    progEl.textContent = '';
  }

  playBtn.addEventListener('click', function () {
    if (!playing && !paused) {
      els = collect();
      playing = true;
      playBtn.textContent = '\u23f8 Pause';
      playBtn.classList.add('active');
      stopBtn.disabled = false;
      speakAt(0);
    } else if (playing) {
      synth.pause();
      paused = true; playing = false;
      playBtn.textContent = '\u25b6 Resume';
      playBtn.classList.remove('active');
    } else {
      synth.resume();
      paused = false; playing = true;
      playBtn.textContent = '\u23f8 Pause';
      playBtn.classList.add('active');
    }
  });

  stopBtn.addEventListener('click', function () {
    synth.cancel();
    finish();
  });

  window.addEventListener('beforeunload', function () { synth.cancel(); });
})();
</script>"""


def patch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # Skip if already patched
    if 'tts-bar' in html:
        print(f"  ⏭  Already has TTS: {filepath}")
        return False

    # Inject CSS before </style>
    if '</style>' not in html:
        print(f"  ⚠  No </style> found: {filepath}")
        return False

    html = html.replace('</style>', TTS_CSS + '\n </style>', 1)

    # Inject JS before </body>
    if '</body>' not in html:
        print(f"  ⚠  No </body> found: {filepath}")
        return False

    html = html.replace('</body>', TTS_JS + '\n</body>', 1)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  ✅ Patched: {filepath}")
    return True


def main():
    notes_dir = 'notes'
    if not os.path.isdir(notes_dir):
        print(f"No '{notes_dir}' directory found. Run from repo root.")
        return

    html_files = sorted([
        os.path.join(notes_dir, f)
        for f in os.listdir(notes_dir)
        if f.endswith('.html') and f != 'index.html'
    ])

    if not html_files:
        print("No note HTML files found.")
        return

    print(f"Patching {len(html_files)} note files with TTS player...\n")
    patched = sum(1 for fp in html_files if patch_file(fp))
    skipped = len(html_files) - patched
    print(f"\nDone: {patched} patched, {skipped} already had TTS.")


if __name__ == '__main__':
    main()
