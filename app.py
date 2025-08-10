import os, json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Setup ----------
st.set_page_config(
    page_title="JWB Dining Assistant", 
    page_icon="🤖", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------- Load background image first ----------
try:
    with open("134-01.svg", "r", encoding="utf-8") as f:
        background_svg = f.read()
    # Convert to base64 for embedding
    import base64
    background_b64 = base64.b64encode(background_svg.encode('utf-8')).decode('utf-8')
    background_url = f"data:image/svg+xml;base64,{background_b64}"
    print(f"Background loaded successfully, URL length: {len(background_url)}")
except Exception as e:
    background_url = ""
    print(f"Failed to load background: {e}")

# ---------- Load Jimmy8 icon for chat messages ----------
try:
    with open("jimmy8-01.svg", "r", encoding="utf-8") as f:
        jimmy_svg = f.read()
    # Clean up SVG content (remove XML declaration and style tags, convert CSS classes to inline styles)
    import re
    jimmy_svg = re.sub(r'<\?xml[^>]*\?>', '', jimmy_svg)
    jimmy_svg = re.sub(r'<style[^>]*>.*?</style>', '', jimmy_svg, flags=re.DOTALL)
    jimmy_svg = re.sub(r'class="([^"]*)"', 'style="fill: white; width: 24px; height: 24px;"', jimmy_svg)
    jimmy_svg = re.sub(r'\s+', ' ', jimmy_svg).strip()
    print("Jimmy8 icon loaded successfully")
except Exception as e:
    jimmy_svg = "🍽️"  # Fallback emoji
    print(f"Failed to load Jimmy8 icon: {e}")

# ---------- Custom CSS Styling ----------
st.markdown(f"""
<style>
    /* Full screen background with your image */
    .stApp, .main, body, html {{
        background-image: url('{background_url}') !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    }}
    
    /* Main app background with gradient overlay */
    .main > div {{
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.4) 0%, rgba(118, 75, 162, 0.4) 100%) !important;
        min-height: 100vh;
        position: relative;
    }}
    
    /* Also apply to the root container */
    [data-testid="stAppViewContainer"] {{
        background-image: url('{background_url}') !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
    }}
    
    /* Hide Streamlit header and footer */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Hide any debug panels */
    .stAlert, .stException {{
        display: none !important;
    }}
    
    /* Ensure content is above background */
    .stApp > div {{
        position: relative;
        z-index: 10;
    }}
    
    /* Chat container styling */
    .stChatMessage {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 20px !important;
        margin: 15px 0 !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        animation: slideUp 0.3s ease-out !important;
    }}
    
    /* User message styling */
    .stChatMessage[data-testid="user-message"] {{
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.25), rgba(255, 255, 255, 0.15)) !important;
        margin-left: 15% !important;
        margin-right: 5% !important;
    }}
    
    /* Assistant message styling */
    .stChatMessage[data-testid="assistant-message"] {{
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1)) !important;
        margin-left: 5% !important;
        margin-right: 15% !important;
    }}
    

    
    /* User message styling */
    .stChatMessage[data-testid="user-message"] {{
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.25), rgba(255, 255, 255, 0.15)) !important;
        margin-left: 15% !important;
        margin-right: 5% !important;
    }}
    
    /* Assistant message styling */
    .stChatMessage[data-testid="assistant-message"] {{
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1)) !important;
        margin-left: 5% !important;
        margin-right: 15% !important;
    }}
    
    /* Chat message animation */
    @keyframes slideUp {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    /* Chat input styling */
    .stChatInput > div > div > div > div {{
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 25px;
        backdrop-filter: blur(10px);
    }}
    
    /* App title styling */
    .main-title {{
        text-align: center;
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 40px 0 20px 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        position: relative;
        z-index: 999;
    }}
    
    .sub-title {{
        text-align: center;
        color: rgba(255, 255, 255, 0.8);
        font-size: 1.1rem;
        margin-bottom: 30px;
        font-weight: 300;
    }}
    
    /* Bot avatar styling */
    .bot-avatar {{
        width: 350px;
        height: 350px;
        background: transparent;
        border-radius: 0;
        margin: 0 auto 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
        border: none;
        z-index: 1000;
        position: relative;
    }}
    
    .logo-img {{
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    
    .logo-img svg {{
        width: 100%;
        height: 100%;
        max-width: 320px;
        max-height: 320px;
        object-fit: contain;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
    }}
    
    /* Welcome message styling */
    .welcome-card {{
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 25px;
        margin: 20px 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
        color: white;
    }}
    
    /* Quick action buttons */
    .quick-actions {{
        display: flex;
        gap: 10px;
        justify-content: center;
        margin: 20px 0;
        flex-wrap: wrap;
    }}
    
    .quick-btn {{
        background: rgba(255, 255, 255, 0.15);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 20px;
        padding: 8px 16px;
        font-size: 0.9rem;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }}
    
    .quick-btn:hover {{
        background: rgba(255, 255, 255, 0.25);
        transform: translateY(-2px);
    }}
    
    /* Spinner styling */
    .stSpinner > div > div {{
        border-top-color: white !important;
    }}
    
    /* Text color for better contrast */
    .stMarkdown, .stText {{
        color: white;
    }}
    
    /* Fix text formatting in chat messages */
    .stChatMessage .stMarkdown {{
        word-wrap: break-word;
        overflow-wrap: break-word;
        white-space: normal;
        max-width: 100%;
    }}
    
    .stChatMessage .stMarkdown p {{
        margin: 0.5rem 0;
        line-height: 1.4;
        font-size: 0.95rem;
    }}
    
    .stChatMessage .stMarkdown em {{
        font-style: normal;
        font-weight: 500;
    }}
    
    /* Debug expander styling */
    .streamlit-expanderHeader {{
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }}
    
    /* Button styling */
    .stButton > button {{
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1)) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 20px !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
        font-weight: 500 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }}
    
    .stButton > button:hover {{
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.2)) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
    }}
    
    .stButton > button:active {{
        transform: translateY(0) !important;
    }}
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {{
        .main-title {{
            font-size: 2rem !important;
        }}
        
        .stChatMessage[data-testid="user-message"] {{
            margin-left: 5% !important;
        }}
        
        .stChatMessage[data-testid="assistant-message"] {{
            margin-right: 5% !important;
        }}
        
        .bot-avatar {{
            width: 280px !important;
            height: 280px !important;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# Load API key from Streamlit secrets (for cloud) or environment (for local)
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("Missing OPENAI_API_KEY in secrets or .env file")
    st.stop()

client = OpenAI(api_key=api_key)



@st.cache_data
def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

menu = load_json("grouped_menu.json")
wine_list = load_json("wine_list.json")
bevs = load_json("beverage_menu.json")
policies = load_json("restaurant_policies.json")

# Use your own file if present, otherwise a brand‑aligned default
try:
    with open("prompt_template.txt", "r", encoding="utf-8") as f:
        base_system = f.read().strip()
except Exception:
    base_system = (
        "You are the JWB Grill dining assistant at Margaritaville Beach Resort Fort Myers Beach. "
        "Tone: elegant, warm, concise, refined—coastal fine dining with a laid‑back soul. "
        "Key pillars: Coastal fine dining with a laid‑back soul. Where Gulf flavors meet island sophistication. "
        "Savor the moment—sunset, seafood, and signature steaks. "
        "Style rules: No slang or beach‑bar clichés. Keep dish names exact from JSON context. "
        "Short, sensory sentences. Respect allergies strictly."
    )

def system_prompt():
    return base_system + (
        "\n\nReply rules:\n"
        "- Infer preferences and constraints from the conversation; ask 1 brief clarifying question only if needed.\n"
        "- Provide 1–3 tailored dish suggestions using exact names from the menu JSON; include prices if available.\n"
        "- Add a thoughtful pairing (wine/cocktail/NA) when suitable, referencing the wine/beverage JSON.\n"
        "- If user mentions allergies (e.g., shellfish, dairy, gluten, nuts), strictly avoid conflicting items and state safe alternatives.\n"
        "- For policy questions (reservations, dress code, corkage, seating), use the exact information from the policies JSON.\n"
        "- Keep paragraphs short and polished; end with a gentle checkback question.\n"
        "- Use proper formatting: NO italics, keep text simple and readable, ensure proper line breaks."
    )

def build_context():
    return {
        "menu": menu,
        "wine_list": wine_list,
        "beverages": bevs,
        "policies": policies
    }

# ---------- Chat state ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- Modern Header ----------
# Load and display the Ask Jimmy logo
try:
    with open("JWB8.svg", "r", encoding="utf-8") as f:
        svg_content = f.read()
    
    # Clean the SVG content to prevent rendering issues
    svg_content = svg_content.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
    
    # Convert CSS classes to inline styles to prevent display issues
    import re
    
    # Extract style definitions and convert to inline styles
    style_definitions = {
        'cls-1': 'fill: #5f81aa',
        'cls-2': 'fill: #6f738d', 
        'cls-3': 'fill: #fff',
        'cls-4': 'fill: #54709c',
        'cls-5': 'fill: #cdceca',
        'cls-6': 'fill: #a2a4a2',
        'cls-7': 'fill: #233866'
    }
    
    # Remove the <style> section
    svg_content = re.sub(r'<style>.*?</style>', '', svg_content, flags=re.DOTALL)
    
    # Replace class references with inline styles
    for class_name, style_value in style_definitions.items():
        svg_content = re.sub(rf'class="{class_name}"', f'style="{style_value}"', svg_content)
    
    # Clean up any extra whitespace
    svg_content = re.sub(r'\s+', ' ', svg_content).strip()
    
    st.markdown(f"""
    <div class="bot-avatar">
        <div class="logo-img">{svg_content}</div>
    </div>
    <h1 class="main-title">Ask Jimmy</h1>
    <p class="sub-title">Where Gulf flavors meet island sophistication</p>
    """, unsafe_allow_html=True)
except Exception as e:
    # Show error details
    st.error(f"❌ Failed to load JWB8.svg: {str(e)}")
    
    # Fallback to simple text if SVG fails to load
    st.markdown("""
    <div class="bot-avatar">
        <div style="color: white; font-weight: bold; text-align: center; font-size: 1.2rem;">
            ASK JIMMY
        </div>
    </div>
    <h1 class="main-title">Ask Jimmy</h1>
    <p class="sub-title">Where Gulf flavors meet island sophistication</p>
    """, unsafe_allow_html=True)

# ---------- Welcome Message & Quick Actions ----------
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-card">
        <h3>Hello, I'm your JWB Assistant! 👋</h3>
        <p>I'm here to help you discover the perfect dishes and pairings from our coastal fine dining menu. 
        Tell me what you're craving, or try one of these popular options:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🦞 Seafood & Wine", key="seafood", help="Seafood recommendations with wine pairings"):
            st.session_state.messages.append({"role": "user", "content": "I love seafood and would like a wine pairing recommendation."})
            st.rerun()
    
    with col2:
        if st.button("🥩 Steak & Red", key="steak", help="Premium steaks with red wine"):
            st.session_state.messages.append({"role": "user", "content": "I want a great steak with a bold red wine."})
            st.rerun()
    
    with col3:
        if st.button("🥗 Light & Fresh", key="light", help="Light, healthy options"):
            st.session_state.messages.append({"role": "user", "content": "I'm looking for something light and fresh."})
            st.rerun()
    
    with col4:
        if st.button("💝 Date Night", key="romantic", help="Romantic dinner suggestions"):
            st.session_state.messages.append({"role": "user", "content": "It's date night - what's your best romantic pairing?"})
            st.rerun()

# ---------- Chat input ----------
user_text = st.chat_input("💬 Tell me what you're in the mood for…")
if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    
    # Special easter egg for Brandon's mom
    if "brandon" in user_text.lower() and "mom" in user_text.lower():
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "💝 **Amy Andersen is the best mom!** She's absolutely amazing - kind, loving, and has the biggest heart. She's the kind of mom who makes everyone feel like family, always there with a warm smile and endless love. Brandon is so lucky to have such an incredible mom! 🌟"
        })
        st.rerun()

# ---------- Render history ----------
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="stChatMessage" data-testid="user-message">
            <div style="display: flex; align-items: center; gap: 10px; padding: 15px;">
                <div style="background: #667eea; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                    👤
                </div>
                <div style="flex: 1;">
                    {msg["content"]}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:  # assistant message
        st.markdown(f"""
        <div class="stChatMessage" data-testid="assistant-message">
            <div style="display: flex; align-items: center; gap: 10px; padding: 15px;">
                <div style="background: #667eea; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                    <div style="display: flex; align-items: center; justify-content: center; width: 100%; height: 100%;">
                        {jimmy_svg}
                    </div>
                </div>
                <div style="flex: 1;">
                    {msg["content"]}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ---------- Generate reply ----------
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.spinner("Curating your table…"):
            context_blob = json.dumps(build_context(), ensure_ascii=False)
            messages = [
                {"role": "system", "content": system_prompt()},
                {"role": "system", "content": f"CONTEXT:\n{context_blob}"},
            ] + st.session_state.messages

            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7
                )
                reply = resp.choices[0].message.content
            except Exception as e:
                reply = f"Sorry—something went wrong: {e}"

            # Display the AI response with the Jimmy8 icon
            st.markdown(f"""
            <div class="stChatMessage" data-testid="assistant-message">
                <div style="display: flex; align-items: center; gap: 10px; padding: 15px;">
                    <div style="background: #667eea; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                        <div style="display: flex; align-items: center; justify-content: center; width: 100%; height: 100%;">
                            {jimmy_svg}
                        </div>
                    </div>
                    <div style="flex: 1;">
                        {reply}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": reply})

# Debug data removed for production
