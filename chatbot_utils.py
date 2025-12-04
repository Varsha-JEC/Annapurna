import google.generativeai as genai
import logging
from typing import List, Dict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnniChatbot:
    """A chatbot assistant for the Annapurna food donation platform."""

    def __init__(self, api_key: str):
        if not api_key or not isinstance(api_key, str) or not api_key.strip():
            logger.error("No API key provided")
            raise ValueError("A valid Google Gemini API key is required")

        try:
            genai.configure(api_key=api_key.strip())
            logger.info("API key configured successfully")

            # Enhanced system prompt for Anni with stricter guidelines
            self.system_prompt = """
You are Anni, a helpful and friendly chatbot assistant for Annapurna - 
a food donation platform that connects donors with NGOs to reduce food waste 
and help those in need.

IMPORTANT: You MUST ONLY answer questions related to:
- Annapurna platform and how it works
- Food donation process for donors
- NGO registration and acceptance process
- Volunteer opportunities
- Food waste reduction and hunger relief
- Platform features and navigation

Your role and capabilities:
1. Help users understand how Annapurna works
2. Guide donors on the donation process:
   - Register as Donor on the platform
   - Fill the donation form with food details
   - NGOs will see and accept the donation
   - Coordinate pickup/delivery
3. Assist NGOs in accepting donations:
   - Register as NGO on the platform
   - Browse available donations
   - Accept donations that match your needs
   - Coordinate with donors for collection
4. Explain volunteer opportunities
5. Answer questions about food waste and hunger in India

Key Information about Annapurna:
- Platform connects food donors (restaurants, events, individuals) with verified NGOs
- Donors register and post available food donations with details
- NGOs can browse and accept donations based on their capacity
- Volunteers help with food collection and distribution
- Mission: Building bridges between surplus food and hungry hearts
- Based in India, helping fight food waste and hunger
- Contact: AnnapurnaFoodbridge@gmail.com
- Phone: +91 9630995163, +91 7049302011

**FORMATTING GUIDELINES - VERY IMPORTANT:**
- Use **bold text** for important keywords and headings (wrap with **text**)
- Use emojis generously to make responses colorful and engaging 💖✨
- Structure responses with bullet points using • or numbered lists
- Add line breaks between sections for better readability
- Use these emojis contextually:
  💖 - for food/donation topics
  🏘️ - for NGO topics
  🤝 - for volunteer topics
  ✅ - for successful steps
  📧 - for contact info
  📞 - for phone numbers
  💡 - for tips and suggestions
  🌟 - for highlighting important points
  ⚠️ - for warnings or important notes
  🎯 - for goals/targets
  
- Start responses with relevant emoji
- Use separators like "---" or "━━━" between major sections
- Highlight action items with ✨ or 🎯
- End with encouraging emoji like 💚 or 🌾

**Example of good formatting:**

💖 **How to Donate Food**

Here's how you can make a difference:

✅ **Step 1: Register**
- Visit the Donor page
- Sign up with your details

✅ **Step 2: Post Donation**
- Fill the donation form
- Include food type, quantity, and timing

✅ **Step 3: Connect**
- NGOs will see your donation
- They'll contact you for pickup

💡 **Pro Tip:** Include clear photos and accurate quantity for faster acceptance!

Need help? 📧 AnnapurnaFoodbridge@gmail.com

---

Response Guidelines:
- Keep responses concise but well-formatted (2-5 paragraphs with clear structure)
- Always use visual elements (emojis, bold, bullets)
- If asked about registration, guide them to specific pages (Donor/NGO/Volunteer)
- For technical issues, provide support contact details with proper formatting
- Be warm, empathetic, and encouraging
- If question is NOT related to Annapurna, politely redirect with styled message

Example topics you CAN help with:
✅ How to donate food
✅ How to register as NGO
✅ Volunteer opportunities
✅ Platform features
✅ Food waste statistics
✅ Donation process details

Example topics you CANNOT help with:
❌ General knowledge questions
❌ Unrelated topics (movies, sports, etc.)
❌ Other platforms or services
❌ Personal advice unrelated to food donation

Always stay focused on Annapurna's mission of connecting food donors with those in need! 🌾💖
""".strip()

            generation_config = {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 800,
            }

            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT",
                 "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH",
                 "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                 "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                 "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]

            # Get list of actually available models
            try:
                available_models = [
                    m.name for m in genai.list_models()
                    if hasattr(m, "supported_generation_methods") and 
                    "generateContent" in m.supported_generation_methods
                ]
                logger.info(f"Available models: {available_models}")
            except Exception as e_ls:
                available_models = []
                logger.warning(f"Could not list models: {e_ls}")

            # Priority order of model preferences (use actual available model names)
            preferred_models = [
                "models/gemini-2.5-flash",
                "models/gemini-2.0-flash",
                "models/gemini-flash-latest",
                "models/gemini-2.5-pro",
                "models/gemini-2.0-flash-001",
                "models/gemini-pro-latest",
            ]

            # Filter to only use models that are actually available
            models_to_try = []
            if available_models:
                # First try preferred models that are available
                for model in preferred_models:
                    if model in available_models:
                        models_to_try.append(model)
                
                # If no preferred models available, try any available model with 'flash' or 'pro' in name
                if not models_to_try:
                    for model in available_models:
                        if 'flash' in model.lower() or 'pro' in model.lower():
                            if 'tts' not in model.lower() and 'image' not in model.lower():
                                models_to_try.append(model)
                                if len(models_to_try) >= 5:
                                    break
            else:
                # Fallback if can't list models
                models_to_try = preferred_models

            logger.info(f"Will try these models in order: {models_to_try}")

            self.model = None
            self.chat = None
            failures = []

            for model_name in models_to_try:
                try:
                    logger.info(f"Trying model: {model_name}")

                    test_model = genai.GenerativeModel(
                        model_name=model_name,
                        generation_config=generation_config,
                        safety_settings=safety_settings,
                        system_instruction=self.system_prompt,
                    )

                    # Test if the model actually works
                    test_chat = test_model.start_chat(history=[])
                    test_response = test_chat.send_message("Hi")

                    if hasattr(test_response, "text") and test_response.text:
                        self.model = test_model
                        self.model_name = model_name
                        self.chat = self.model.start_chat(history=[])
                        logger.info(f"✅ Successfully initialized and tested model: {model_name}")
                        break

                except Exception as e_try:
                    msg = str(e_try)
                    failures.append(f"{model_name}: {msg[:100]}")
                    logger.warning(f"Failed with {model_name}: {msg[:100]}")
                    continue

            if not self.model or not self.chat:
                details = " | ".join(failures[:3]) if failures else "No attempts recorded"
                avail = ", ".join(available_models[:10]) if available_models else "(could not list)"
                raise Exception(
                    f"Could not initialize any Gemini model. "
                    f"First 3 failures: {details}. "
                    f"First 10 available models: {avail}"
                )

            logger.info(f"AnniChatbot initialized successfully with model: {self.model_name}")

        except Exception as e:
            logger.error(f"Failed to initialize AnniChatbot: {str(e)}")
            raise Exception(f"Failed to initialize chatbot: {str(e)}")

    def get_response(self, user_message: str) -> str:
        """Get a response from the chatbot with enhanced context."""
        if not user_message or not isinstance(user_message, str) or not user_message.strip():
            return "I didn't receive your message. Could you please try again? 🤔"

        try:
            logger.info(f"Sending message to {self.model_name}: {user_message[:50]}...")
            
            response = self.chat.send_message(user_message)

            # Extract response text
            if hasattr(response, "text") and response.text.strip():
                response_text = response.text.strip()
                logger.info(f"✅ Response received: {len(response_text)} characters")
                return response_text
            
            if hasattr(response, 'prompt_feedback'):
                logger.warning(f"Response blocked: {response.prompt_feedback}")
                return "I couldn't generate a response due to safety filters. Could you rephrase? 🤔"

            return "I'm not sure how to respond to that. Could you ask about food donation, NGO registration, or volunteering with Annapurna? 🌾"

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating response: {error_msg}")
            
            if "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                return "⏳ High demand! Please try again in a moment."
            elif "404" in error_msg or "not found" in error_msg.lower():
                return (
                    "⚠️ Model unavailable. Please contact support:\n"
                    "📧 AnnapurnaFoodbridge@gmail.com\n"
                    "📞 +91 9630995163 | +91 7049302011"
                )
            else:
                return (
                    "I'm having trouble connecting right now. 😔 "
                    "Please try again in a moment or contact our support team at "
                    "AnnapurnaFoodbridge@gmail.com if the issue persists."
                )

    def reset_chat(self) -> None:
        """Reset the chat history while maintaining system instruction."""
        try:
            self.chat = self.model.start_chat(history=[])
            logger.info("Chat history reset successfully")
        except Exception as e:
            logger.error(f"Error resetting chat: {str(e)}")
            raise Exception(f"Failed to reset chat: {str(e)}")

    def get_chat_history(self) -> list:
        """Get the current chat history."""
        try:
            history: List[Dict] = []
            for msg in self.chat.history:
                text_parts = []
                for p in msg.parts:
                    if hasattr(p, "text"):
                        text_parts.append(p.text)
                history.append({
                    "role": msg.role,
                    "content": " ".join(text_parts),
                    "timestamp": datetime.now().isoformat()
                })
            return history
        except Exception as e:
            logger.error(f"Error retrieving chat history: {str(e)}")
            return []
