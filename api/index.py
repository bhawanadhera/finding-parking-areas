from app import app

# Vercel handler
def handler(environ, start_response):
    return app(environ, start_response)
