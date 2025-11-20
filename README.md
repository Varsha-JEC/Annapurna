# Annapurna – FoodBridge

Welcome to **Annapurna – FoodBridge**, a modern web application designed to connect food donors with NGOs and volunteers, reducing food waste and fighting hunger. This project is built with Streamlit, Firebase, and Google's Gemini API.

## 🌟 Features

- **Modern UI/UX:** A clean, card-based design inspired by Swiggy/Zomato.
- **Donor Portal:** User authentication, food donation form with image upload, and location detection.
- **NGO Portal:** Browse and accept available food donations.
- **Volunteer Registration:** A simple form for individuals to join the cause.
- **Feedback System:** Collect and display reviews for donors and NGOs.
- **Gemini Chatbot:** An AI-powered assistant to answer user questions (via an optional backend).
- **Google Maps Integration:** For location services and finding nearby NGOs.

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **Backend:** Firebase (Authentication, Realtime Database, Storage)
- **AI Chatbot:** Google Gemini 2.5 Pro (via FastAPI proxy)
- **Mapping:** Google Maps Platform APIs
- **Optional Backend Proxy:** FastAPI

---

## 🚀 Getting Started

Follow these steps to set up and run the project locally.

### 1. Prerequisites

- Python 3.8+
- A Google Firebase project
- A Google Cloud Platform project with Gemini and Google Maps APIs enabled
- `git` installed on your machine

### 2. Clone the Repository

```bash
git clone <your-repository-url>
cd Annapurna
```

### 3. Setup Firebase

1.  **Create a Firebase Project:** Go to the [Firebase Console](https://console.firebase.google.com/) and create a new project.
2.  **Enable Authentication:** In the Firebase console, go to `Authentication` -> `Sign-in method` and enable **Email/Password** and **Google**.
3.  **Create Realtime Database:** Go to `Realtime Database` -> `Create database`. Start in **test mode** for initial setup (you can apply the security rules later).
4.  **Set up Storage:** Go to `Storage` and click `Get started`.
5.  **Get Service Account Key:**
    - In your Firebase project, go to `Project settings` (gear icon) -> `Service accounts`.
    - Click `Generate new private key`. A JSON file will be downloaded. 
    - **Important:** Keep this file secure. Do not commit it to version control.
6.  **Get Web App Config:**
    - In `Project settings`, scroll down to `Your apps`.
    - Click the web icon (`</>`) to create a new web app.
    - After creating the app, you will see your Firebase configuration keys (`apiKey`, `authDomain`, etc.). You will need these for your `.env` file.

### 4. Setup Google Cloud (Gemini & Maps)

1.  **Create a Google Cloud Project:** If you don't have one, create a project in the [Google Cloud Console](https://console.cloud.google.com/).
2.  **Enable APIs:**
    - Go to `APIs & Services` -> `Library`.
    - Search for and enable the following APIs:
        - **Generative AI API** (or Vertex AI API for more advanced use)
        - **Maps JavaScript API**
        - **Geocoding API**
        - **Distance Matrix API**
3.  **Get API Keys:**
    - Go to `APIs & Services` -> `Credentials`.
    - Create an API key for Google Maps and another for Gemini.
    - **Restrict your API keys** for security before using them in production.

### 5. Configure Environment Variables

1.  Create a file named `.env` in the root directory of the project (you can copy `.env.example`).
2.  Fill in the values based on the credentials you obtained:

```ini
# Firebase Configuration
FIREBASE_CREDENTIALS_JSON_PATH="/path/to/your/firebase-service-account.json"
FIREBASE_API_KEY="your_firebase_api_key"
FIREBASE_AUTH_DOMAIN="your_project_id.firebaseapp.com"
FIREBASE_DATABASE_URL="https://your_project_id.firebaseio.com"
FIREBASE_STORAGE_BUCKET="your_project_id.appspot.com"

# Google APIs Configuration
GEMINI_API_KEY="your_gemini_api_key"
GOOGLE_MAPS_API_KEY="your_google_maps_api_key"
```

### 6. Install Dependencies

```bash
# For the main Streamlit app
pip install -r requirements.txt

# For the optional FastAPI backend
pip install -r backend/requirements.txt
```

### 7. Import Sample Data & Rules (Optional)

1.  **Firebase Rules:**
    - Go to your Firebase `Realtime Database` -> `Rules` tab.
    - Copy the content of `firebase_rules.json` and paste it into the editor. Click `Publish`.
2.  **Sample Data:**
    - Go to your Firebase `Realtime Database` -> `Data` tab.
    - Click the three-dots menu and select `Import JSON`.
    - Upload the `sample_data.json` file.

---

## 🏃‍♀️ Running the Application

### 1. Run the Streamlit Frontend

Make sure you are in the root directory of the project.

```bash
streamlit run Annapurna.py
```

The application should now be running at `http://localhost:8501`.

### 2. Run the FastAPI Backend (Optional)

If you want to use the secure backend proxy for the Gemini chatbot:

```bash
cd backend
uvicorn main:app --reload
```

The backend server will be running at `http://localhost:8000`.

---

## 🎨 Customization

- **Logo & Images:** Replace the images in `assets/images/` with your own.
- **Styling:** Modify the CSS in `assets/css/style.css` to change the look and feel.
- **Functionality:** The Python files in the `pages/` directory are well-commented. You can extend the functionality by integrating the Firebase Admin SDK and making calls to the Google APIs.
