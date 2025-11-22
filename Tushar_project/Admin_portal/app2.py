from sib_api_v3_sdk import Configuration, ApiClient
from sib_api_v3_sdk.api.transactional_emails_api import TransactionalEmailsApi
from sib_api_v3_sdk.models.send_smtp_email import SendSmtpEmail

API_KEY = "d1360b34-66ac-4cf9-93b0-0465f9c370e4"   # Your key

def send_email():
    try:
        # Configure API key
        config = Configuration()
        config.api_key['api-key'] = API_KEY

        api_instance = TransactionalEmailsApi(ApiClient(config))

        # Prepare email
        email = SendSmtpEmail(
            to=[{"email": "deeprajnptel@gmail.com"}],    # Receiver
            sender={"email": "deeprajautade1@gmail.com", "name": "Deepraj"},  # Sender
            subject="Test Email Using Brevo (Student Project)",
            html_content="""
                <h2>Hello!</h2>
                <p>This email is sent using <b>Brevo SMTP API</b>.</p>
                <p>Your student project mail system is working!</p>
            """
        )

        # Send email
        response = api_instance.send_transac_email(email)
        print("Email sent successfully!")
        print(response)

    except Exception as e:
        print("Error:", e)


send_email()
