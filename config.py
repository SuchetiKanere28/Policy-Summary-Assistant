import os
import platform

class Config:
    """
    Configuration settings for Policy Summary Assistant.
    Tuned for academic-style summarization and insurance document analysis.
    """

    # ---------------------------
    # 🔹 Model settings
    # ---------------------------
    SUMMARY_MODEL = "sshleifer/distilbart-cnn-12-6"
    MAX_TOKENS = 1024                             # Maximum tokens for model inference
    TIMEOUT_SECONDS = 30                          # Timeout limit for async operations
    USE_GPU_IF_AVAILABLE = True                   # Use GPU acceleration if CUDA available

    # ---------------------------
    # 🔹 Summary configuration
    # ---------------------------
    TARGET_WORDS = 500                            # Desired final word count
    MIN_SUMMARY_LENGTH = 450                      # Minimum acceptable summary size
    MAX_SUMMARY_LENGTH = 550                      # Maximum acceptable summary size
    SECTION_SUMMARY_LENGTH = 150                  # For per-section summarization

    # ---------------------------
    # 🔹 File processing
    # ---------------------------
    # Overlap between chunks for continuity
    CHUNK_SIZE = 400
    CHUNK_OVERLAP = 20
    MAX_FILE_SIZE_MB = 50                         # File size limit
    ENABLE_CACHING = True                         # Cache model between runs

    # ---------------------------
    # 🔹 NLP & Analysis thresholds
    # ---------------------------
    SENTIMENT_THRESHOLD_POS = 0.2                 # Positive sentiment threshold
    SENTIMENT_THRESHOLD_NEG = -0.2                # Negative sentiment threshold
    READABILITY_TARGET = 60.0                     # Target Flesch score for clear writing

    # ---------------------------
    # 🔹 Policy Section Detection
    # ---------------------------
    SECTION_TITLES = [
        "LOSS OF OR DAMAGE TO YOUR VEHICLE",
        "YOUR LIABILITY",
        "OPTIONAL COVER LIMITS",
        "POLICY COVERAGE",
        "EXCLUSIONS",
        "CLAIMS PROCEDURE",
        "GENERAL CONDITIONS",
        "ENDORSEMENTS",
        "RENEWAL TERMS"
    ]

    # ---------------------------
    # 🔹 Platform-specific
    # ---------------------------
    IS_WINDOWS = platform.system() == "Windows"

# Global config object
config = Config()
