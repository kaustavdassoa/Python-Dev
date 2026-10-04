
try:
    from paperbanana import PaperBananaPipeline
    print("PaperBananaPipeline import successful")
except ImportError as e:
    print(f"PaperBananaPipeline import failed: {e}")

try:
    from paperbanana import PaperBanana
    print("PaperBanana import successful")
except ImportError as e:
    print(f"PaperBanana import failed: {e}")
