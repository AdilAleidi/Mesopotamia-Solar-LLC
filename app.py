import os
from datetime import datetime
from flask import Flask, flash, redirect, url_for, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email
from flask_cors import CORS
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
csrf = CSRFProtect()
cors = CORS()
mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # Verify required environment variables
    required_env_vars = ['MAIL_USERNAME', 'MAIL_PASSWORD', 'FLASK_SECRET_KEY']
    for var in required_env_vars:
        if not os.environ.get(var):
            raise ValueError(f"Missing required environment variable: {var}")

    # App Configuration
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL') or \
            'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance/app.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=os.environ['FLASK_SECRET_KEY'],
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.environ['MAIL_USERNAME'],
        MAIL_PASSWORD=os.environ['MAIL_PASSWORD'],
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER', os.environ['MAIL_USERNAME'])
    )

    # Ensure instance folder exists
    try:
        os.makedirs(os.path.join(app.instance_path))
    except OSError:
        pass

    # Initialize extensions with the app
    db.init_app(app)
    csrf.init_app(app)
    cors.init_app(app)
    mail.init_app(app)

    # Setup logging
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler('error.log', maxBytes=100000, backupCount=3)
        handler.setLevel(logging.ERROR)
        app.logger.addHandler(handler)

    # Register routes
    register_routes(app)

    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Database creation error: {e}")
            raise

    return app


# Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_featured = db.Column(db.Boolean, default=False)


# Forms
class ContactForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired()])
    email = StringField('Your Email', validators=[
        DataRequired(message="Email is required!"),
        Email(message="Invalid email address!")
    ])
    message = TextAreaField('Your Message', validators=[DataRequired()])
    submit = SubmitField('Send')


# Routes
def register_routes(app):
    @app.route('/')
    def home():
        try:
            featured_products = Product.query.filter_by(is_featured=True).all()
            return render_template('home.html',
                                active_page='home',
                                current_year=datetime.now().year,
                                company_name="Mesopotamia Solar",
                                featured_products=featured_products)
        except Exception as e:
            app.logger.error(f"Home route error: {e}")
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
            recipient = os.environ.get('RECIPIENT_EMAIL')
            if not recipient:
                flash("Recipient email not configured!", "danger")
                return redirect(url_for('contact'))
                
            msg = Message(
                "New Contact Form Submission",
                recipients=[recipient],
                body=f"""
                Name: {form.name.data}
                Email: {form.email.data}
                Message: {form.message.data}
                """
            )
            try:
                mail.send(msg)
                flash("Your message has been sent successfully!", "success")
            except Exception as e:
                app.logger.error(f"Mail sending failed: {e}")
                flash("Failed to send message. Please try again later.", "danger")
            return redirect(url_for('contact'))

        return render_template('contact.html',
                            form=form,
                            active_page='contact',
                            current_year=datetime.now().year,
                            company_name="Mesopotamia Solar")

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('500.html'), 500


# Create and run the application
app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')