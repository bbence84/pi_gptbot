import smtplib
import os
from dotenv import load_dotenv
load_dotenv()

#Email Variables
SMTP_SERVER = 'smtp.gmail.com' #Email Server (don't change!)
SMTP_PORT = 587 #Server Port (don't change!)
GMAIL_USERNAME = os.getenv('GMAIL_USERNAME', '') 
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD', '')

class Emailer:
    def sendmail(self, recipient, subject, content):
        if (GMAIL_USERNAME != '' and GMAIL_PASSWORD != ''):
            headers = ["From: " + GMAIL_USERNAME, "Subject: " + subject, "To: " + recipient,
                    "MIME-Version: 1.0", "Content-Type: text/html"]
            headers = "\r\n".join(headers)
            session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            session.ehlo()
            session.starttls()
            session.ehlo()
            session.login(GMAIL_USERNAME, GMAIL_PASSWORD)
            print("Sending email to " + recipient + ".")
            session.sendmail(GMAIL_USERNAME, recipient, headers + "\r\n\r\n" + content)
            session.quit

# if __name__ == "__main__":
#     sender = Emailer()
#     sendTo = 'xxxx@xxxx.com'
#     emailSubject = "Hello World"
#     emailContent = "This is a test of the Emailer Class"
#     sender.sendmail(sendTo, emailSubject, emailContent)