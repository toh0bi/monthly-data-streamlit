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

**Please log in or register to continue.**
""",
        "CHAT_GREETING": "Hello! I have access to your monthly data. Ask me about trends, comparisons or details – for example 'How was my electricity consumption in 2023?', 'Analyze my weight trend' or 'Is it raining more this year than last year?'.",
        "MODE_HELP_COUNTER": "Use this for meters that simply count up (like Electricity, Gas, Water meters).\nThe app will calculate the monthly usage by subtracting the previous month's value from the current reading.",
        "MODE_HELP_DIRECT": "Use this for data where the value itself is what you want to track for that month.\nExamples: Body Weight (kg), Rainfall (mm), Average Temperature (°C), Bank Account Balance (€).",
        "MODE_HELP_FORMULA": "Combine existing data series using a mathematical formula (e.g. `[Main Meter] - [Heatpump] + 0.5 * [PV]`).\nCalculated after monthly aggregation. Months with unknown/missing source data are omitted, while valid 0 values are preserved.",
        "FORMULA_HELP_TEXT": "Reference series in brackets like `[Series Name]`. Supported operators: `+`, `-`, `*`, `/`, `(`, `)` and numeric factors like `2 * [Series]`."
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

**Bitte melde dich an oder registriere dich, um fortzufahren.**
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
        "Username must be at least 3 characters long": "Benutzername muss mindestens 3 Zeichen lang sein",
        "Password must be at least 6 characters long": "Passwort muss mindestens 6 Zeichen lang sein",
        "Legacy Chat ID (Optional)": "Alte Chat-ID (Optional, falls du Daten migrieren willst)",
        "Enter your numeric Telegram Chat ID to migrate your existing bot data. Each Chat ID can only be claimed once.": "Gib deine numerische Telegram-Chat-ID ein, um deine bestehenden Bot-Daten zu übernehmen. Jede Chat-ID kann nur einmal verknüpft werden.",
        "Invalid Legacy Chat ID format.": "Ungültiges Format für die alte Chat-ID (nur Zahlen erlaubt).",
        "This Legacy Chat ID is not authorized for migration.": "Diese Chat-ID ist nicht für die Migration freigegeben.",
        "Legacy Chat ID not found.": "Alte Chat-ID wurde nicht gefunden.",
        "This Legacy Chat ID is already linked to an account.": "Diese Chat-ID ist bereits mit einem Konto verknüpft.",
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
        "Min": "Min",
        "Max": "Max",
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
        "No meter types defined. Go to Settings to add one.": "Keine Datenreihen definiert. Gehe zu Einstellungen, um eine hinzuzufügen.",
        "No data series defined. Go to Settings to add one.": "Keine Datenreihen definiert. Gehe zu Einstellungen, um eine hinzuzufügen.",
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
        "Define Data Categories": "Datenreihen definieren",
        "Define Data Series": "Datenreihen definieren",
        "Here you can define what kind of data you want to track. This can be utility meters (electricity, water) or personal metrics (weight, rainfall, etc.).": "Hier kannst du definieren, welche Daten du verfolgen möchtest. Das können Zähler (Strom, Wasser) oder persönliche Werte (Gewicht, Regenmenge etc.) sein.",
        "Here you can define what kind of data you want to track. This can be utility meters (electricity, water), personal metrics (weight, rainfall) or calculated series based on formulas.": "Hier kannst du definieren, welche Datenreihen du verfolgen möchtest – von klassischen Zählern (Strom, Wasser) über direkte Messwerte (Gewicht, Regen) bis hin zu berechneten Datenreihen per Formel.",
        "Add New Category": "Neue Datenreihe hinzufügen",
        "Add New Data Series": "Neue Datenreihe hinzufügen",
        "Counter / Accumulating": "Zähler / Akkumulierend",
        "Counter / Accumulating (Calculates Difference)": "Zähler / Akkumulierend (Berechnet Differenz)",
        "MODE_HELP_COUNTER": "Verwende dies für Zähler, die einfach hochzählen (wie Strom, Gas, Wasser).\nDie App berechnet den monatlichen Verbrauch durch Subtraktion des Vormonatswertes.",
        "MODE_HELP_DIRECT": "Verwende dies für Daten, bei denen der Wert selbst das Ziel ist.\nBeispiele: Körpergewicht (kg), Niederschlag (mm), Durchschnittstemperatur (°C), Kontostand (€).",
        "MODE_HELP_FORMULA": "Kombiniere bestehende Datenreihen über eine mathematische Formel (z.B. `[Hauptzähler] - [Wärmepumpe] + 0.5 * [PV]`).\nEs wird nach der monatlichen Aufbereitung gerechnet. Monate mit unbekannten Werten werden ausgelassen; echte 0-Werte bleiben erhalten.",
        "FORMULA_HELP_TEXT": "Referenziere Datenreihen in eckigen Klammern wie `[Name]`. Erlaubte Operatoren: `+`, `-`, `*`, `/`, `(`, `)` sowie Faktoren wie `2 * [Name]`.",
        "Direct Value": "Direkter Wert",
        "Direct Value / Measurement": "Direkter Wert / Messung",
        "Direct Value (Takes Value as is)": "Direkter Wert (Nimmt Wert wie er ist)",
        "Calculated (Formula)": "Berechnet (Formel)",
        "Formula": "Formel",
        "Formula (e.g. [Main Meter] - [Sub Meter] + 2 * [Solar])": "Formel (z.B. [Hauptzähler] - [Unterzähler] + 2 * [Solar])",
        "Click to insert data series or operators into the formula:": "Klicke, um Datenreihen oder Operatoren in die Formel einzufügen:",
        "Create at least one data series first to use in a formula.": "Erstelle zuerst mindestens eine Datenreihe, um sie in einer Formel zu verwenden.",
        "Please enter a name.": "Bitte gib einen Namen ein.",
        "Please enter a formula.": "Bitte gib eine Formel ein.",
        "Formula must reference at least one data series in [brackets].": "Die Formel muss mindestens eine Datenreihe in [eckigen Klammern] enthalten.",
        "Unmatched brackets in formula.": "Unvollständige eckige Klammern in der Formel.",
        "Invalid mathematical expression.": "Ungültiger mathematischer Ausdruck.",
        "Name (e.g. 'Weight', 'Electricity')": "Name (z.B. 'Gewicht', 'Strom')",
        "Unit (e.g. 'kg', 'kWh')": "Einheit (z.B. 'kg', 'kWh')",
        "Type": "Typ",
        "Add Category": "Datenreihe hinzufügen",
        "Add Data Series": "Datenreihe hinzufügen",
        "Added {}": "{} hinzugefügt",
        "Category already exists": "Datenreihe existiert bereits",
        "Data series already exists": "Datenreihe existiert bereits",
        "Manage Existing Categories": "Bestehende Datenreihen verwalten",
        "Manage Existing Data Series": "Bestehende Datenreihen verwalten",
        "⬆️ Up": "⬆️ Hoch",
        "⬇️ Down": "⬇️ Runter",
        "Evaluation Mode": "Auswertungsmodus",
        "Select 'Counter' for increasing meters (utilities) or 'Direct Value' for measurements (weight, temp).": "Wähle 'Zähler' für aufsteigende Zähler (Energie) oder 'Direkter Wert' für Messungen (Gewicht, Temp).",
        "Save Configuration": "Konfiguration speichern",
        "Saved": "Gespeichert",
        "Delete {}": "Lösche {}",
        "Deleted {}": "{} gelöscht",
        "System & Quota": "System & Quota",
        "AI Requests Used (Month)": "Genutzte KI-Anfragen (Monat)",
        "Data Categories": "Datenreihen",
        "Data Series": "Datenreihen",

        # AI Pages
        "🤖 Talk to your Data": "🤖 Sprich mit deinen Daten",
        "Analyze your monthly data with AI support (Powered by AWS Bedrock / Claude Haiku 5.5)": "Analysiere deine monatlichen Daten mit KI-Unterstützung (Powered by AWS Bedrock / Claude Haiku 5.5)",
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
        "Or upload an image (Photo, Scan)": "Oder lade ein Bild hoch (Foto, Scan)",
        "Start AI Analysis": "KI-Analyse starten",
        "Please enter text first.": "Bitte gib erst Text ein.",
        "Please enter text or upload an image.": "Bitte gib Text ein oder lade ein Bild hoch.",
        "Analyzing structure...": "Analysiere Struktur...",
        "Analyzing data...": "Analysiere Daten...",
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
