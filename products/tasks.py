import logging
from io import BytesIO

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from accounts.models import CustomUser

from .models import Order, OrderItem, Purchase

logger = logging.getLogger(__name__)


@shared_task
def generate_and_send_receipt_email(purchase_id):
    try:
        # Get the purchase object
        purchase = Purchase.objects.select_related(
            "order", "order__customer", "order__shipping_address"
        ).get(id=purchase_id)

        # Check if purchase is completed
        if purchase.status != "completed":
            logger.warning(
                f"Attempted to generate receipt for non-completed purchase: {purchase_id}"
            )
            return False

        # Generate PDF receipt
        pdf_buffer = generate_pdf_receipt(purchase)

        # Prepare email content
        subject = f"Receipt for Your Purchase #{purchase.transaction_reference}"
        recipient_email = purchase.order.customer.email

        # Render email body
        email_body = render_to_string(
            "receipt_email.html",
            {
                "purchase": purchase,
                "order": purchase.order,
                "customer": purchase.order.customer,
            },
        )

        # Send email with PDF attachment
        send_mail(
            subject=subject,
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=email_body,
            fail_silently=False,
            attachments=[
                (
                    f"receipt_{purchase.transaction_reference}.pdf",
                    pdf_buffer.getvalue(),
                    "application/pdf",
                )
            ],
        )

        logger.info(f"Receipt email sent successfully for purchase: {purchase_id}")
        return True

    except Purchase.DoesNotExist:
        logger.error(f"Purchase with ID {purchase_id} does not exist")
        return False
    except Exception as e:
        logger.error(
            f"Error generating and sending receipt for purchase {purchase_id}: {str(e)}"
        )
        return False


def generate_pdf_receipt(purchase):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch
    )

    elements = []

    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        spaceAfter=30,
        alignment=1,
        textColor=colors.darkblue,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkgreen,
    )

    # Title
    title = Paragraph("PURCHASE RECEIPT", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Company info
    company_info = [
        Paragraph("<b>ALX E-Commerce Platform</b>", styles["Normal"]),
        Paragraph("123, Damas", styles["Normal"]),
        Paragraph("Yaounde, Cameroon", styles["Normal"]),
        Paragraph("Email: support@alx-ecommerce.com", styles["Normal"]),
        Paragraph("Phone: +237-681-985-010", styles["Normal"]),
    ]

    for info in company_info:
        elements.append(info)

    elements.append(Spacer(1, 20))

    # Customer and purchase details
    details_data = [
        [
            Paragraph("<b>Purchase Date:</b>", styles["Normal"]),
            Paragraph(
                str(purchase.purchase_date.strftime("%Y-%m-%d %H:%M:%S")),
                styles["Normal"],
            ),
        ],
        [
            Paragraph("<b>Transaction Reference:</b>", styles["Normal"]),
            Paragraph(purchase.transaction_reference, styles["Normal"]),
        ],
        [
            Paragraph("<b>Payment Provider:</b>", styles["Normal"]),
            Paragraph(purchase.provider, styles["Normal"]),
        ],
        [
            Paragraph("<b>Total Amount:</b>", styles["Normal"]),
            Paragraph(f"{purchase.amount} {purchase.currency}", styles["Normal"]),
        ],
        [
            Paragraph("<b>Status:</b>", styles["Normal"]),
            Paragraph(purchase.status.title(), styles["Normal"]),
        ],
    ]

    details_table = Table(details_data, colWidths=[2 * inch, 3 * inch])
    details_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(details_table)
    elements.append(Spacer(1, 20))

    # Customer Information
    elements.append(Paragraph("CUSTOMER INFORMATION", heading_style))

    customer_data = [
        [
            Paragraph("<b>Name:</b>", styles["Normal"]),
            Paragraph(
                f"{purchase.order.customer.first_name} {purchase.order.customer.last_name}",
                styles["Normal"],
            ),
        ],
        [
            Paragraph("<b>Email:</b>", styles["Normal"]),
            Paragraph(purchase.order.customer.email, styles["Normal"]),
        ],
        [
            Paragraph("<b>Shipping Address:</b>", styles["Normal"]),
            Paragraph(
                f"{purchase.order.shipping_address.street}, {purchase.order.shipping_address.city}, {purchase.order.shipping_address.state}, {purchase.order.shipping_address.country}",
                styles["Normal"],
            ),
        ],
    ]

    customer_table = Table(customer_data, colWidths=[2 * inch, 3 * inch])
    customer_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(customer_table)
    elements.append(Spacer(1, 20))

    # Order Items
    elements.append(Paragraph("ORDER ITEMS", heading_style))

    # Table header
    item_header = ["Product Name", "Quantity", "Unit Price", "Subtotal"]
    item_data = [item_header]

    # Add order items
    for item in purchase.order.items.all():
        item_data.append(
            [
                Paragraph(item.product.name, styles["Normal"]),
                str(item.quantity),
                f"{item.unit_price_at_purchase} {purchase.currency}",
                f"{item.subtotal} {purchase.currency}",
            ]
        )

    # Add total row
    item_data.append(
        ["", "", "<b>TOTAL</b>", f"<b>{purchase.amount} {purchase.currency}</b>"]
    )

    # Create table
    item_table = Table(item_data, colWidths=[2 * inch, 1 * inch, 1.2 * inch, 1 * inch])
    item_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    elements.append(item_table)
    elements.append(Spacer(1, 20))

    # Thank you message
    thank_you = Paragraph(
        "Thank you for your purchase! We appreciate your business and hope you enjoy your items. "
        "If you have any questions about your order, please contact our customer service team.",
        styles["Normal"],
    )
    elements.append(thank_you)
    elements.append(Spacer(1, 20))

    # Terms and conditions
    terms = Paragraph(
        "<b>Terms and Conditions:</b><br/>"
        "• This receipt serves as proof of purchase.<br/>"
        "• All sales are final unless covered by our return policy.<br/>"
        "• For returns or exchanges, please contact us within 30 days of purchase.",
        styles["Normal"],
    )
    elements.append(terms)

    # Build PDF
    doc.build(elements)

    # Move to the beginning of the buffer
    buffer.seek(0)

    return buffer
