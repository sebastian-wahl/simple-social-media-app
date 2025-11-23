import uvicorn

from social_media_app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "social_media_app.app:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=(settings.APP_ENV == "dev"),
        log_level="info",
        access_log=True,
    )
