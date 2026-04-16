from flask import Flask
import config
from apscheduler.schedulers.background import BackgroundScheduler
from backend.scheduler import job_generate_weekly_report
import os

def create_app():
    app = Flask(__name__)
    app.config["UPLOAD_FOLDER"] = "data/uploads"
    app.secret_key = config.SECRET_KEY

    with app.app_context():
        from .routes import register_routes
        register_routes(app)

    # Prevent APScheduler from running twice with Flask auto reloader
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        scheduler = BackgroundScheduler()
        # Run every Monday at 05:00 AM
        scheduler.add_job(func=job_generate_weekly_report, trigger="cron", day_of_week='mon', hour=5, minute=0)
        scheduler.start()

    return app
