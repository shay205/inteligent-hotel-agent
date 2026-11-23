"""Luxury hotel visual system shared by all Streamlit views."""
import streamlit as st

CSS = """
<style>
:root { --cream:#F7F2EA; --beige:#E8DDCC; --gold:#B9955B; --coffee:#3A2921; --charcoal:#24211F; --brown:#5E493B; }
html, body, [class*="css"] { font-family:"DM Sans","Segoe UI",system-ui,sans-serif; }
h1,h2,h3 { font-family:"Cormorant Garamond",Georgia,"Times New Roman",serif; letter-spacing:-.02em; }
.block-container { max-width:1180px; padding-top:2.1rem; padding-bottom:4rem; animation:pageIn .45s ease-out; }
@keyframes pageIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }
section[data-testid="stSidebar"] { background:#2F2823; border-right:1px solid rgba(185,149,91,.22); }
section[data-testid="stSidebar"] * { color:#F5EFE6 !important; }
.brand-mark { display:flex; align-items:center; gap:12px; padding:18px 4px 24px; }
.brand-monogram { width:46px; height:46px; display:grid; place-items:center; border:1px solid #B9955B;
                  border-radius:50%; font-family:Georgia,serif; color:#D2B98B !important; letter-spacing:.08em; }
.brand-name { font-family:Georgia,serif; font-size:1.08rem; line-height:1.1; }
.brand-caption { font-size:.68rem; text-transform:uppercase; letter-spacing:.18em; color:#CBBFAE !important; margin-top:5px; }
div[data-testid="stSidebarNav"] { display:none; }
section[data-testid="stSidebar"] div[role="radiogroup"] label { border-radius:8px; padding:5px 8px; transition:.2s ease; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background:rgba(185,149,91,.13); transform:translateX(3px); }
.sidebar-footer { margin:28px 4px 12px; font-family:Georgia,serif; font-style:italic;
                  color:#CDBA9E !important; font-size:.85rem; }
.luxury-hero { min-height:620px; border-radius:22px; background-size:cover; background-position:center 58%;
               display:flex; align-items:center; box-shadow:0 24px 60px rgba(58,41,33,.18); overflow:hidden;
               margin-bottom:34px; image-rendering:auto; }
.luxury-hero-content { max-width:610px; margin-left:7%; color:#FFF; }
.hero-kicker,.eyebrow { text-transform:uppercase; letter-spacing:.22em; font-size:.74rem; font-weight:700; }
.luxury-hero h1 { color:#FFF; font-size:clamp(3.4rem,7vw,6.5rem); line-height:.88; margin:.2em 0 .28em; }
.hero-copy { max-width:520px; font-size:1.12rem; line-height:1.7; color:#F3EEE6; }
.hero-actions { display:flex; gap:10px; margin-top:24px; }
.hero-actions span { padding:13px 20px; border-radius:999px; font-weight:700; }
.hero-primary { background:#B9955B; color:#fff; }
.hero-secondary { border:1px solid rgba(255,255,255,.55); backdrop-filter:blur(8px); }
.section-heading { text-align:center; margin:54px 0 24px; }
.section-heading p { color:#927153; text-transform:uppercase; letter-spacing:.18em; font-size:.72rem; font-weight:700; }
.section-heading h2 { font-size:3rem; margin:.15em 0; color:#F5EFE6; }
.room-feature-card { background:#2A2521; border:1px solid #51483F; border-radius:14px; overflow:hidden;
                     box-shadow:0 14px 40px rgba(0,0,0,.18); transition:.35s ease; height:100%; }
.room-feature-card:hover { transform:translateY(-7px); border-color:#C5A875; box-shadow:0 22px 52px rgba(0,0,0,.28); }
.room-feature-image { height:230px; background-size:cover; background-position:center; transition:.5s ease; }
.room-feature-card:hover .room-feature-image { transform:scale(1.025); }
.room-feature-body { padding:18px 20px 20px; }
.room-feature-body p { color:#C5A875; text-transform:uppercase; letter-spacing:.08em; font-size:.68rem; }
.room-feature-body h3 { color:#F5EFE6; font-size:1.7rem; margin:.35em 0 .8em; }
.room-feature-meta { display:flex; justify-content:space-between; align-items:end; color:#D1C5B7; font-size:.82rem; }
.room-feature-meta strong { color:#F5EFE6; font-size:1.12rem; }
.room-feature-meta small { color:#BFAF9E; font-weight:400; }
.amenity-heading { margin-top:70px; }
.amenity-card { min-height:280px; border:1px solid #51483F; background-size:cover;
                background-position:center; border-radius:12px; overflow:hidden; position:relative;
                transition:.35s ease; box-shadow:0 14px 36px rgba(0,0,0,.18); }
.amenity-card:hover { border-color:#C5A875; transform:translateY(-5px); background-size:cover;
                      box-shadow:0 20px 44px rgba(0,0,0,.28); }
.amenity-card-content { position:absolute; left:20px; right:20px; bottom:18px; color:#FFF; }
.amenity-card-content span { display:block; text-transform:uppercase; letter-spacing:.14em;
                             font-size:.62rem; color:#E7D5B5; margin-bottom:6px; }
.amenity-icon { display:grid; place-items:center; width:44px; height:44px; border-radius:50%; background:#3A322A;
                color:#C5A875; }
.amenity-card h3 { color:#F5EFE6; font-size:1.25rem; margin:14px 0 8px; }
.amenity-card p { color:#C9BEAF; font-size:.86rem; line-height:1.55; }
.guest-promise { margin:72px 0 32px; padding:70px 8%; text-align:center; color:#F7F2EA;
                 background:linear-gradient(135deg,#3A2921,#604938); border-radius:18px; }
.guest-promise h2 { font-size:3rem; max-width:700px; margin:.25em auto; }
.guest-promise > p:last-child { max-width:680px; margin:auto; color:#DDD1C3; line-height:1.8; }
.contact-card { background:#2D2823; border:1px solid #51483F; border-radius:14px; padding:28px 32px; }
.contact-card h2 { margin:.25em 0; color:#F5EFE6; }
.contact-card p { color:#C9BEAF; }
.luxury-footer { margin-top:56px; padding:26px 0 12px; border-top:1px solid #DED4C7;
                 display:flex; justify-content:space-between; gap:18px; color:#C9BEAF; font-size:.82rem; }
.luxury-footer strong { font-family:Georgia,serif; color:#F5EFE6; }
.page-hero { padding:34px 38px; margin-bottom:22px; background:linear-gradient(135deg,#3A2921,#604938);
             border-radius:16px; color:#F7F2EA; border-bottom:4px solid #B9955B; }
.page-hero h1 { color:#FFF; font-size:3.2rem; margin:.15em 0; }
.page-hero > p:last-child { color:#D8CCBE; max-width:680px; }
.metric { width:100%; min-height:122px; box-sizing:border-box; background:#4A3428;
          border:1px solid #C5A875; border-top:4px solid #E0BF7A; border-radius:14px;
          padding:18px 16px; margin:0 0 18px; box-shadow:0 14px 34px rgba(0,0,0,.3); }
.metric .value { font-family:Georgia,serif; font-size:2.35rem; font-weight:700; color:#FFE2A8 !important;
                 line-height:1.1; margin-top:8px; }
.metric .label { color:#FFF8EE !important; font-size:.75rem; text-transform:uppercase; letter-spacing:.08em;
                 font-weight:700; line-height:1.25; }
.metric .caption { color:#E6D2B9 !important; font-size:.73rem; margin-top:7px; line-height:1.3; }
.member-list { max-width:760px; background:#2A2521; border:1px solid #51483F; border-radius:14px;
               overflow:hidden; box-shadow:0 12px 32px rgba(0,0,0,.14); margin-bottom:30px; }
.member-row { display:flex; align-items:center; gap:14px; padding:14px 18px; border-bottom:1px solid #51483F; }
.member-row:last-child { border-bottom:0; }
.member-avatar { display:grid; place-items:center; width:38px; height:38px; flex:0 0 38px;
                 border-radius:50%; background:#80633E; color:#FFF8EE; font-family:Georgia,serif;
                 font-size:1.05rem; }
.member-row strong { display:block; color:#F7EAD5; font-size:.95rem; }
.member-row small { display:block; color:#C9BEAF; font-size:.78rem; margin-top:3px; }
.room-card { background:#2A2521; color:#F5EFE6; border:1px solid #51483F; border-radius:14px; padding:18px 20px;
             box-shadow:0 12px 32px rgba(0,0,0,.18); margin:8px 0; transition:.25s ease; overflow:hidden; }
.room-card:hover { border-color:#C5A875; transform:translateY(-3px); }
.room-card-image { height:220px; margin:-18px -20px 16px; background-size:cover; background-position:center;
                   border-bottom:1px solid #51483F; }
.room-card.unavailable { opacity:.72; }
.room-card .title { font-family:Georgia,serif; color:#F5EFE6; font-size:1.2rem; font-weight:700; }
.room-card .meta { color:#C9BEAF; font-size:.86rem; }
.room-card .price { color:#F5EFE6; font-family:Georgia,serif; font-size:1.3rem; font-weight:700; }
.room-card ul { margin:8px 0 0; padding-left:18px; }
.room-card li.warn { color:#A16832; }
.badge { display:inline-block; background:#EFE6D8; color:#71583F; border-radius:999px; padding:3px 9px;
         font-size:.72rem; margin-right:5px; }
.score-wrap { height:7px; background:#EEE8DF; border-radius:999px; margin-top:10px; }
.score-bar { height:7px; background:#A98A58; border-radius:999px; }
.score-num { color:#71583F; font-weight:700; }
.assistant-status { color:#776C63; font-size:.78rem; text-transform:uppercase; letter-spacing:.12em; }
.assistant-status span { display:inline-block; width:8px; height:8px; border-radius:50%; background:#6F8B66;
                         margin-right:7px; box-shadow:0 0 0 4px rgba(111,139,102,.12); }
[data-testid="stChatMessage"], [data-testid*="ChatMessage"],
div[class*="stChatMessage"], div[class*="chatMessage"] {
  border:1px solid #80633E; border-radius:16px; background:#3A2921 !important; color:#F7EAD5 !important;
}
[data-testid="stChatMessage"] > div,
[data-testid*="ChatMessage"] > div,
div[class*="stChatMessage"] > div,
div[class*="chatMessage"] > div,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
[data-testid*="ChatMessage"] [data-testid="stMarkdownContainer"],
div[class*="stChatMessage"] [data-testid="stMarkdownContainer"],
div[class*="chatMessage"] [data-testid="stMarkdownContainer"] {
  background-color:transparent !important;
}
[data-testid="stChatMessage"]::before,
[data-testid*="ChatMessage"]::before,
div[class*="stChatMessage"]::before,
div[class*="chatMessage"]::before {
  background:#3A2921 !important;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span, [data-testid="stChatMessage"] strong,
[data-testid="stChatMessage"] em, [data-testid="stChatMessage"] code,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] *,
[data-testid*="ChatMessage"] p, [data-testid*="ChatMessage"] li,
[data-testid*="ChatMessage"] span, [data-testid*="ChatMessage"] strong,
[data-testid*="ChatMessage"] em, [data-testid*="ChatMessage"] code,
[data-testid*="ChatMessage"] [data-testid="stMarkdownContainer"],
[data-testid*="ChatMessage"] [data-testid="stMarkdownContainer"] *,
div[class*="stChatMessage"] p, div[class*="stChatMessage"] li,
div[class*="stChatMessage"] span, div[class*="stChatMessage"] strong,
div[class*="stChatMessage"] em, div[class*="stChatMessage"] code,
div[class*="stChatMessage"] [data-testid="stMarkdownContainer"],
div[class*="stChatMessage"] [data-testid="stMarkdownContainer"] * {
  color:#F7EAD5 !important;
}
[data-testid="stChatMessage"] a { color:#E2C58E !important; }
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"],
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"] * { color:#C9BEAF !important; }
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"] { background:#3A322A; color:#C5A875; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h1,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h3 {
  color:#FFE8B8 !important;
}
div[data-testid="stButton"] button p { color:inherit !important; }
div[data-testid^="stChatMessage"] { color:#F5EFE6 !important; }
div[data-testid="stChatInput"] { border-radius:999px; background:#2A2521; border:1px solid #51483F; }
div[data-testid="stChatInput"] textarea,
div[data-testid="stChatInput"] textarea:focus { color:#FFF8EE !important; background:transparent; caret-color:#E2C58E; }
div[data-testid="stChatInput"] textarea::placeholder { color:#C9BEAF !important; }
div[data-testid="stButton"] button { border-radius:999px; border:1px solid #80633E; color:#F7EAD5 !important;
                                     background:#3A2921; transition:.22s ease; }
div[data-testid="stButton"] button p,
div[data-testid="stButton"] button span { color:#F7EAD5 !important; }
div[data-testid="stButton"] button:hover { border-color:#C5A875; background:#5A4030; transform:translateY(-1px); }
div[data-testid="stKey_floating_ai"] button { position:fixed; right:28px; bottom:24px; z-index:999;
      border-radius:999px; background:#3A2921; color:#FFF !important; border:1px solid #B9955B;
      box-shadow:0 16px 38px rgba(58,41,33,.28); padding:.65rem 1.1rem; }
div[data-testid="stKey_floating_ai"] button:hover { background:#604938; transform:translateY(-3px); }
@media (max-width: 900px) {
  .luxury-hero { min-height:520px; border-radius:14px; }
  .luxury-hero-content { margin:0 8%; }
  .luxury-hero h1 { font-size:3.7rem; }
  .luxury-footer { flex-direction:column; }
  .page-hero h1 { font-size:2.4rem; }
  .sidebar-footer { display:none; }
}
@media (max-width: 640px) {
  .block-container { padding:1rem .7rem 5rem; }
  .luxury-hero { min-height:480px; background-position:62% center; }
  .luxury-hero-content { margin:0 7%; }
  .luxury-hero h1 { font-size:3.2rem; }
  .hero-copy { font-size:.96rem; }
  .hero-actions { flex-direction:column; align-items:flex-start; }
  .section-heading h2,.guest-promise h2 { font-size:2.15rem; }
  .room-feature-image { height:210px; }
  div[data-testid="stKey_floating_ai"] button { right:16px; bottom:14px; }
  .luxury-footer { text-align:left; }
}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)