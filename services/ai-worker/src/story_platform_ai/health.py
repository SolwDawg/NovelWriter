def health_payload() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ai-worker",
        "version": "0.1.0",
    }
