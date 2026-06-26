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

        # Register the reevaluation module as a Blueprint
        from reevaluation_time_exercise.app import bp as reeval_bp
        app.register_blueprint(reeval_bp, url_prefix="/reeval")

    # Prevent APScheduler from running twice with Flask auto reloader or Gunicorn workers
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        import socket
        try:
            # Bind to a local port to ensure only one worker starts the scheduler
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("127.0.0.1", 47200))
        except socket.error:
            app.logger.info("Scheduler already started in another worker.")
        else:
            scheduler = BackgroundScheduler()
            # Run every Monday at 05:00 AM
            scheduler.add_job(func=job_generate_weekly_report, trigger="cron", day_of_week='mon', hour=5, minute=0)
            scheduler.start()

    return app
