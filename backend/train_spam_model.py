"""
Training pipeline for the SmartShield AI Spam Detection Model.
Trains a TF-IDF Vectorizer + Logistic Regression classifier on the
canonical UCI SMS Spam Collection dataset with augmented modern phishing/scam patterns.
"""

import io
import os
import urllib.request
import zipfile
from pathlib import Path
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split

MODELS_DIR = Path(__file__).resolve().parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODELS_DIR / "spam_detector_model.joblib"
VECTORIZER_PATH = MODELS_DIR / "spam_vectorizer.joblib"

# Additional modern cyber security scam & phishing samples to augment standard dataset
MODERN_SAMPLES = [
    ("spam", "URGENT: Your bank account has been temporarily locked due to suspicious activity. Verify credentials at http://secure-login-bank-update.xyz or call immediately."),
    ("spam", "Your package delivery #US948271 is on hold due to unpaid customs fee of $2.99. Pay within 24 hours at http://track-parcel-usps.click to avoid return."),
    ("spam", "IRS Final Notice: An arrest warrant has been issued in your name for tax fraud. Pay your settlement fee using Apple gift cards or Bitcoin immediately."),
    ("spam", "Congratulations! You have been selected for a $1,000 Walmart gift card. Click bit.ly/claim-card-now to claim your prize today!"),
    ("spam", "Verify your crypto wallet immediately. Unauthorized withdrawal of 0.85 BTC detected. Cancel transaction at http://meta-mask-verify.xyz/auth."),
    ("spam", "Your Netflix membership has expired. Update your billing card details now to keep streaming: http://netflix-billing-renew.top."),
    ("spam", "Security Alert: New sign-in detected on your account from Russia. If this wasn't you, reset your password and send OTP immediately."),
    ("spam", "Hello dear, I am barrister Johnson representing late client estate of $10.5M USD. Reply with full bank details and passport for wire transfer processing."),
    ("spam", "URGENT NOTICE: Your Social Security Number has been suspended. Call our agents immediately or face immediate legal prosecution."),
    ("spam", "Work from home making $500/day rating products! No experience needed, instant deposit via CashApp or Telegram @payfast."),
    ("ham", "Hey, are we still meeting for lunch at 12:30 today? Let me know!"),
    ("ham", "The project report has been uploaded to the shared Google Drive folder. Please review before tomorrow's standup."),
    ("ham", "Can you pick up milk and bread on your way home? Thanks love."),
    ("ham", "Your doctor appointment is confirmed for Thursday at 3:00 PM with Dr. Smith. Reply C to confirm or R to reschedule."),
    ("ham", "Hi team, please find attached the meeting minutes and action items from today's sprint planning session."),
    ("ham", "Dad's birthday dinner is at the Italian place downtown at 7 PM on Saturday."),
    ("ham", "Your flight UA 492 to Chicago is on time. Gate departure B14 at 4:15 PM."),
    ("ham", "I've sent the code review feedback on PR #104. Mostly minor formatting comments."),
    ("ham", "Thanks for your help with the presentation yesterday, everyone loved it!"),
    ("ham", "Reminder: Library books are due next Tuesday. You can renew online anytime."),
]


def load_dataset():
    """Fetches and parses the canonical SMS Spam Collection dataset (5574 real labeled messages)."""
    urls = [
        "https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv",
        "https://raw.githubusercontent.com/mohitgupta-omg/Kaggle-SMS-Spam-Collection-Dataset-/master/spam.csv",
    ]
    texts = []
    labels = []

    for url in urls:
        try:
            print(f"Downloading SMS Spam Collection from {url}...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
                for line in content.strip().split("\n"):
                    line = line.strip()
                    if "\t" in line:
                        parts = line.split("\t", 1)
                        lbl = parts[0].strip().lower()
                        txt = parts[1].strip()
                        if lbl in ("ham", "spam") and txt:
                            labels.append(lbl)
                            texts.append(txt)
            if len(texts) > 1000:
                print(f"Successfully loaded {len(texts)} samples.")
                break
        except Exception as e:
            print(f"Download failed for {url}: {e}")

    # Augment with modern samples
    for label, text in MODERN_SAMPLES:
        labels.append(label)
        texts.append(text)

    return texts, labels


def train():
    texts, labels = load_dataset()
    if len(texts) < 10:
        raise RuntimeError("Insufficient training data available.")

    print(f"Total training dataset size: {len(texts)} (Spam: {labels.count('spam')}, Ham: {labels.count('ham')})")

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
        max_features=8000,
    )

    print("Fitting TF-IDF Vectorizer...")
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    print("Training Logistic Regression classifier...")
    model = LogisticRegression(C=2.0, max_iter=500, class_weight="balanced", random_state=42)
    model.fit(X_train_vec, y_train)

    y_pred = model.predict(X_test_vec)
    f1 = f1_score(y_test, y_pred, pos_label="spam")
    print(f"Validation F1-score (spam): {f1:.4f}")
    print("\nClassification Report:\n", classification_report(y_test, y_pred))

    # Persist model and vectorizer
    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    print(f"Model saved to: {MODEL_PATH}")
    print(f"Vectorizer saved to: {VECTORIZER_PATH}")

    # Test sample inference
    test_samples = [
        "URGENT: Claim your $500 Amazon voucher at http://gift-claim.xyz now!",
        "Hey, don't forget to bring the keys when you leave the office.",
    ]
    for sample in test_samples:
        feat = vectorizer.transform([sample])
        pred = model.predict(feat)[0]
        prob = model.predict_proba(feat)[0]
        spam_prob = prob[list(model.classes_).index("spam")]
        print(f"Sample: '{sample}' -> Prediction: {pred} (Spam probability: {spam_prob:.2%})")


if __name__ == "__main__":
    train()
