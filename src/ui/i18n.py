import streamlit as st

# Dictionary with translations
# Key: The English text (used as ID)
# Value: Dictionary of translations
TRANSLATIONS = {
    "en": {
        "HOME_PAGE_DESCRIPTION": """
### Your Personal Data Tracker

Keep track of any monthly data you care about:
*   ⚡ **Utilities** (Electricity, Water, Gas, PV)
*   💪 **Health** (Body Weight, Gym Visits)
*   🌱 **Environment** (Rainfall, Temperature)
*   💰 **Finance** (Savings, Expenses)

**Features:**
*   📅 **Easy Data Entry:** Smart forms adapt to your data types.
*   📈 **Interactive Dashboards:** Visualize trends, seasonalities and compare years.
*   🤖 **AI Analysis:** Chat with your data using advanced AI.
*   📱 **Mobile Friendly:** Works great on your phone.

👈 **Please log in or register in the sidebar to continue.**
""",
        "CHAT_GREETING": "Hello! I have access to your monthly data. Ask me about trends, comparisons or details – for example 'How was my electricity consumption in 2023?', 'Analyze my weight trend' or 'Is it raining more this year than last year?'."
    },
    "de": {
        # Special Keys
        "HOME_PAGE_DESCRIPTION": """
### Dein persönlicher Daten-Tracker

Verfolge monatliche Daten, die dir wichtig sind:
*   ⚡ **Versorgung** (Strom, Wasser, Gas, PV)
*   💪 **Gesundheit** (Körpergewicht, Gym-Besuche)
*   🌱 **Umwelt** (Niederschlag, Temperatur)
*   💰 **Finanzen** (Ersparnisse, Ausgaben)

**Funktionen:**
*   📅 **Einfache Dateneingabe:** Smarte Formulare passen sich deinen Datentypen an.
*   📈 **Interaktive Dashboards:** Visualisiere Trends, Saisonalitäten und vergleiche Jahre.
*   🤖 **KI Analyse:** Chatte mit deinen Daten durch fortschrittliche KI.
*   📱 **Mobilfreundlich:** Funktioniert hervorragend auf deinem Handy.

👈 **Bitte melde dich in der Sidebar an oder registriere dich, um fortzufahren.**
""",

        # App / Navigation
        "Monthly Data Bot": "Monthly Data Bot",
        "Dashboard": "Dashboard",
        "Data Entry": "Dateneingabe",
        "AI Data Import": "KI Daten-Import",
        "AI Analysis": "KI Analyse",
        "Settings": "Einstellungen",
        "Logged in as": "Angemeldet als",
        "Logout": "Abmelden",
        
        # Auth
        "Username": "Benutzername",
        "Password": "Passwort",
        "Confirm Password": "Passwort bestätigen",
        "Login": "Anmelden",
        "Register": "Registrieren",
        "Welcome back, {}!": "Willkommen zurück, {}!",
        "Invalid username or password": "Ungültiger Benutzername oder Passwort",
        "Passwords do not match": "Passwörter stimmen nicht überein",
        "Username already exists": "Benutzername existiert bereits",
        "Legacy Chat ID (Optional)": "Alte Chat-ID (Optional, falls du Daten migrieren willst)",
        "Registration successful! Please login.": "Registrierung erfolgreich! Bitte anmelden.",
        "Registration failed. Please try again.": "Registrierung fehlgeschlagen. Bitte erneut versuchen.",
        "Welcome to Monthly Data Bot 📊": "Willkommen beim Monatsdaten Bot 📊",
        
        # Common
        "Submit": "Absenden",
        "Save": "Speichern",
        "Cancel": "Abbrechen",
        "Error": "Fehler",
        "Success": "Erfolg",
        "No data.": "Keine Daten.",
        
        # Dashboard
        "No readings.": "Keine Messwerte.",
        "Not enough data to calculate consumption.": "Nicht genügend Daten für Verbrauchsberechnung.",
        "Filter Years": "Jahre filtern",
        "No data in selected range.": "Keine Daten im gewählten Bereich.",
        "Monthly": "Monatlich",
        "Monthly Total": "Gesamt", # Used in context "Monthly Total" -> "Monatlich Gesamt"
        "Value": "Wert",
        "View Mode": "Ansicht",
        "Year-over-Year": "Jahresvergleich",
        "Linear Trend": "Linearer Trend",
        "Month": "Monat",
        "Year": "Jahr",
        "Date": "Datum",
        "Yearly Statistics": "Jahresstatistik",
        "Year {}": "Jahr {}",
        "Data Points": "Datensätze",
        "Total": "Gesamt",
        "Avg Monthly": "Ø Monatlich",
        "Avg Daily": "Ø Täglich",
        # Months
        "Jan": "Jan",
        "Feb": "Feb",
        "Mar": "Mär",
        "Apr": "Apr",
        "May": "Mai",
        "Jun": "Jun",
        "Jul": "Jul",
        "Aug": "Aug",
        "Sep": "Sep",
        "Oct": "Okt",
        "Nov": "Nov",
        "Dec": "Dez",
        
        # Data Entry
        "No meter types defined. Go to Settings to add one.": "Keine Datentypen definiert. Gehe zu Einstellungen, um einen hinzuzufügen.",
        "Add New Reading": "Neuen Eintrag hinzufügen",
        "Counter Value": "Zählerstand / Wert",
        "Add Reading": "Eintrag hinzufügen",
        "Reading added!": "Eintrag hinzugefügt!",
        "Failed to add reading.": "Eintrag konnte nicht hinzugefügt werden.",
        "History: {}": "Verlauf: {}",
        "📥 Download {} History (CSV)": "📥 Download {} Verlauf (CSV)",
        "{} readings selected": "{} Einträge ausgewählt",
        "🗑️ Delete Selected": "🗑️ Ausgewählte löschen",
        "Deleted!": "Gelöscht!",
        "No readings found.": "Keine Einträge gefunden.",
        
        # Settings
        "Define Data Categories": "Daten-Kategorien definieren",
        "Here you can define what kind of data you want to track. This can be utility meters (electricity, water) or personal metrics (weight, rainfall, etc.).": "Hier kannst du definieren, welche Daten du verfolgen möchtest. Das können Zähler (Strom, Wasser) oder persönliche Werte (Gewicht, Regenmenge etc.) sein.",
        "Add New Category": "Neue Kategorie hinzufügen",
        "Counter / Accumulating": "Zähler / Akkumulierend",
        "Counter / Accumulating (Calculates Difference)": "Zähler / Akkumulierend (Berechnet Differenz)",
        "Direct Value / Measurement": "Direkter Wert / Messung",
        "Direct Value (Takes Value as is)": "Direkter Wert (Nimmt Wert wie er ist)",
        "Name (e.g. 'Weight', 'Electricity')": "Name (z.B. 'Gewicht', 'Strom')",
        "Unit (e.g. 'kg', 'kWh')": "Einheit (z.B. 'kg', 'kWh')",
        "Type": "Typ",
        "Add Category": "Kategorie hinzufügen",
        "Added {}": "{} hinzugefügt",
        "Category already exists": "Kategorie existiert bereits",
        "Manage Existing Categories": "Bestehende Kategorien verwalten",
        "⬆️ Up": "⬆️ Hoch",
        "⬇️ Down": "⬇️ Runter",
        "Evaluation Mode": "Auswertungsmodus",
        "Select 'Counter' for increasing meters (utilities) or 'Direct Value' for measurements (weight, temp).": "Wähle 'Zähler' für aufsteigende Zähler (Energie) oder 'Direkter Wert' für Messungen (Gewicht, Temp).",
        "Save Configuration": "Konfiguration speichern",
        "Saved": "Gespeichert",
        "Delete {}": "Lösche {}",
        "System & Quota": "System & Quota",
        "AI Requests Used (Month)": "Genutzte KI-Anfragen (Monat)",
        "Data Categories": "Daten-Kategorien",

        # AI Pages
        "🤖 Talk to your Data": "🤖 Sprich mit deinen Daten",
        "Analyze your monthly data with AI support (Powered by AWS Bedrock / Claude 3.5 Sonnet)": "Analysiere deine monatlichen Daten mit KI-Unterstützung (Powered by AWS Bedrock / Claude 3.5 Sonnet)",
        "Monthly Quota: {}/{} requests": "Monats-Quota: {}/{} Anfragen",
        "You have reached your monthly limit of {} requests. Come back next month!": "Du hast dein monatliches Limit von {} Anfragen erreicht. Komm nächsten Monat wieder!",
        "🗑️ Start new chat": "🗑️ Neuen Chat beginnen",
        "Clears the current chat history": "Löscht den aktuellen Chatverlauf",
        "Ask a question about your data...": "Stelle eine Frage zu deinen Daten...",
        "⏳ *Analyzing data...*": "⏳ *Analysiere Daten...*",
        "Unfortunately, I cannot find any meter data in your profile. Please add data in the dashboard first.": "Ich finde leider keine Zählerdaten in deinem Profil. Bitte füge erst Daten im Dashboard hinzu.",
        "Insufficient data available for analysis.": "Keine ausreichenden Daten für eine Analyse vorhanden.",
        "CHAT_GREETING": "Hallo! Ich habe Zugriff auf deine monatlichen Daten. Frag mich nach Trends, Vergleichen oder Details – zum Beispiel 'Wie war mein Stromverbrauch 2023?', 'Analysiere meinen Gewichtsverlauf' oder 'Regnet es dieses Jahr mehr als letztes Jahr?'.",
        
        "🤖 AI Data Import": "🤖 KI Daten-Import",
        "Paste chaotic data simply via Copy & Paste. The AI structures it for you.": "Füge chaotische Daten einfach per Copy & Paste ein. Die KI strukturiert sie für dich.",
        "Paste data here (Excel, CSV, Notes...)": "Daten hier einfügen (Excel, CSV, Notizen...)",
        "Example:\nJan 2023: Electricity 1050, Water 50\nFeb 2023: Electricity 1120, Water 52\n...": "Beispiel:\nJan 2023: Strom 1050, Wasser 50\nFeb 2023: Strom 1120, Wasser 52\n...",
        "Start AI Analysis": "KI-Analyse starten",
        "Please enter text first.": "Bitte gib erst Text ein.",
        "Analyzing structure...": "Analysiere Struktur...",
        "AI Error: {}": "KI-Fehler: {}",
        "Could not find valid data.": "Konnte keine gültigen Daten finden.",
        "{} records found!": "{} Datensätze gefunden!",
        "Error processing response: {}...": "Fehler beim Verarbeiten der Antwort: {}...",
        "Preview": "Vorschau",
        "💾 Save All": "💾 Alle speichern",
        "{} records successfully saved!": "{} Einträge erfolgreich gespeichert!",
        "Error at row {}: {}": "Fehler bei Zeile {}: {}",
    }
}

def get_text(text_id: str, *args) -> str:
    """
    Retrieves the translation for the given text_id based on the current session language.
    If the language is English (default) or the translation is missing, returns the text_id itself.
    
    Args:
        text_id (str): The text to translate (usually the English text).
        *args: Optional arguments for string formatting (e.g. for "Welcome back, {}!").
    
    Returns:
        str: Not translated or translated text.
    """
    lang = st.session_state.get('language', 'en')
    
    if lang == 'en':
        # Check for special keys in English (like descriptions) or return ID
        translations = TRANSLATIONS.get('en', {})
        result = translations.get(text_id, text_id)
    else:
        # Try to find translation
        translations = TRANSLATIONS.get(lang, {})
        result = translations.get(text_id, text_id) # Fallback to text_id (English)
        
    # Format if args provided
    if args:
        try:
            return result.format(*args)
        except IndexError:
            return result
            
    return result

# Alias for convenience (standard gettext convention)
t = get_text
