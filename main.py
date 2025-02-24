import streamlit as st
import pandas as pd
import requests
import io

# Seitenkonfiguration
st.set_page_config(
    page_title="BonsAI_Score",
    page_icon="https://sw01.rogsurvey.de/data/bonsai/Kara_23_19/logo_Bonsa_BONSAI_neu.png",
    layout="wide"
)

# Custom CSS für besseres Styling
st.markdown("""
    <style>
    .stTextInput > label, .stTextArea > label {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .stButton > button {
        width: 100%;
        margin-top: 1rem;
    }
    .main > div {
        padding: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# API-Endpunkt aus Secrets laden statt direkt im Code
url = st.secrets["api"]["url"]

# Funktion zur Analyse einer Frage
def analyze_question(frage, antwort):
    body = {
        "message": f"Zu bewertende Frage: {frage}. Zu bewertende Antwort: {antwort}",
        "system_prompt": system_prompt
    }
    
    # Debug-Information in session_state speichern
    if "debug_info" not in st.session_state:
        st.session_state.debug_info = []
    st.session_state.debug_info.append(body)
    
    try:
        with st.spinner(f'Analysiere Antwort: "{antwort}"...'):
            response = requests.post(url, json=body)
            response.raise_for_status()
            data = response.json()
            if data and "message" in data:
                return data["message"].strip()
            else:
                return "Ungültiges Antwortformat"
    except requests.RequestException as e:
        return f"Fehler: {e}"

# Authentifizierung
def check_password():
    """Returns `True` if the user had the correct password."""

    # Platziere Login-Elemente in Spalten für besseres Layout
    login_col1, login_col2, login_col3 = st.columns([1,2,1])
    
    with login_col2:
        if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
            # Logo und Titel nur anzeigen, wenn noch nicht eingeloggt
            st.image("https://sw01.rogsurvey.de/data/bonsai/Kara_23_19/logo_Bonsa_BONSAI_neu.png", width=100)
            st.markdown("### Anmeldung BonsAI_Score")
        
        def password_entered():
            """Checks whether a password entered by the user is correct."""
            if st.session_state["username"] in st.secrets["users"]:
                if st.session_state["password"] == st.secrets["users"][st.session_state["username"]]:
                    st.session_state["password_correct"] = True
                    del st.session_state["password"]  # Passwort aus Session State löschen
                    del st.session_state["username"]  # Username aus Session State löschen
                else:
                    st.session_state["password_correct"] = False

        if "password_correct" not in st.session_state:
            # First run, show inputs for username + password
            st.text_input("Benutzername", key="username")
            st.text_input("Passwort", type="password", key="password")
            st.button("Einloggen", on_click=password_entered, use_container_width=True)

            return False
        elif not st.session_state["password_correct"]:
            # Password not correct, show input + error
            st.text_input("Benutzername", key="username")
            st.text_input("Passwort", type="password", key="password")
            st.button("Einloggen", on_click=password_entered, use_container_width=True)
            st.error("😕 Benutzername oder Passwort falsch")
            return False
        else:
            # Password correct
            return True

# Hauptapp nur anzeigen, wenn Login erfolgreich
if check_password():
    # App-Header
    col_logo, col_title = st.columns([0.2, 0.05])
    with col_logo:
        st.image("https://sw01.rogsurvey.de/data/bonsai/Kara_23_19/logo_Bonsa_BONSAI_neu.png", width=80)
    with col_title:
        st.title("BonsAI___Score")
    st.markdown("---")

    # Container für DataFrame - Wird vor der Verwendung definiert
    results_container = st.container()

    # Zwei Spalten für die Haupteingaben
    col1, col2 = st.columns([1, 1])

    # Initialisierung des DataFrames in session_state
    if "results_df" not in st.session_state:
        st.session_state.results_df = pd.DataFrame(columns=["Antwort", "Codierung"])

    # Funktion zur Verarbeitung der Nennungen
    def process_nennungen():
        # Debug-Info zurücksetzen
        st.session_state.debug_info = []
        
        antworten = [a.strip() for a in nennungen.splitlines() if a.strip()]
        progress_bar = st.progress(0)
        
        # DataFrame zurücksetzen
        st.session_state.results_df = pd.DataFrame(columns=["Antwort", "Codierung"])
        
        for idx, antwort in enumerate(antworten):
            codierung = analyze_question(frage, antwort)
            new_row = pd.DataFrame([{"Antwort": antwort, "Codierung": codierung}])
            st.session_state.results_df = pd.concat([st.session_state.results_df, new_row], ignore_index=True)
            
            # Update Fortschrittsbalken
            progress = (idx + 1) / len(antworten)
            progress_bar.progress(progress)
        
        progress_bar.empty()
        st.success("✅ Analyse abgeschlossen!")

    with col1:
        st.subheader("📝 Eingabebereich")
        
        # System Prompt mit verbesserter UX
        with st.expander("🧪 Experimentiere mit dem System Prompt", expanded=True):
            st.markdown("""
                ### Experimentierbereich für KI-Anweisungen
                
                Hier kannst du mit verschiedenen Anweisungen für die KI experimentieren. 
                Der aktuelle Prompt ist auf die Bewertung von Umfrageantworten optimiert, 
                aber du kannst ihn anpassen und mit verschiedenen Varianten experimentieren.
                
                **Tipps zum Experimentieren:**
                - Versuche die Bewertungskriterien anzupassen
                - Ändere die Gewichtung verschiedener Aspekte
                - Füge neue Kriterien hinzu oder entferne bestehende
                - Experimentiere mit verschiedenen Skalen
                """)
            
            system_prompt = st.text_area(
                "🤖 KI-Anweisungen (System Prompt):",
                value="""Als Sprachassistent bist du darauf spezialisiert, die Qualität von offenen Antworten in Onlineumfragen zu bewerten.

**Eingabeformat**
Du erhältst die Eingabe in folgendem Format:
Frage: [Die gestellte Frage]
Antwort: [Die zu bewertende Antwort]

**Bewertungskriterien**

1. **Relevanz**: 
   - Bewertet die inhaltliche Passung zur Frage (0-100)
   - Bei komplett irrelevanter Antwort = 0

2. **Klarheit**: 
   - Bewertet Verständlichkeit und Struktur (0-100)
   - Auch bei irrelevanter Antwort die tatsächliche Klarheit bewerten

3. **Detailgrad und Menschlichkeit**: 
   - Bewertet Informationsgehalt und Vollständigkeit (0-100)
    - Bewertungsrichtlinien:
      *WICHTIG: Eine Einwortantwort ist oft besser als eine lange, ausschweifende Antwort
      *Wenn eine kurze oder Einwortantwort relevant ist, dann sollte der Score 80-100 sein
       *0 Punkte vergeben bei Lexikon-artigen Erklärungen

4. **Grammatik und Stil**: 
   - Bewertet sprachliche Korrektheit (0-100)
   - Unabhängig von Relevanz oder Detailgrad bewerten

5. **Sprache**:
   - Wenn die Frage Frage und die Antwort auf verschieden Sprachen sind, z.B. Frage auf Deutsch und Antwort auf Englisch: 
     * Sprache = 0, sonst 100
     * Wenn Sprache = 0, dann setze alle Scores=0
     * Bei Nonsense = 0

**Gesamtwertung**:
- Mathematischer Durchschnitt aller fünf Kriterien

# Antwortsyntax (NUR DIESE ZEILE AUSGEBEN)
Relevanz: [Zahl]; Klarheit: [Zahl]; Detailgrad: [Zahl]; Grammatik und Stil: [Zahl]; Sprache: [Zahl];Gesamt: [Zahl]""",
                height=400,
                help="Experimentiere mit verschiedenen Anweisungen und beobachte, wie sich die Bewertungen ändern."
            )
            
            st.info("💡 Probiere verschiedene Varianten aus und vergleiche die Ergebnisse!")
        
        # Trennlinie zwischen Experiment- und Eingabebereich
        st.markdown("---")
        st.markdown("### 📊 Datenerfassung")
        
        # Frage-Eingabe mit verbesserter Beschreibung
        frage = st.text_input(
            "Zu bewertende Frage:",
            placeholder="  Gib hier die Frage ein, zu der die Antworten bewertet werden sollen..."
        )
        
        # Funktion zur Überprüfung der Anzahl der Nennungen
        def count_valid_entries(text):
            return len([line for line in text.splitlines() if line.strip()])

        # Nennungen-Eingabe mit Validierung
        nennungen = st.text_area(
            "Nennungen:",
            placeholder="Gib hier die Antworten ein (eine pro Zeile, maximal 1500). Du kannst die Nennungen am besten direkt aus Excel kopieren und dann hier einfügen.",
            height=200
        )

        # Validierung der Nennungen-Anzahl
        if nennungen:
            num_entries = count_valid_entries(nennungen)
            if num_entries > 2500:
                st.error("⚠️ Maximale Anzahl von 2500 Nennungen überschritten! Aktuell: " + str(num_entries))
                st.warning("Bitte reduziere die Anzahl der Nennungen auf maximal 2500.")
                can_process = False
            else:
                can_process = True
                if num_entries > 0:
                    st.info(f"Anzahl der Nennungen: {num_entries}/2500")

        # Analyse-Button
        if st.button("Analyse starten", use_container_width=True):
            if not frage.strip():
                st.error("⚠️ Bitte gib eine Frage ein.")
            elif not nennungen.strip():
                st.error("⚠️ Bitte gib mindestens eine Nennung ein.")
            elif not can_process:
                st.error("⚠️ Bitte korrigiere die Anzahl der Nennungen.")
            else:
                process_nennungen()

    with col2:
        st.subheader("📊 Ergebnisbereich")
        
        # Debug-Bereich
        with st.expander("🔍 Debug-Informationen", expanded=False):
            st.markdown("### API-Anfragen")
            if "debug_info" in st.session_state and st.session_state.debug_info:
                for idx, debug_data in enumerate(st.session_state.debug_info, 1):
                    st.markdown(f"**Anfrage {idx}:**")
                    st.code(str(debug_data), language="json")
            else:
                st.info("Noch keine Debug-Informationen verfügbar. Starte eine Analyse, um die API-Anfragen zu sehen.")
        
        # Ergebnisanzeige mit Live-Updates
        result_placeholder = st.empty()
        
        if st.session_state.results_df.empty:
            result_placeholder.info("Hier erscheinen die Ergebnisse, sobald du die Analyse startest.")
        else:
            # DataFrame anzeigen
            result_placeholder.dataframe(
                st.session_state.results_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Download-Option nur anzeigen, wenn Ergebnisse vorliegen
            st.markdown("---")
            st.subheader("💾 Download")
            
            # Excel-Download
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                st.session_state.results_df.to_excel(writer, sheet_name='Ergebnisse', index=False)
            
            st.download_button(
                label="📥 Ergebnisse als XLSX herunterladen",
                data=buffer.getvalue(),
                file_name="BonsAI_Score_Ergebnisse.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )


