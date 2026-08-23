"""Seed content, transcribed from docs/MESSAGE_MAP.md.

Everything here is seeded DISABLED. Content becomes enabled only by passing
verification, which is a human decision recorded in the audit log.

All Urdu strings are DRAFTS pending review by a fluent Urdu speaker.
All `kokoro` strings are Devanagari pronunciation aids for Kokoro's Hindi
voices — they are pronunciation, not translation, and must be verified BY EAR.
"""

from __future__ import annotations

# --------------------------------------------------------------- signs
# (code, urdu_meaning, english_meaning, demo_critical, notes)

SIGNS: list[tuple[str, str, str, bool, str]] = [
    # --- the 15-sign freeze list ---
    ("HEADACHE", "سر درد", "headache", False, "Pain concept — blocked on D015"),
    ("CHEST_PAIN", "سینے میں درد", "chest pain", True, "Pain concept — blocked on D015"),
    ("STOMACH_PAIN", "پیٹ میں درد", "stomach pain", False, "Pain concept — blocked on D015"),
    ("FEVER", "بخار", "fever", True, ""),
    ("COUGH", "کھانسی", "cough", False, ""),
    ("VOMITING", "قے", "vomiting", False, ""),
    ("DIZZINESS", "چکر", "dizziness", False, ""),
    ("BREATHING_PROBLEM", "سانس کی تکلیف", "breathing problem", True,
     "High-risk confusion — extra testing required"),
    ("BLEEDING", "خون بہنا", "bleeding", False,
     "High-risk confusion — extra testing required"),
    ("HELP", "مدد", "help", False, ""),
    ("YES", "ہاں", "yes", True, "High-risk confusion pair with NO — tested on Day 1"),
    ("NO", "نہیں", "no", True, "High-risk confusion pair with YES — tested on Day 1"),
    ("TWO", "دو", "two", True, "Confusable with ONE/THREE"),
    ("DAY", "دن", "day", True, ""),
    ("INJURY", "چوٹ", "injury", False, "Buffer sign"),
    # --- P1 candidates, beyond the freeze list ---
    ("EYE_PAIN", "آنکھ میں درد", "eye pain", False, "Pain concept — blocked on D015"),
    ("BACK_PAIN", "کمر میں درد", "back pain", False, "Pain concept — blocked on D015"),
    ("WEAKNESS", "کمزوری", "weakness", False, ""),
    ("ALLERGY", "الرجی", "allergy", False, "High-risk confusion"),
]

# --------------------------------------------------------------- messages
# (code, concepts, urdu, english, kokoro, priority, demo_critical)

