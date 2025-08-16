# MailDev Docker container for Fly.io deployment
FROM maildev/maildev:2.0.5

# Expose web interface and SMTP ports
EXPOSE 1080 1025

# Configure MailDev with proper settings for Fly.io
CMD ["bin/maildev", \
     "--web", "1080", \
     "--smtp", "1025", \
     "--hide-extensions", "STARTTLS", \
     "--incoming-user", "", \
     "--incoming-pass", "", \
     "--web-user", "", \
     "--web-pass", ""]
