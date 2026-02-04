import boto3
import json
import streamlit as st
from typing import List, Dict, Any
from src.data.models import MeterReading

class LLMClient:
    def __init__(self, region_name: str = "eu-central-1"):
        """
        Initializes the Bedrock client.
        Tries to use credentials from Streamlit secrets first, then environment variables.
        """
        self.region = region_name
        
        # Check if secrets are available
        if hasattr(st, "secrets") and "AWS_ACCESS_KEY_ID" in st.secrets:
            self.bedrock = boto3.client(
                'bedrock-runtime',
                region_name=st.secrets.get("AWS_DEFAULT_REGION", self.region),
                aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
            )
        else:
            # Fallback to default chain (env vars, ~/.aws/credentials, IAM role)
            self.bedrock = boto3.client('bedrock-runtime', region_name=self.region)
        
        # Model ID for Claude 3.5 Sonnet
        # Note: For Anthropic models, first-time users may need to submit use case details in AWS Console before access is granted.
        self.model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0" 

    def format_readings(self, data_summary: Dict[str, Any]) -> str:
        """
        Converts the data dictionary into a prompt-friendly CSV format.
        Expected data_summary structure:
        {
            "Electricity": {
                "unit": "kWh", 
                "df": pd.DataFrame(columns=['month_str', 'consumption', ...]),
                "mode": "difference"
            },
            ...
        }
        """
        lines = ["Meter Type, Month, Value, Unit"]
        
        for meter_type, info in data_summary.items():
            unit = info.get('unit', 'Units')
            df = info.get('df')
            
            if df is None or df.empty:
                continue
                
            # Iterate through the calculated monthly dataframe
            # Columns expected: 'month_str' (YYYY-MM), 'consumption'
            for _, row in df.iterrows():
                # Format value to 2 decimal places to save tokens and be cleaner
                val = f"{row['consumption']:.2f}"
                date_str = row['month_str']
                lines.append(f"{meter_type}, {date_str}, {val}, {unit}")
                
        return "\n".join(lines)

    def query(self, messages_history: List[Dict[str, str]], data_context: str) -> str:
        """
        Sends the data context and full chat history to Claude via Bedrock.
        messages_history: List of dicts with 'role' (user/assistant) and 'content'
        """
        
        # System Prompt with Safety Guardrails
        system_prompt = """Du bist ein intelligenter und hilfreicher Daten-Analyst.
Deine Aufgabe ist es, Fragen basierend auf den bereitgestellten Zeitreihen-Daten präzise zu beantworten.
Die Daten können sehr vielfältig sein (z.B. Energieverbrauch, Körpergewicht, Niederschlagsmengen, Finanzdaten etc.).

SICHERHEITS- UND VERHALTENSREGELN:
1. DATENBASIERT: Antworte NUR basierend auf den gegebenen Daten. Wenn die Daten eine Antwort nicht hergeben, sage das klar.
2. KONTEXT: Du darfst allgemeines Wissen nutzen, um Trends passend zum Datentyp zu erklären (z.B. Saisonalität bei Wetter/Energie, normale Schwankungen bei Gewicht), aber erfinde keine Fakten über den Nutzer.
3. KEIN MISSBRAUCH: Wenn Fragen nichts mit den Daten oder deren Analyse zu tun haben, antworte höflich: "Ich bin darauf spezialisiert, deine Daten zu analysieren. Diese Frage kann ich nicht beantworten."
4. HAFTUNGSAUSSCHLUSS: Gib keine verbindlichen finanziellen, medizinischen oder baulichen Ratschläge. Deine Analysen sind rein informativ.
5. FORMAT: Antworte in klarem Deutsch. Nutze Markdown für Tabellen oder Listen, wenn es die Lesbarkeit verbessert.

DATEN (CSV-Format):
""" + data_context

        # Convert Streamlit chat history format to Bedrock/Claude format
        # Streamlit: {"role": "user", "content": "..."}
        # Claude: {"role": "user", "content": [{"type": "text", "text": "..."}]}
        bedrock_messages = []
        
        # Helper: Claude expects alternating user/assistant messages.
        # We need to ensure we don't have user->user or assistant->assistant.
        # Also, the first message MUST be user (system is separate).
        
        current_role = None
        current_content_parts = []

        for msg in messages_history:
            role = msg.get("role")
            content = msg.get("content")

            if role not in ["user", "assistant"] or not content:
                continue
            
            # If it's the first valid message, it must be 'user'. 
            # If history starts with 'assistant' (e.g. greeting), we must skip it or prefix/hack it.
            # Usually skipping the greeting is safest for API compliance if we have system prompt data context.
            if not bedrock_messages and role == "assistant":
                continue

            if role == current_role:
                # Same role twice in a row -> Append content to previous message
                # (Claude usually handles text blocks concatenated just fine)
                bedrock_messages[-1]["content"][0]["text"] += f"\n\n{content}"
            else:
                # New role -> New message
                bedrock_messages.append({
                    "role": role,
                    "content": [{"type": "text", "text": content}]
                })
                current_role = role
        
        # Final check: Ensure we have at least one user message
        if not bedrock_messages:
             # Fallback if history was empty or only assistant
             # This should barely happen if called correctly
             return "Keine gültige Anfrage gefunden."

        # Request body for Claude 3
        # We need to make sure we don't exceed context window, but for small history it's fine.
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "system": system_prompt,
            "messages": bedrock_messages,
            "temperature": 0.1 
        })

        try:
            response = self.bedrock.invoke_model(
                body=body,
                modelId=self.model_id,
                accept="application/json",
                contentType="application/json"
            )
            
            response_body = json.loads(response.get("body").read())
            result = response_body.get("content")[0].get("text")
            return result

        except Exception as e:
            # DEBUGGING: Print full error to console
            print(f"🚨 BEDROCK ERROR: {str(e)}")
            
            error_msg = str(e)
            if "AccessDeniedException" in error_msg:
                # Append the real error for debugging in UI too, nicely formatted
                return f"⚠️ Zugriff verweigert.\n\n*Technischer Detail-Fehler:*\n`{error_msg}`\n\n(Bitte prüfe Region und Model Access in der AWS Console)."
            return f"Es ist ein Fehler bei der Kommunikation mit dem KI-Service aufgetreten: {error_msg}"