MESSAGES: list[tuple[str, list[str], str, str, str, str, bool]] = [
    ("HEADACHE", ["HEADACHE"],
     "مجھے سر میں درد ہے۔", "I have a headache.",
     "मुझे सर में दर्द है।", "p0", False),
    ("CHEST_PAIN", ["CHEST_PAIN"],
     "مجھے سینے میں درد ہے۔", "I have chest pain.",
     "मुझे सीने में दर्द है।", "p0", True),
    ("STOMACH_PAIN", ["STOMACH_PAIN"],
     "میرے پیٹ میں درد ہے۔", "My stomach hurts.",
     "मेरे पेट में दर्द है।", "p0", False),
    ("FEVER", ["FEVER"],
     "مجھے بخار ہے۔", "I have fever.",
     "मुझे बुख़ार है।", "p0", True),
    ("COUGH", ["COUGH"],
     "مجھے کھانسی ہے۔", "I have a cough.",
     "मुझे खाँसी है।", "p0", False),
    ("VOMITING", ["VOMITING"],
     "مجھے قے آ رہی ہے۔", "I am vomiting.",
     "मुझे क़ै आ रही है।", "p0", False),
    ("DIZZINESS", ["DIZZINESS"],
     "مجھے چکر آ رہے ہیں۔", "I feel dizzy.",
     "मुझे चक्कर आ रहे हैं।", "p0", False),
    ("BREATHING_PROBLEM", ["BREATHING_PROBLEM"],
     "مجھے سانس لینے میں مشکل ہو رہی ہے۔", "I am having difficulty breathing.",
     "मुझे साँस लेने में मुश्किल हो रही है।", "p0", True),
    ("BLEEDING", ["BLEEDING"],
     "مجھے خون آ رہا ہے۔", "I am bleeding.",
     "मुझे ख़ून आ रहा है।", "p0", False),
    ("NEED_HELP", ["HELP"],
     "مجھے مدد چاہیے۔", "I need help.",
     "मुझे मदद चाहिए।", "p0", False),
    # --- answers, required by the demo script ---
    ("YES", ["YES"], "جی ہاں۔", "Yes.", "जी हाँ।", "p0", True),
    ("NO", ["NO"], "جی نہیں۔", "No.", "जी नहीं।", "p0", True),
    # --- bounded duration combinations (MESSAGE_MAP §4) ---
    ("CHEST_PAIN_TWO_DAYS", ["CHEST_PAIN", "TWO", "DAY"],
     "مجھے دو دن سے سینے میں درد ہے۔", "I have had chest pain for two days.",
     "मुझे दो दिन से सीने में दर्द है।", "p0", True),
    ("FEVER_TWO_DAYS", ["FEVER", "TWO", "DAY"],
     "مجھے دو دن سے بخار ہے۔", "I have had fever for two days.",
     "मुझे दो दिन से बुख़ार है।", "p0", True),
    # --- P1 ---
    ("EYE_PAIN", ["EYE_PAIN"],
     "میری آنکھ میں درد ہے۔", "My eye hurts.",
     "मेरी आँख में दर्द है।", "p1", False),
    ("BACK_PAIN", ["BACK_PAIN"],
     "میری کمر میں درد ہے۔", "My back hurts.",
     "मेरी कमर में दर्द है।", "p1", False),
    ("WEAKNESS", ["WEAKNESS"],
     "مجھے کمزوری محسوس ہو رہی ہے۔", "I feel weak.",
     "मुझे कमज़ोरी महसूस हो रही है।", "p1", False),
    ("INJURY", ["INJURY"],
     "مجھے چوٹ لگی ہے۔", "I have an injury.",
     "मुझे चोट लगी है।", "p1", False),
    ("ALLERGY", ["ALLERGY"],
     "مجھے الرجی ہے۔", "I have an allergy.",
     "मुझे एलर्जी है।", "p1", False),
]

# --------------------------------------------------------------- doctor phrases
# (code, urdu_meaning, english_meaning, sort_order)

CATEGORIES: list[tuple[str, str, str, int]] = [
    ("basic", "Basic", "بنیادی", 1),
    ("pain", "Pain", "درد", 2),
    ("symptoms", "Symptoms", "علامات", 3),
    ("medical", "Medical", "طبی", 4),
]

