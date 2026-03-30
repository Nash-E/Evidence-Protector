import os
from flask import Flask, render_template
from api.upload import upload_bp
from api.analyze import analyze_bp
from api.export import export_bp

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = None
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    app.register_blueprint(upload_bp)
    app.register_blueprint(analyze_bp)
    app.register_blueprint(export_bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
