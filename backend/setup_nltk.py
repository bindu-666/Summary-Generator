import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download required NLTK data
print("Downloading NLTK punkt_tab data...")
nltk.download('punkt_tab', download_dir='./nltk_data')
print("NLTK punkt_tab data downloaded successfully!") 