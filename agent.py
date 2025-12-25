# governance_layer/sitecustomize.py
import sys
import logging

# Configure a logger to prove it's working
logging.basicConfig(level=logging.INFO, format='[🛡️ GATEWAY] %(message)s')

def patch_gemini():
    """Patches the Google GenAI library safely."""
    
    # 1. Import the library manually
    #    This loads it into sys.modules so the user gets our version later.
    try:
        import google.generativeai as genai
    except ImportError:
        # User doesn't have the library installed; do nothing.
        return

    # 2. Define the Wrapper
    #    We assume the user calls `model.generate_content(...)`
    original_fn = genai.GenerativeModel.generate_content

    def governed_generate_content(self, contents, *args, **kwargs):
        # --- PRE-CHECK (Governance) ---
        logging.info(f"Intercepted Prompt: {contents}")
        
        # Example: Enforce Policy
        if "secret" in str(contents).lower():
            logging.warning("BLOCKING request containing sensitive keyword.")
            raise ValueError("Security Policy Violation: Sensitive data detected.")

        # --- EXECUTE ---
        # Call the real Google function
        response = original_fn(self, contents, *args, **kwargs)

        # --- POST-LOG (Monitoring) ---
        token_count = "Unknown"
        if response.usage_metadata:
            token_count = response.usage_metadata.total_token_count
        
        logging.info(f"Response Received. Usage: {token_count} tokens.")
        return response

    # 3. Apply the Patch (Monkey Patching)
    #    We overwrite the method on the Class itself.
    genai.GenerativeModel.generate_content = governed_generate_content
    logging.info("Gemini Library successfully patched.")

# Run the patcher immediately on startup
patch_gemini()