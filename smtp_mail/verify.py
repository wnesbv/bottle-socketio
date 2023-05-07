
import os, smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv


load_dotenv(dotenv_path=os.getenv("dotenv_path"))
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
FROM = os.getenv("FROM")


def send_mail(self, verify):

    msg = MIMEMultipart()

    message = str(self)

    password = MAIL_PASSWORD
    msg["From"] = FROM
    msg["To"] = verify
    msg["Subject"] = "Subscription"

    msg.attach(MIMEText(message, "plain"))

    server = smtplib.SMTP("smtp.gmail.com: 587")

    server.starttls()

    server.login(msg["From"], password)

    server.sendmail(msg["From"], msg["To"], msg.as_string())

    server.quit()