# (code, category, urdu, english, priority, demo_critical, sort, stt_aliases)
DOCTOR_PHRASES: list[tuple[str, str, str, str, str, bool, int, list[str]]] = [
    ("DOCTOR_UNDERSTAND", "basic", "کیا آپ سمجھ گئے؟", "Do you understand?",
     "p0", False, 1, ["کیا آپ سمجھ گئے", "سمجھ آیا", "samajh gaye"]),
    ("DOCTOR_WAIT_HERE", "basic", "براہِ کرم یہاں انتظار کریں۔", "Please wait here.",
     "p0", False, 2, ["یہاں انتظار کریں", "انتظار کریں", "wait karein"]),

    ("DOCTOR_WHERE_PAIN", "pain", "درد کہاں ہے؟", "Where is the pain?",
     "p0", False, 1, ["درد کہاں ہے", "کہاں درد ہے", "dard kahan hai"]),
    ("DOCTOR_SINCE_WHEN", "pain", "کب سے؟", "Since when?",
     "p0", True, 2, ["کب سے", "کتنے دن سے", "kab se"]),
    ("DOCTOR_PAIN_SEVERE", "pain", "کیا درد شدید ہے؟", "Is the pain severe?",
     "p0", False, 3, ["کیا درد شدید ہے", "درد زیادہ ہے", "dard shadeed hai"]),

    ("DOCTOR_FEVER", "symptoms", "کیا آپ کو بخار ہے؟", "Do you have fever?",
     "p0", False, 1, ["کیا آپ کو بخار ہے", "بخار ہے", "bukhar hai"]),
    ("DOCTOR_COUGH", "symptoms", "کیا آپ کو کھانسی ہے؟", "Do you have a cough?",
     "p0", False, 2, ["کیا آپ کو کھانسی ہے", "کھانسی ہے", "khansi hai"]),
    ("DOCTOR_VOMITING", "symptoms", "کیا آپ کو قے آ رہی ہے؟", "Are you vomiting?",
     "p0", False, 3, ["کیا آپ کو قے آ رہی ہے", "قے آ رہی ہے", "ulti aa rahi hai"]),
    ("DOCTOR_DIZZY", "symptoms", "کیا آپ کو چکر آ رہے ہیں؟", "Do you feel dizzy?",
     "p0", False, 4, ["کیا آپ کو چکر آ رہے ہیں", "چکر آ رہے ہیں", "chakkar aa rahe hain"]),
    ("DOCTOR_BREATHING_DIFFICULTY", "symptoms", "کیا سانس لینے میں مشکل ہے؟",
     "Difficulty breathing?", "p0", True, 5,
     ["کیا سانس لینے میں مشکل ہے", "سانس لینے میں مشکل", "saans lene mein mushkil"]),

    ("DOCTOR_ALLERGY", "medical", "کیا آپ کو کسی دوا سے الرجی ہے؟",
     "Allergic to any medicine?", "p1", False, 1,
     ["کیا آپ کو کسی دوا سے الرجی ہے", "الرجی ہے", "allergy hai"]),
    ("DOCTOR_TAKEN_MEDICINE", "medical", "کیا آپ نے کوئی دوا لی ہے؟",
     "Have you taken any medicine?", "p1", False, 2,
     ["کیا آپ نے کوئی دوا لی ہے", "دوا لی ہے", "dawa li hai"]),
    ("DOCTOR_INJURY", "medical", "کیا آپ کو چوٹ لگی ہے؟", "Did you have an injury?",
     "p1", False, 3, ["کیا آپ کو چوٹ لگی ہے", "چوٹ لگی ہے", "chot lagi hai"]),
    ("DOCTOR_NEED_TEST", "medical", "ہمیں ٹیسٹ کرنا ہوگا۔", "We need to perform a test.",
     "p1", False, 4, ["ہمیں ٹیسٹ کرنا ہوگا", "ٹیسٹ کرنا ہوگا", "test karna hoga"]),
    ("DOCTOR_TAKE_MEDICINE", "medical", "یہ دوا لیں۔", "Take this medicine.",
     "p1", False, 5, ["یہ دوا لیں", "دوا لیں", "yeh dawa lein"]),
]

# --------------------------------------------------------------- settings

DEFAULT_SETTINGS: dict[str, object] = {
    "primary_output_language": "urdu",
    "english_text_enabled": False,
    "english_speech_enabled": False,
    "tts_voice": "",
    "overlay_enabled": False,
    "doctor_voice_input_enabled": False,
    "stt_provider": "groq",
}

# Initial recognition thresholds. These are STARTING POINTS, not measurements.
# Real values come from Day-1 calibration and are frozen before the T4
# unseen-person test (D026).
INITIAL_RECOGNITION_CONFIG = {
    "tau_accept": 0.55,
    "delta_margin": 0.15,
    "sigma": 0.35,
    "band_width_pct": 15,
    "p_absent": 0.35,
    "notes": "Initial values from docs/RECOGNITION_SPEC.md. NOT calibrated. NOT frozen.",
}
