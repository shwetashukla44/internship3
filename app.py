import streamlit as st
import ollama
import urllib.parse
import requests
import random
import re
from io import BytesIO

# Safe import checks for optional libraries
try:
    from gtts import gTTS
    gtts_available = True
except ImportError:
    gtts_available = False

try:
    import pypdf
    pypdf_available = True
except ImportError:
    pypdf_available = False

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    youtube_available = True
except ImportError:
    youtube_available = False

try:
    import speech_recognition as sr
    sr_available = True
except ImportError:
    sr_available = False

# ----------------------------------------------------
# MULTI-LINGUAL UI DICTIONARY (WITH UPGRADED NAMES)
# ----------------------------------------------------
languages = {
    "English": {
        "nav": "Navigate Sections:",
        "config": "Configuration",
        "chat_title": "💬 Control Center",
        "chat_caption": "Your private communication hub for programming, mathematics, writing, and custom assistance.",
        "clear_history": "🧹 Clear History",
        "export_history": "📥 Export Conversation (Markdown)",
        "renov_title": "🛠️ Style Lab",
        "renov_caption": "Optimize spatial design, structures, and layout concepts with automated renderings.",
        "doc_title": "📚 Data Vault",
        "doc_caption": "Process and analyze local text, research PDFs, or WAV audio files securely offline.",
        "yt_title": "🎥 Study Sheets",
        "yt_caption": "Extract and synthesize YouTube transcripts into structured reference guides and custom QA.",
        "img_title": "🎨 Canvas",
        "img_col": "Visual prompt construction",
        "img_pres": "Select Rendering Preset:",
        "img_gen": "Generate Concept Image"
    },
    "Spanish": {
        "nav": "Navegar Secciones:",
        "config": "Configuración",
        "chat_title": "💬 Centro de Control",
        "chat_caption": "Su centro de comunicación privado para programación, matemáticas, escritura y soporte.",
        "clear_history": "🧹 Limpiar Historial",
        "export_history": "📥 Exportar Conversación (Markdown)",
        "renov_title": "🛠️ Laboratorio de Estilo",
        "renov_caption": "Optimice el diseño espacial, estructuras y conceptos de distribución con renderizados automáticos.",
        "doc_title": "📚 Bóveda de Datos",
        "doc_caption": "Procese y analice textos locales, PDFs de investigación o archivos de audio WAV de forma segura sin conexión.",
        "yt_title": "🎥 Hojas de Estudio",
        "yt_caption": "Extraiga y sintetice transcripciones de YouTube en guías de referencia estructuradas.",
        "img_title": "🎨 Lienzo",
        "img_col": "Construcción de prompt visual",
        "img_pres": "Seleccione Preset de Renderizado:",
        "img_gen": "Generar Imagen de Concepto"
    },
    "French": {
        "nav": "Naviguer dans les sections :",
        "config": "Configuration",
        "chat_title": "💬 Centre de Contrôle",
        "chat_caption": "Votre hub de communication privé pour la programmation, les mathématiques, l'écriture et l'assistance.",
        "clear_history": "🧹 Effacer l'Historique",
        "export_history": "📥 Exporter la Conversation (Markdown)",
        "renov_title": "🛠️ Labo de Style",
        "renov_caption": "Optimisez l'agencement spatial et les concepts de mise en page avec des rendus automatiques.",
        "doc_title": "📚 Coffre de Données",
        "doc_caption": "Traisez et analysez des textes locaux, des PDF de recherche ou des fichiers audio WAV hors ligne.",
        "yt_title": "🎥 Fiches de Révision",
        "yt_caption": "Extrayez et synthétisez les transcriptions YouTube en fiches de référence structurées.",
        "img_title": "🎨 Canevas",
        "img_col": "Construction de prompt visual",
        "img_pres": "Sélectionnez le style de rendu :",
        "img_gen": "Générer l'image de concept"
    }
}

# Configure the page layout
st.set_page_config(
page_title="AI Studio",
page_icon="✨",
layout="wide",
initial_sidebar_state="expanded",
)

st.markdown(
"""
<div class="hero">
<span class="badge">✨ AI Studio</span>
<h1>Your all-in-one AI workspace</h1>
<p>Chat, create, summarize, translate, and design — in one clean surface.</p>
</div>
""",
unsafe_allow_html=True,
)

