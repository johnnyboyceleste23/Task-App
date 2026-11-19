from app import app, my_background_task

if __name__ == "__main__":
    with app.app_context():
        my_background_task()