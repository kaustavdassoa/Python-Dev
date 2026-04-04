import google.generativeai as genai
import dotenv   
import os

# Make sure your GEMINI_API_KEY is set in your environment
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("⚠️ Error: GOOGLE_API_KEY environment variable not found.")
    exit()

genai.configure(api_key=api_key)

print("Fetching available models...\n")
# Setup the table headers
print(f"{'EXACT MODEL STRING (Use this in code)':<40} | {'DISPLAY NAME':<35} | {'SUPPORTED METHODS'}")
print("-" * 115)

try:
    for m in genai.list_models():
        # Get the supported methods (e.g., generateContent, embedContent)
        methods = ", ".join(m.supported_generation_methods) if m.supported_generation_methods else "N/A"
        
        # Print a formatted row
        print(f"{m.name:<40} | {m.display_name:<35} | {methods}")

except Exception as e:
    print(f"Failed to fetch models. Error: {e}")

print("-" * 115)