CUSTOM_CSS = """
<style>
:root{
  --bg:#0b1020; --card:#131a33; --ink:#eef1ff; --muted:#93a0c8;
  --accent:#7c9cff; --accent2:#b78cff; --ring:rgba(124,156,255,.35);
}
html, body, [class*="css"]  { font-family: 'Inter', system-ui, sans-serif; }
.main .block-container{ padding-top: 1.2rem; max-width: 1200px; }
.hero{
  background: radial-gradient(1200px 400px at 10% -10%, rgba(124,156,255,.25), transparent 60%),
              radial-gradient(900px 400px at 110% 10%, rgba(183,140,255,.22), transparent 60%),
              linear-gradient(180deg,#0f1530,#0b1020);
  border:1px solid rgba(255,255,255,.06);
  border-radius:22px; padding:26px 28px; margin-bottom:18px;
}
.hero h1{ font-size: 2rem; margin:0; letter-spacing:-.02em;color:#b8c1e0;}
.hero p{ color:#b8c1e0; margin:.35rem 0 0;}
.badge{
  display:inline-block; padding:4px 10px; border-radius:999px;
  background:rgba(124,156,255,.12); color:#c9d3ff; font-size:.75rem;
  border:1px solid rgba(124,156,255,.25); margin-right:6px;
}
.card{
  background: var(--card); border:1px solid rgba(255,255,255,.06);
  border-radius:16px; padding:16px 18px;
}
.stButton>button{
  border-radius:12px; border:1px solid rgba(255,255,255,.08);
  background: linear-gradient(135deg,#7c9cff,#b78cff); color:white;
  font-weight:600; padding:.55rem 1rem;
}
.stButton>button:hover{ filter: brightness(1.05); box-shadow:0 0 0 4px var(--ring); }
.stTextInput>div>div>input, .stTextArea textarea{
  border-radius:12px !important;
}
hr{ border-color: rgba(255,255,255,.06); }
.small{ color:var(--muted); font-size:.85rem;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Dynamically fetch models installed on the user's local Ollama server
def get_local_ollama_models():
    fallback = ["llama3", "mistral", "gemma", "phi3"]
    try:
        models_info = ollama.list()
        models = [m['name'] for m in models_info.get('models', [])]
        if models:
            return models
    except Exception:
        pass
    return fallback

# Build a global metadata lookup for model sizes
model_sizes = {}
try:
    models_info = ollama.list()
    for m in models_info.get('models', []):
        model_sizes[m['name']] = m.get('size', 0)
except Exception:
    pass

# Custom label formatter for the selectbox dropdown
def format_model_label(model_name):
    size_bytes = model_sizes.get(model_name, 0)
    clean_name = model_name.split(":")[0].replace("-", " ").replace("_", " ").title()
    
    icon = "🧠"
    if "vision" in model_name.lower() or "llava" in model_name.lower():
        icon = "👁️ Vision"
    elif "coder" in model_name.lower() or "code" in model_name.lower():
        icon = "💻 Code"
    elif "llama" in model_name.lower():
        icon = "🦙 Llama"
    elif "gemma" in model_name.lower():
        icon = "💎 Gemma"
    elif "mistral" in model_name.lower():
        icon = "🌪️ Mistral"
    elif "phi" in model_name.lower():
        icon = "💻 Phi"

    if size_bytes > 0:
        size_gb = size_bytes / (1024**3)
        return f"{icon} — {clean_name} ({size_gb:.1f} GB)"
    return f"{icon} — {clean_name}"

# Helper function to extract YouTube Video ID
def get_yt_video_id(url):
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

# Helper function to extract text metrics
def get_text_metrics(text):
    words = len(text.split())
    reading_time = max(1, round(words / 200))
    chars = len(text)
    return words, reading_time, chars

# Helper function to clean raw Mermaid formatting
def clean_mermaid(text: str) -> str:
    """
    Advanced scraper that extracts ONLY the Mermaid syntax from a 
    chatty AI response, even if the AI adds conversational text.
    """
    # 1. Remove Markdown code blocks (```mermaid ... ```) if present
    if "```mermaid" in text:
        text = text.split("```mermaid")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    # 2. Use Regex to find the first valid Mermaid keyword (graph, flowchart, etc.)
    # This effectively "scrapes" the code out of the middle of a sentence.
    match = re.search(r'(graph\s+TD|flowchart\s+TD|sequenceDiagram|classDiagram|stateDiagram|erDiagram|pie|mindmap|timeline)', text, re.IGNORECASE)
    
    if match:
        # Slice the string to start exactly where the diagram type is found
        text = text[match.start():]
    
    # 3. Final cleanup: remove any trailing text after the diagram ends 
    # (Useful if the AI says: "graph TD ... [diagram] ... hope this helps!")
    # We look for the last line that doesn't look like diagram syntax, 
    # but for simplicity in Streamlit, just returning the slice is usually enough.
    
    return text.strip()

# Universal YouTube Transcript Fetcher (Supports old and new library versions)
def fetch_youtube_transcript(video_id):
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.fetch(video_id, languages=['en']).to_raw_data()
        return " ".join([t['text'] for t in transcript_list])
    except Exception:
        pass
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        return " ".join([t['text'] for t in transcript_list])
    except Exception:
        pass
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t['text'] for t in transcript_list])
    except Exception as e:
        raise Exception(f"All transcript extraction methods failed. Details: {e}")

# Helper function for text-to-speech with byte download support
def get_tts_audio_and_bytes(text_to_speak):
    if not gtts_available:
        return None, None
    try:
        fp = BytesIO()
        tts = gTTS(text=text_to_speak[:1000], lang='en')
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_bytes = fp.getvalue()
        return fp, audio_bytes
    except Exception:
        return None, None

# Helper function for PDF parsing
def parse_pdf(uploaded_file):
    if not pypdf_available:
        return "pypdf library not installed. Please run 'pip install pypdf'."
    try:
        reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except Exception as e:
        return f"Error parsing PDF: {e}"

# Helper function to capture mic audio locally
def record_mic():
    if not sr_available:
        st.error("SpeechRecognition library is missing.")
        return None
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.toast("Listening... Speak now!")
            r.adjust_for_ambient_noise(source, duration=0.8)
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            st.toast("Processing audio...")
            return r.recognize_google(audio)
    except Exception as e:
        st.error("Microphone access failed.")
        st.info("Tip: Ensure 'pyaudio' is installed (`pip install pyaudio`) and microphone permissions are granted.")
        return None

# ----------------------------------------------------
# 🌟 RESPONSIVE HEADER BAR (REPLACES SIDEBAR ENTIRELY)
# ----------------------------------------------------
with st.container(border=True):
    col_nav1, col_nav2, col_nav3 = st.columns([2, 1, 1])
    
    with col_nav2:
        selected_lang = st.selectbox("🌐 Language / Idioma", ["English", "Spanish", "French"], key="app_lang")
        t = languages[selected_lang]
        
    with col_nav1:
        app_mode = st.selectbox(t["nav"], [
            "💬 Control Center", 
            "🛠️ Style Lab", 
            "📚 Data Vault",
            "🎥 Study Sheets",
            "🎨 Canvas"
        ], key="app_navigation")
        
    with col_nav3:
        text_size = st.slider("Accessibility: Text Size (px)", 12, 24, 16, key="app_font_size")

# Custom dynamic CSS styling
st.markdown(f"""
    <style>
    div[data-testid="stMetricValue"] {{
        font-size: 24px;
        font-weight: bold;
    }}
    .stButton button {{
        border-radius: 6px;
    }}
    p, span, li, div[data-testid="stMarkdownContainer"] p {{
        font-size: {text_size}px !important;
    }}
    /* Forces a highly visible custom scrollbar on all menus */
    ::-webkit-scrollbar {{
        width: 10px !important;
        height: 10px !important;

    }}
    ::-webkit-scrollbar-thumb {{
        background: #888888 !important;
        border-radius: 5px !important;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: #555555 !important;
    }}
    /* Style the selectboxes & popup dropdown options list */
    div[data-baseweb="select"] {{
        font-size: 16px !important;
        font-weight: 500 !important;
    }}
    div[role="listbox"] li {{
        font-size: 15px !important;
        padding: 10px 15px !important;
    }}
    /* Hides the "Press Enter to apply" helper text under text inputs */
    div[data-testid="InputInstructions"] {{
        display: none !important;
    }}
    /* 1. Target the main Selectbox box (the one visible on the page) */
