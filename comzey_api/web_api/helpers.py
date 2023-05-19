from django.core.mail import send_mail
from decouple import config



def send_password_reset_email(email, reset_url):
    subject = 'Reset your password'
    message = f'Use the following link to reset your password:\n\n{reset_url}'
    from_email = config('EMAIL_HOST_USER')
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)  