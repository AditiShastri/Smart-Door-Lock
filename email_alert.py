import smtplib
import cv2
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText

def send_email(receiver_email, subject, body, image=None):
    sender_email = "stopspammingaditi@gmail.com"
    app_password = "cggs zykk bacp icyb"  # 🔒 Replace with Gmail app password

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)

            if image is not None:
                _, img_encoded = cv2.imencode('.jpg', image)
                img_bytes = img_encoded.tobytes()

                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = receiver_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))

                part = MIMEBase('application', 'octet-stream')
                part.set_payload(img_bytes)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="intruder.jpg"')
                msg.attach(part)

                server.sendmail(sender_email, receiver_email, msg.as_string())
            else:
                # Send plain text if no image
                message = f"Subject: {subject}\n\n{body}"
                server.sendmail(sender_email, receiver_email, message)

        print("[EMAIL] Alert sent successfully.")

    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