div[data-baseweb="select"] > div {{
    background: rgba(255, 255, 255, 0.05) !important; /* Semi-transparent dark */
    color: #eef1ff !important; /* Light text */
    border: 1px solid rgba(124, 156, 255, 0.3) !important; /* Blue border */
    border-radius: 10px !important;
    background: linear-gradient(135deg,#7c9cff,#b78cff);
}}

/* 2. Target the Dropdown Menu (the part that pops open) */
div[role="listbox"] {{
    background-color: #131a33 !important; /* Dark background */
    border: 1px solid #7c9cff !important; /* Blue border */
    border-radius: 10px !important;
}}

/* 3. Target the individual Options inside the list */
div[role="option"] {{
    color: #eef1ff !important;
    padding: 10px !important;
}}

/* 4. Change the Hover color of the options */
div[role="option"]:hover {{
    background-color: #7c9cff !important; /* Highlight color */
    color: #0b1020 !important; /* Dark text when highlighted */
}}

/* 5. Change the text color of the "selected" item in the box */
div[data-baseweb="select"] div[aria-selected="true"] {{
    color: #7c9cff !important;
}}
div[data-testid="stChatInput"] {{
    border: 1px solid rgba(124, 156, 255, 0.3) !important; /* Blueish border */
    border-radius: 15px !important;
    padding: 5px !important;
    background: linear-gradient(135deg,#7c9cff,#b78cff); 
}}

/* 1. The Text Area box itself (Background and Typing Color) */
    div[data-testid="stTextArea"] textarea {{
        background-color: #1a1c2c !important;  /* Dark background color */
        color: #ffffff !important;              /* White text color when typing */
        border: 1px solid #7c9cff !important;   /* Blue border */
        border-radius: 10px !important;
        background: linear-gradient(135deg,#7c9cff,#b78cff);
    }}

    /* 2. The Placeholder text (The "Type here..." text) */
    div[data-testid="stTextArea"] textarea::placeholder {{
        color: #93a0c8 !important;             /* Muted gray placeholder */
        background: linear-gradient(135deg,#7c9cff,#b78cff); 
    }}

    /* 3. The Label text (The title sitting above the box) */
    div[data-testid="stTextArea"] label {{
        color: #7c9cff !important;             /* Blue label color */
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        background: linear-gradient(135deg,#7c9cff,#b78cff);
    }}
    
    /* 4. Focus state (When you click inside the box) */
    div[data-testid="stTextArea"] textarea:focus {{
        border: 2px solid #b78cff !important;   /* Purple border when typing */
        box-shadow: 0 0 10px rgba(183, 140, 255, 0.3) !important;
        background: linear-gradient(135deg,#7c9cff,#b78cff);
    }}

/* 2. Target the text area inside the chat input */
div[data-testid="stChatInput"] textarea {{
    background: linear-gradient(135deg,#7c9cff,#b78cff);
    color: #ffffff!important; /* Light text color */
    font-size: 16px !important;
}}

/* 3. Target the placeholder text (the "Ask me anything..." text) */
div[data-testid="stChatInput"] textarea::placeholder {{
    color: #ffffff !important;
    background: linear-gradient(135deg,#7c9cff,#b78cff);
}}

/* 4. Target the send button icon (optional) */
div[data-testid="stChatInput"] button {{
    background: linear-gradient(135deg,#7c9cff,#b78cff); !important;
    border: none !important;
    color: #ffffff !important;
}}


    </style>
""", unsafe_allow_html=True)

# Scan local machine dynamically for Ollama models
model_options = get_local_ollama_models()
vision_models = ["llama3.2-vision", "llava"]

# Global real-time connection check
try:
    ollama.list()
    ollama_online = True
except Exception:
    ollama_online = False

status_dot = "🟢" if ollama_online else "🔴"

# ----------------------------------------------------
# SECTION 1: CONTROL CENTER (CHAT)
# ----------------------------------------------------
if app_mode == "💬 Control Center":
    st.subheader(t["chat_title"])
    st.caption(t["chat_caption"])
    
    # Unified configuration card on the main page
    with st.container(border=True):
        st.markdown("⚙️ **Assistant Settings & Templates**")
        col_settings1, col_settings2, col_settings3 = st.columns(3)
        
        with col_settings1:
            selected_model = st.selectbox(f"🤖 Local LLM {status_dot}:", model_options, format_func=format_model_label, key="global_model")
            
        with col_settings2:
            personas = {
                "General Assistant": "You are a helpful, friendly, and knowledgeable AI assistant.",
                "Code Expert": "You are an expert software engineer. Provide clean, well-commented code.",
                "Creative Writer": "You are a creative writer. Help the user brainstorm ideas, stories, or copy.",
                "Language Translator": "You are a professional translator. Translate the user's text accurately and explain any cultural nuances.",
                "Math Tutor": "You are a patient math teacher. Break down complex math equations step-by-step and explain the concepts clearly.",
            }
            selected_persona = st.selectbox("Chatbot Persona:", list(personas.keys()), key="chat_persona")
            system_prompt = personas[selected_persona]
            
        with col_settings3:
            prompt_templates = {
                "No Template": "",
                "Explain Code Step-by-Step": "Explain the following code step-by-step: \n",
                "Translate to Professional English": "Translate the following text into professional, polished English: \n",
                "Explain to a 10-Year-Old": "Explain the following concept like I am a 10-year-old child: \n",
                "Solve Math Step-by-Step": "Solve the following mathematical problem step-by-step with proof: \n"
            }
            selected_template = st.selectbox("💡 Prompt Template:", list(prompt_templates.keys()))
            template_prefix = prompt_templates[selected_template]

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "current_persona" not in st.session_state:
        st.session_state.current_persona = selected_persona
    elif st.session_state.current_persona != selected_persona:
        st.session_state.messages = []
        st.session_state.current_persona = selected_persona
        st.toast(f"Switched to {selected_persona} mode!")

    col_u1, col_u2, col_u3 = st.columns([5, 1, 1])
    # with col_u2:
    #     if sr_available:
    #         if st.button("🎙️ Dictate Input", use_container_width=True):
    #             spoken_text = record_mic()
    #             if spoken_text:
    #                 st.session_state["mic_prompt"] = spoken_text
    #                 st.toast(f"Captured: '{spoken_text}'")
    with col_u3:
        if st.button(t["clear_history"], use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    for index, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and gtts_available:
                audio_col, download_col = st.columns([1, 4])
                audio_key = f"audio_{index}"
                bytes_key = f"bytes_{index}"
                
                if audio_key not in st.session_state:
                    st.session_state[audio_key], st.session_state[bytes_key] = get_tts_audio_and_bytes(message["content"])
                
                if st.session_state[audio_key]:
                    with audio_col:
                        st.audio(st.session_state[audio_key], format="audio/mp3")
                    with download_col:
                        st.download_button(
                            label="⬇️ Save Audio (MP3)",
                            data=st.session_state[bytes_key],
                            file_name=f"chat_speech_{index}.mp3",
                            mime="audio/mp3",
                            key=f"dl_{index}"
                        )

    if "user_chat_input" not in st.session_state:
        st.session_state["user_chat_input"] = ""

    if "mic_prompt" in st.session_state and st.session_state["mic_prompt"]:
        st.session_state["user_chat_input"] = st.session_state.pop("mic_prompt")

    if prompt := st.chat_input("Ask me anything...", key="user_chat_input"):
        final_prompt = template_prefix + prompt
        st.chat_message("user").markdown(final_prompt)
        st.session_state.messages.append({"role": "user", "content": final_prompt})

        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in st.session_state.messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                response = ollama.chat(
                    model=selected_model,
                    messages=api_messages,
                    stream=True
                )
                for chunk in response:
                    full_response += chunk['message']['content']
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()
            except Exception:
                st.error("Could not connect to Ollama.")

    if len(st.session_state.messages) > 0:
        st.markdown("---")
        chat_text = "\n".join([f"**{msg['role'].upper()}**: {msg['content']}" for msg in st.session_state.messages])
        st.download_button(
            label=t["export_history"],
            data=chat_text,
            file_name="chat_history.md",
            mime="text/markdown"
        )

# ----------------------------------------------------
# SECTION 2: STYLE LAB (RENOVATION)
# ----------------------------------------------------
elif app_mode == "🛠️ Style Lab":
    st.subheader(t["renov_title"])
    st.caption(t["renov_caption"])
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.container(border=True):
            st.markdown("**Design Configuration**")
            selected_model = st.selectbox(f"🤖 Local LLM {status_dot}:", model_options, format_func=format_model_label, key="style_model")
            
            room = st.selectbox("Room Type:", ["Living Room", "Kitchen", "Master Bedroom", "Bathroom", "Backyard/Patio", "Home Office"])
            style = st.selectbox("Target Style Theme:", ["Modern Minimalist", "Scandinavian", "Industrial", "Bohemian", "Rustic/Farmhouse", "Japandi"])
            room_size = st.selectbox("Dimensions Category:", ["Small (under 100 sq ft)", "Medium (100 - 250 sq ft)", "Large (over 250 sq ft)"])
            budget = st.selectbox("Budget Allowance:", ["Low (DIY & Repurposing)", "Mid-Range (Smart Upgrades)", "High-End (Full Remodel)"])
        
        with st.container(border=True):
            st.markdown("**Local Space Scan (Vision AI)**")
            uploaded_image = st.file_uploader("Upload spatial photo:", type=["png", "jpg", "jpeg"])
            if uploaded_image:
                st.image(uploaded_image, caption="Current Layout Reference", use_container_width=True)
                selected_vision_model = st.selectbox(f"🤖 Local LLM {status_dot}:", model_options, format_func=format_model_label, key="style_vision_model")
            
        generate_tips = st.button("Generate Design Report & Render", use_container_width=True, type="primary")
        
    with col2:
        if generate_tips:
            with st.container(border=True):
                st.markdown("**Conceptual 3D Blueprint Render**")
                with st.spinner("Rendering layout scheme..."):
                    try:
                        size_keyword = room_size.split(" ")[0].lower()
                        image_prompt_text = f"Interior design rendering of a {size_keyword} {room.lower()} in {style} style, professional interior design photography, clean architecture, daylight, highly detailed"
                        
                        encoded_img_prompt = urllib.parse.quote(image_prompt_text)
                        seed = random.randint(1, 999999)
                        image_url = f"https://image.pollinations.ai/prompt/{encoded_img_prompt}?width=1024&height=768&nologo=true&seed={seed}"
                        
                        st.image(image_url, caption=f"Generated Reference: {style} {room}", use_container_width=True)
                        
                        image_data = requests.get(image_url).content
                        st.download_button(
                            label="💾 Download Generated Rendering",
                            data=image_data,
                            file_name=f"{style.replace(' ', '_')}_{room.lower()}_concept.jpg",
                            mime="image/jpeg"
                        )
                    except Exception as e:
                        st.error(f"Image generation failed: {e}")
            
            with st.container(border=True):
                st.markdown("**Technical Renovation Advice Draft**")
                with st.spinner("Compiling structural specifications..."):
                    try:
                        if uploaded_image:
                            img_bytes = uploaded_image.getvalue()
                            prompt = (
                                f"Analyze this image of a room. Provide renovation advice to transform it "
                                f"into a {style} style {room_size.lower()} {room} on a {budget} budget. "
                                f"Be descriptive and practical."
                            )
                            response = ollama.generate(model=selected_vision_model, prompt=prompt, images=[img_bytes])
                        else:
                            prompt = (
                                f"You are a professional interior designer and contractor. "
                                f"Create a curated, practical renovation guide for a {room_size.lower()} {room} in the '{style}' style. "
                                f"The project has a {budget} budget. "
                                f"Include:\n"
                                f"1. 4-5 highly actionable renovation and decorating tips.\n"
                                f"2. A recommended color palette with paint name ideas.\n"
                                f"3. High-impact elements to focus on to get the look.\n"
                                f"4. Budget-friendly alternatives or smart material suggestions."
                            )
                            response = ollama.generate(model=selected_model, prompt=prompt)
                        
                        guide_text = response['response']
                        st.success("Analysis Complete!")
                        st.markdown(guide_text)
                        st.session_state["last_guide"] = guide_text
                    except Exception as e:
                        st.error(f"Ollama execution failed: {e}")

        # Persistent utilities for generated guide
        if "last_guide" in st.session_state:
            with st.container(border=True):
                st.markdown("**Utilities & Visualizations**")
                col_b1, col_b2, col_b3 = st.columns([1, 1, 2])
                with col_b1:
                    if gtts_available and st.button("🔊 Read Aloud"):
                        audio_fp, audio_bytes = get_tts_audio_and_bytes(st.session_state["last_guide"])
                        if audio_fp:
                            st.audio(audio_fp, format="audio/mp3")
                            st.download_button(label="⬇️ Save Audio File (MP3)", data=audio_bytes, file_name="renovation_tips.mp3", mime="audio/mp3")
                with col_b2:
                    st.download_button(
                        label="📥 Export Blueprint (Markdown)",
                        data=st.session_state["last_guide"],
                        file_name="renovation_guide.md",
                        mime="text/markdown"
                    )
                with col_b3:
                    # Concept Mermaid flowchart
                    if st.button("📊 Create Mind-Map Diagram"):
                        with st.spinner("Compiling structural flowchart..."):
                            m_prompt = (
                                        f"Based on this text, compile a Mermaid.js flowchart. "
                                        f"STRICT RULE: Respond ONLY with the code. Do NOT include 'Here is your diagram' "
                                        f"or any other conversational text. Start directly with 'graph TD'.\n\n"
                                        f"Text:\n{st.session_state['last_guide']}"
                                    )
                            try:
                                m_res = ollama.generate(model=selected_model, prompt=m_prompt)
                                cleaned_chart = clean_mermaid(m_res['response'])
                                st.markdown(f"```mermaid\n{cleaned_chart}\n```")
                            except Exception as e:
                                st.error("Chart rendering failed.")

# ----------------------------------------------------
# SECTION 3: DATA VAULT (DOCUMENT QA - STATE MANAGED)
# ----------------------------------------------------
elif app_mode == "📚 Data Vault":
    st.subheader(t["doc_title"])
    
    # Initialize Document State Management to prevent infinite re-parsing
    if "doc_text" not in st.session_state:
        st.session_state["doc_text"] = ""
    if "processed_filename" not in st.session_state:
        st.session_state["processed_filename"] = ""
    if "doc_qa_answer" not in st.session_state:
        st.session_state["doc_qa_answer"] = ""

    # ONLY SHOW THE CAPTION BEFORE SUBMITTING THE FILE
    if not st.session_state["doc_text"]:
        st.caption(t["doc_caption"])

    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.container(border=True):
            st.markdown("**Document or WAV Audio Source**")
            selected_model = st.selectbox(f"🤖 Local LLM {status_dot}:", model_options, format_func=format_model_label, key="vault_model")
            
            doc_file = st.file_uploader("Upload Document File (.txt, .pdf, .wav):", type=["txt", "pdf", "wav"])
            
            # Reset cached text if a new file is uploaded
            if doc_file and st.session_state["processed_filename"] != doc_file.name:
                st.session_state["doc_text"] = ""
                st.session_state["doc_qa_answer"] = ""
                st.session_state["processed_filename"] = ""

            # Explicit Submit Button to process the document
            if doc_file and not st.session_state["doc_text"]:
                if st.button("📁 Submit & Analyze File", type="primary", use_container_width=True):
                    file_extension = doc_file.name.split(".")[-1].lower()
                    with st.spinner("Processing file contents..."):
                        if file_extension == "txt":
                            st.session_state["doc_text"] = doc_file.read().decode("utf-8")
                        elif file_extension == "pdf":
                            st.session_state["doc_text"] = parse_pdf(doc_file)
                        elif file_extension == "wav":
                            if not sr_available:
                                st.error("Speech Recognition toolkit not installed.")
                            else:
                                r = sr.Recognizer()
                                try:
                                    with sr.AudioFile(doc_file) as source:
                                        audio_data = r.record(source)
                                        st.session_state["doc_text"] = r.recognize_google(audio_data)
                                except Exception as e:
                                    st.error(f"Failed to parse audio WAV: {e}")
                        
                        st.session_state["processed_filename"] = doc_file.name
                        st.rerun()

            # Render document metrics once processed
            if st.session_state["doc_text"]:
                doc_text = st.session_state["doc_text"]
                words, r_time, chars = get_text_metrics(doc_text)
                st.markdown("**Document Metrics**")
                m_col1, m_col2 = st.columns(2)
                with m_col1:
                    st.metric("Total Words", f"{words:,}")
                with m_col2:
                    st.metric("Est. Read Time", f"{r_time} min")
    
    with col2:
        if st.session_state["doc_text"]:
            doc_text = st.session_state["doc_text"]
            
            with st.container(border=True):
                st.markdown("**Source Preview**")
                st.text_area("Live Preview (First 2000 Characters)", doc_text[:2000] + "\n...", height=150, disabled=True)
            
            with st.container(border=True):
                st.markdown("**Query Processor**")
                user_query = st.text_input("Ask a question about this content:")
                
                if st.button("Extract Answer", type="primary") and user_query:
                    with st.spinner("Interrogating context..."):
                        prompt = (
                            f"Use the following document text as your context to answer this query: '{user_query}'\n\n"
                            f"Document text:\n{doc_text[:6000]}"
                        )
                        try:
                            response = ollama.generate(model=selected_model, prompt=prompt)
                            st.session_state["doc_qa_answer"] = response['response']
                        except Exception as e:
                            st.error(f"Execution failed: {e}")

            # Render QA answer persistently
            if st.session_state["doc_qa_answer"]:
                st.markdown("---")
                st.write("**Answer Output:**")
                st.write(st.session_state["doc_qa_answer"])
                st.download_button(
                    label="📥 Export Answer as TXT",
                    data=st.session_state["doc_qa_answer"],
                    file_name="qa_answer.txt",
                    mime="text/plain"
                )

# ----------------------------------------------------
# SECTION 4: STUDY SHEETS (YOUTUBE SUMMARIZER - CACHED)
# ----------------------------------------------------
elif app_mode == "🎥 Study Sheets":
    st.subheader(t["yt_title"])
    st.caption(t["yt_caption"])

    # Initialize State Caches to prevent widget disappearing errors
    if "yt_summary" not in st.session_state:
        st.session_state["yt_summary"] = ""
    if "yt_mindmap" not in st.session_state:
        st.session_state["yt_mindmap"] = ""
    if "yt_qa_answer" not in st.session_state:
        st.session_state["yt_qa_answer"] = ""
    if "yt_last_video_id" not in st.session_state:
        st.session_state["yt_last_video_id"] = ""
    if "current_transcript" not in st.session_state:
        st.session_state["current_transcript"] = ""

    if not youtube_available:
        st.error("Missing dependency: 'youtube-transcript-api'.")
    else:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            with st.container(border=True):
                st.markdown("**Source Video**")
                selected_model = st.selectbox(f"🤖 Local LLM {status_dot}:", model_options, format_func=format_model_label, key="study_model")
                
                yt_url = st.text_input("Enter YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")
                video_id = get_yt_video_id(yt_url) if yt_url else None
                
                if video_id:
                    if video_id != st.session_state["yt_last_video_id"]:
                        st.session_state["current_transcript"] = ""
                        st.session_state["yt_summary"] = ""
                        st.session_state["yt_mindmap"] = ""
                        st.session_state["yt_qa_answer"] = ""
                        st.session_state["yt_last_video_id"] = video_id
                    
                    # Explicit Submit Button to process video transcript
                    if not st.session_state["current_transcript"]:
                        if st.button("📥 Submit & Parse Video", type="primary", use_container_width=True):
                            with st.spinner("Extracting captions..."):
                                try:
                                    transcript_text = fetch_youtube_transcript(video_id)
                                    st.session_state["current_transcript"] = transcript_text
                                    st.session_state["yt_last_video_id"] = video_id
                                    st.success("Subtitles parsed.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to fetch subtitles: {e}")
                                    st.session_state["current_transcript"] = ""
                else:
                    if yt_url:
                        st.error("Invalid YouTube URL structure.")

                # Display metrics if transcript is active
                if st.session_state["current_transcript"]:
                    words, r_time, _ = get_text_metrics(st.session_state["current_transcript"])
                    st.markdown("**Transcript Metrics**")
                    m_col1, m_col2 = st.columns(2)
                    with m_col1:
                        st.metric("Transcript Words", f"{words:,}")
                    with m_col2:
                        st.metric("Est. Video Duration", f"{r_time} min")

        with col2:
            if yt_url and video_id and st.session_state.get("current_transcript"):
                transcript_text = st.session_state["current_transcript"]
                
                with st.container(border=True):
                    st.markdown("**Subtitle Preview**")
                    st.text_area("Captions preview", transcript_text[:1500] + "\n...", height=120, disabled=True)
                
                with st.container(border=True):
                    st.markdown("**Processing Suite**")
                    yt_action = st.radio("Choose Action Mode:", ["Generate Summary", "Ask Questions"])
                    
                    if yt_action == "Generate Summary":
                        summary_style = st.selectbox("Format style:", ["Bullet Points", "Paragraph Executive Summary", "Actionable Takeaways"])
                        
                        col_y1, col_y2 = st.columns(2)
                        with col_y1:
                            summarize_btn = st.button("Generate Summary Report", type="primary", use_container_width=True)
                        with col_y2:
                            visualize_btn = st.button("📊 Generate Concept Mind-Map", use_container_width=True)
                            
                        if summarize_btn:
                            with st.spinner("Synthesizing script details..."):
                                prompt = (
                                    f"Summarize the following YouTube video transcript in the format of '{summary_style}'. "
                                    f"Provide a clear and accurate structure.\n\n"
                                    f"Transcript:\n{transcript_text[:6000]}"
                                )
                                try:
                                    response = ollama.generate(model=selected_model, prompt=prompt)
                                    st.session_state["yt_summary"] = response['response']
                                    st.session_state["yt_mindmap"] = ""  # Clear chart
                                except Exception as e:
                                    st.error(f"Ollama call failed: {e}")
                                    
                        if visualize_btn:
                            with st.spinner("Synthesizing concept roadmap..."):
                                m_prompt = (
                                            f"Based on this video transcript, draft a Mermaid.js mind-map. "
                                            f"STRICT RULE: Respond ONLY with the code. Do NOT include any intro or outro text. "
                                            f"Start directly with 'graph TD'.\n\n"
                                            f"Transcript:\n{transcript_text[:6000]}"
                                        )
                                try:
                                    m_res = ollama.generate(model=selected_model, prompt=m_prompt)
                                    st.session_state["yt_mindmap"] = clean_mermaid(m_res['response'])
                                    st.session_state["yt_summary"] = ""  # Clear summary
                                except Exception as e:
                                    st.error("Roadmap compilation failed.")
                        
                        # Persist Summary
                        if st.session_state["yt_summary"]:
                            st.write("---")
                            st.write("### Video Summary Output")
                            st.write(st.session_state["yt_summary"])
                            
                            st.download_button(
                                label="📥 Export Summary (Markdown)",
                                data=st.session_state["yt_summary"],
                                file_name=f"yt_{video_id}_summary.md",
                                mime="text/markdown"
                            )
                        
                        # Persist Mindmap
                        if st.session_state["yt_mindmap"]:
                            st.write("---")
                            st.write("### Video Concept Mind-Map")
                            st.markdown(f"```mermaid\n{st.session_state['yt_mindmap']}\n```")
                                    
                    elif yt_action == "Ask Questions":
                        user_q = st.text_input("Ask a question about this video:")
                        if st.button("Submit Question", type="primary") and user_q:
                            with st.spinner("Searching transcript context..."):
                                prompt = (
                                    f"Based strictly on this video transcript, answer the following question: '{user_q}'\n\n"
                                    f"Transcript:\n{transcript_text[:6000]}"
                                )
                                try:
                                    response = ollama.generate(model=selected_model, prompt=prompt)
                                    st.session_state["yt_qa_answer"] = response['response']
                                except Exception as e:
                                    st.error(f"Failed to query transcript: {e}")
                        
                        # Persist QA answer
                        if st.session_state["yt_qa_answer"]:
                            st.write("---")
                            st.write("### Answer Output")
                            st.write(st.session_state["yt_qa_answer"])
                            st.download_button(
                                label="📥 Export Answer as TXT",
                                data=st.session_state["yt_qa_answer"],
                                file_name="yt_answer.txt",
                                mime="text/plain"
                            )

# ----------------------------------------------------
# SECTION 5: CANVAS (IMAGE GENERATOR)
# ----------------------------------------------------
elif app_mode == "🎨 Canvas":
    st.subheader(t["img_title"])
    st.caption("A completely free rendering studio that constructs images on-demand with zero API requirements.")
    
    img_col1, img_col2 = st.columns([1, 1])
    
    with img_col1:
        with st.container(border=True):
            st.markdown(f"**{t['img_col']}**")
            base_prompt = st.text_input("Describe your idea:", placeholder="e.g., A bright Scandinavian kitchen with light wood cabinets")
            
            aspect_ratio = st.selectbox("Aspect Ratio Layout:", ["Square (1:1)", "Landscape (16:9)", "Portrait (9:16)"])
            if aspect_ratio == "Square (1:1)":
                width, height = 1024, 1024
            elif aspect_ratio == "Landscape (16:9)":
                width, height = 1280, 720
            else:
                width, height = 720, 1280
            
            preset_style = st.selectbox(t["img_pres"], [
                "Realistic Photo", "Cinematic Render", "Watercolor Illustration", 
                "Retro Pixel Art", "Vector Graphic", "Oil Painting"
            ])
            
            details = st.multiselect(
                "Visual enhancements:",
                ["Cinematic lighting", "Highly detailed 8k", "Modern interior photography", "Cozy atmosphere", "Sunset warm light"]
            )
        
        style_prompts = {
            "Realistic Photo": "professional photorealistic interior design photography, daylight, sharp focus",
            "Cinematic Render": "cinematic lighting, dramatic depth of field, Octane render vibe, volumetric shadows",
            "Watercolor Illustration": "soft pastel watercolor sketch style, fine artistic borders, architectural illustration",
            "Retro Pixel Art": "retro classic 16-bit pixel art style, isometric view, gaming graphics",
            "Vector Graphic": "flat minimalist vector design style, clean solid shapes, modern graphic poster aesthetic",
            "Oil Painting": "textured impasto oil painting on canvas, classical dramatic fine art brush strokes"
        }
        
        final_prompt_parts = [base_prompt, style_prompts[preset_style]] + details
        full_prompt = ", ".join([p for p in final_prompt_parts if p.strip() != ""])
        
        if base_prompt:
            st.info(f"**Final Render Prompt:** {full_prompt}")
            
        generate_image = st.button(t["img_gen"], type="primary", use_container_width=True)
        
    with img_col2:
        if generate_image and base_prompt:
            with st.container(border=True):
                st.markdown("**Render Preview Canvas**")
                with st.spinner("Painting concepts visually..."):
                    try:
                        encoded_prompt = urllib.parse.quote(full_prompt)
                        seed = random.randint(1, 999999)
                        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={seed}"
                        
                        st.image(image_url, caption=f"Aspect: {aspect_ratio} | Preset: {preset_style}", use_container_width=True)
                        
                        image_data = requests.get(image_url).content
                        st.download_button(
                            label="Download Concept Image",
                            data=image_data,
                            file_name="concept_design_render.jpg",
                            mime="image/jpeg",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Image generation failed: {e}")
        elif generate_image and not base_prompt:
            st.warning("Please describe your conceptual design in the input box first.")
