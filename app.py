import os
from datetime import datetime
from flask import Flask, flash, redirect, url_for, render_template, current_app
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.security import generate_password_hash

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
csrf = CSRFProtect()
cors = CORS()
mail = Mail()

def create_app(config=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configure application
    configure_app(app, config)
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Configure logging
    configure_logging(app)
    
    # Register blueprints/routes
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Initialize database
    with app.app_context():
        initialize_database(app)
    
    return app

def configure_app(app, config):
    """Load application configuration"""
    # Verify required environment variables
    required_env_vars = ['MAIL_USERNAME', 'MAIL_PASSWORD', 'FLASK_SECRET_KEY']
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Base Configuration
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 
            f"sqlite:///{os.path.join(app.instance_path, 'app.db')}"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=os.environ['FLASK_SECRET_KEY'],
        MAIL_SERVER=os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
        MAIL_PORT=int(os.environ.get('MAIL_PORT', 587)),
        MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true',
        MAIL_USERNAME=os.environ['MAIL_USERNAME'],
        MAIL_PASSWORD=os.environ['MAIL_PASSWORD'],
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER', os.environ['MAIL_USERNAME']),
        RECIPIENT_EMAIL=os.environ.get('RECIPIENT_EMAIL'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB upload limit
    )

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

def initialize_extensions(app):
    """Initialize Flask extensions"""
    db.init_app(app)
    csrf.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})  # Restrict in production
    mail.init_app(app)

def configure_logging(app):
    """Configure application logging"""
    if not app.debug:
        # Production logging
        handler = RotatingFileHandler(
            os.path.join(app.instance_path, 'error.log'),
            maxBytes=1024 * 1024,  # 1MB
            backupCount=5
        )
        handler.setLevel(logging.ERROR)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.ERROR)

def register_blueprints(app):
    """Register application blueprints"""
    # Main routes
    @app.route('/')
    def home():
        try:
            featured_products = Product.query.filter_by(is_featured=True).limit(4).all()
            return render_template('home.html',
                               active_page='home',
                               current_year=datetime.now().year,
                               company_name="Mesopotamia Solar",
                               featured_products=featured_products)
        except Exception as e:
            current_app.logger.error(f"Home route error: {e}", exc_info=True)
            return render_template('error.html'), 500

    @app.route('/about')
    def about():
        return render_template('about.html',
                            active_page='about',
                            current_year=datetime.now().year,
                            company_name="Mesopotamia Solar")

    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        form = ContactForm()
        if form.validate_on_submit():
            recipient = current_app.config.get('RECIPIENT_EMAIL')
            if not recipient:
                flash("Recipient email not configured!", "danger")
                current_app.logger.error("Recipient email not configured")
                return redirect(url_for('contact'))
                
            try:
                msg = Message(
                    subject="New Contact Form Submission - Mesopotamia Solar",
                    recipients=[recipient],
                    body=render_template('email/contact.txt',
                                       form=form.data),
                    html=render_template('email/contact.html',
                                       form=form.data)
                )
                mail.send(msg)
                flash("Your message has been sent successfully!", "success")
                current_app.logger.info("Contact form submitted successfully")
            except Exception as e:
                current_app.logger.error(f"Mail sending failed: {e}", exc_info=True)
                flash("Failed to send message. Please try again later.", "danger")
            return redirect(url_for('contact'))

        return render_template('contact.html',
                            form=form,
                            active_page='contact',
                            current_year=datetime.now().year,
                            company_name="Mesopotamia Solar")

def register_error_handlers(app):
    """Register error handlers"""
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        current_app.logger.error(f"500 error: {e}", exc_info=True)
        return render_template('errors/500.html'), 500

def initialize_database(app):
    """Initialize database"""
    try:
        db.create_all()
        app.logger.info("Database tables created successfully")
    except Exception as e:
        app.logger.error(f"Database creation error: {e}", exc_info=True)
        raise

# Models
class Product(db.Model):
    """Product model"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Product {self.name}>'

# Forms
class ContactForm(FlaskForm):
    """Contact form with validation"""
    name = StringField('Your Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    email = StringField('Your Email', validators=[
        DataRequired(message="Email is required!"),
        Email(message="Invalid email address!"),
        Length(max=120)
    ])
    message = TextAreaField('Your Message', validators=[
        DataRequired(),
        Length(min=10, max=2000)
    ])
    submit = SubmitField('Send')

# Application Factory
app = create_app()

if __name__ == "__main__":
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=debug,
        use_reloader=debug
    )
