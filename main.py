from config.env import get_settings

if __name__ == "__main__":

    settings = get_settings()

    print("Environment variables:")
    print(f"Document URL: {settings.DOCUMENT_URL_GOOGLE}")
    print(f"API URL: {settings.API_GOOGLE_URL}")
    print(f"Secret Key: {settings.SECRET_KEY}")
    print("########################")