from flask import current_app
from flask_mail import Message, Mail
from flask_login import current_user

mail = Mail()


def send_mail(subject, body):
    """로그인한 사용자의 이메일로 메일을 보냄"""
    msg = Message(
        subject=subject,
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[current_user.email]  # 현재 로그인한 사용자의 이메일
    )
    msg.body = body
    mail.send(msg)


def send_training_complete_email():
    """학습이 완료되었을 때 이메일 전송"""
    subject = "학습 완료 알림"
    body = "모델의 학습이 완료되었습니다."
    send_mail(subject, body)


def send_inference_complete_email():
    """추론이 완료되었을 때 이메일 전송"""
    subject = "추론 완료 알림"
    body = "모델의 추론이 완료되었습니다."
    send_mail(subject, body)
