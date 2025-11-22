import resend
from typing import Optional

# Your API Key
resend.api_key = "re_SUV53KzQ_5DKABW69WjsnnCQyXG2c17J7"

class EmailService:
    
    @staticmethod
    def send_order_confirmation_to_customer(customer_email: str, customer_name: str, 
                                           order_id: int, product_name: str, 
                                           quantity: int, total_amount: float):
        """Send order confirmation email to customer"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #10b981; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9fafb; padding: 20px; }}
                .order-details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .button {{ background: #10b981; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Order Confirmed!</h1>
                </div>
                <div class="content">
                    <h2>Hi {customer_name},</h2>
                    <p>Thank you for your order! We're excited to confirm that we've received your order.</p>
                    
                    <div class="order-details">
                        <h3>Order Details:</h3>
                        <p><strong>Order ID:</strong> #{order_id}</p>
                        <p><strong>Product:</strong> {product_name}</p>
                        <p><strong>Quantity:</strong> {quantity}</p>
                        <p><strong>Total Amount:</strong> ₹{total_amount:.2f}</p>
                    </div>
                    
                    <p>We'll notify you once your order is shipped.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Agricultural Products Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            params = {
                "from": "Agricultural Platform <onboarding@resend.dev>",
                "to": [customer_email],
                "subject": f"Order Confirmation - Order #{order_id}",
                "html": html_content,
            }
            response = resend.Emails.send(params)
            print(f"Order confirmation email sent to {customer_email}")
            return response
        except Exception as e:
            print(f"Error sending email to customer: {e}")
            return None

    @staticmethod
    def send_order_notification_to_farmer(farmer_email: str, farmer_name: str,
                                         order_id: int, product_name: str,
                                         quantity: int, customer_name: str,
                                         customer_phone: str):
        """Send new order notification to farmer"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #3b82f6; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9fafb; padding: 20px; }}
                .order-details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📦 New Order Received!</h1>
                </div>
                <div class="content">
                    <h2>Hi {farmer_name},</h2>
                    <p>You have received a new order for your product.</p>
                    
                    <div class="order-details">
                        <h3>Order Details:</h3>
                        <p><strong>Order ID:</strong> #{order_id}</p>
                        <p><strong>Product:</strong> {product_name}</p>
                        <p><strong>Quantity:</strong> {quantity}</p>
                        <p><strong>Customer Name:</strong> {customer_name}</p>
                        <p><strong>Customer Phone:</strong> {customer_phone}</p>
                    </div>
                    
                    <p>Please prepare the order for delivery.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Agricultural Products Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            params = {
                "from": "Agricultural Platform <onboarding@resend.dev>",
                "to": [farmer_email],
                "subject": f"New Order #{order_id} - {product_name}",
                "html": html_content,
            }
            response = resend.Emails.send(params)
            print(f"Order notification email sent to farmer {farmer_email}")
            return response
        except Exception as e:
            print(f"Error sending email to farmer: {e}")
            return None

    @staticmethod
    def send_status_update_to_customer(customer_email: str, customer_name: str,
                                       order_id: int, product_name: str,
                                       old_status: str, new_status: str):
        """Send order status update to customer"""
        status_messages = {
            'processing': 'Your order is being processed.',
            'shipped': 'Your order has been shipped and is on its way!',
            'delivered': 'Your order has been delivered. Enjoy your purchase!',
            'cancelled': 'Your order has been cancelled.'
        }
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #8b5cf6; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9fafb; padding: 20px; }}
                .status-update {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; text-align: center; }}
                .status {{ font-size: 24px; font-weight: bold; color: #10b981; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📢 Order Status Update</h1>
                </div>
                <div class="content">
                    <h2>Hi {customer_name},</h2>
                    <p>Your order status has been updated.</p>
                    
                    <div class="status-update">
                        <p><strong>Order ID:</strong> #{order_id}</p>
                        <p><strong>Product:</strong> {product_name}</p>
                        <p class="status">{new_status.upper()}</p>
                        <p>{status_messages.get(new_status, 'Status updated.')}</p>
                    </div>
                </div>
                <div class="footer">
                    <p>© 2025 Agricultural Products Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            params = {
                "from": "Agricultural Platform <onboarding@resend.dev>",
                "to": [customer_email],
                "subject": f"Order #{order_id} Status Update - {new_status.title()}",
                "html": html_content,
            }
            response = resend.Emails.send(params)
            print(f"Status update email sent to {customer_email}")
            return response
        except Exception as e:
            print(f"Error sending status update email: {e}")
            return None

    @staticmethod
    def send_payment_confirmation(customer_email: str, customer_name: str,
                                  order_id: int, amount: float, payment_id: str):
        """Send payment confirmation to customer"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #10b981; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9fafb; padding: 20px; }}
                .payment-details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .amount {{ font-size: 28px; font-weight: bold; color: #10b981; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Payment Confirmed!</h1>
                </div>
                <div class="content">
                    <h2>Hi {customer_name},</h2>
                    <p>We've received your payment successfully.</p>
                    
                    <div class="payment-details">
                        <h3>Payment Details:</h3>
                        <p><strong>Order ID:</strong> #{order_id}</p>
                        <p><strong>Payment ID:</strong> {payment_id}</p>
                        <p><strong>Amount Paid:</strong></p>
                        <p class="amount">₹{amount:.2f}</p>
                    </div>
                    
                    <p>Thank you for your payment!</p>
                </div>
                <div class="footer">
                    <p>© 2025 Agricultural Products Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            params = {
                "from": "Agricultural Platform <onboarding@resend.dev>",
                "to": [customer_email],
                "subject": f"Payment Confirmation - Order #{order_id}",
                "html": html_content,
            }
            response = resend.Emails.send(params)
            print(f"Payment confirmation email sent to {customer_email}")
            return response
        except Exception as e:
            print(f"Error sending payment confirmation: {e}")
            return None

    @staticmethod
    def send_service_booking_confirmation(customer_email: str, customer_name: str,
                                         booking_id: int, service_name: str,
                                         provider_name: str, booking_date: str):
        """Send service booking confirmation to customer"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #f59e0b; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9fafb; padding: 20px; }}
                .booking-details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔧 Service Booking Confirmed!</h1>
                </div>
                <div class="content">
                    <h2>Hi {customer_name},</h2>
                    <p>Your service booking has been confirmed.</p>
                    
                    <div class="booking-details">
                        <h3>Booking Details:</h3>
                        <p><strong>Booking ID:</strong> #{booking_id}</p>
                        <p><strong>Service:</strong> {service_name}</p>
                        <p><strong>Provider:</strong> {provider_name}</p>
                        <p><strong>Date:</strong> {booking_date}</p>
                    </div>
                    
                    <p>The service provider will contact you soon.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Agricultural Products Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            params = {
                "from": "Agricultural Platform <onboarding@resend.dev>",
                "to": [customer_email],
                "subject": f"Service Booking Confirmation - #{booking_id}",
                "html": html_content,
            }
            response = resend.Emails.send(params)
            print(f"Service booking confirmation sent to {customer_email}")
            return response
        except Exception as e:
            print(f"Error sending service booking confirmation: {e}")
            return None

    @staticmethod
    def send_service_provider_notification(provider_email: str, provider_name: str,
                                          booking_id: int, service_name: str,
                                          customer_name: str, customer_phone: str):
        """Send new booking notification to service provider"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #f59e0b; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9fafb; padding: 20px; }}
                .booking-details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 New Service Booking!</h1>
                </div>
                <div class="content">
                    <h2>Hi {provider_name},</h2>
                    <p>You have received a new service booking.</p>
                    
                    <div class="booking-details">
                        <h3>Booking Details:</h3>
                        <p><strong>Booking ID:</strong> #{booking_id}</p>
                        <p><strong>Service:</strong> {service_name}</p>
                        <p><strong>Customer Name:</strong> {customer_name}</p>
                        <p><strong>Customer Phone:</strong> {customer_phone}</p>
                    </div>
                    
                    <p>Please contact the customer to schedule the service.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Agricultural Products Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            params = {
                "from": "Agricultural Platform <onboarding@resend.dev>",
                "to": [provider_email],
                "subject": f"New Service Booking #{booking_id}",
                "html": html_content,
            }
            response = resend.Emails.send(params)
            print(f"Service provider notification sent to {provider_email}")
            return response
        except Exception as e:
            print(f"Error sending service provider notification: {e}")
            return None


