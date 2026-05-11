"""
ZOZAPRIME Ticket Service
========================
Location: events/ticket_service.py (NEW FILE)

Handles all post-payment ticket operations:
- HMAC-SHA256 signed QR code generation
- Branded ticket image generation (1200x600)
- Email delivery with QR + ticket image attachments

REQUIREMENTS:
  Add to requirements.txt: qrcode[pil]==7.4.2
  (Pillow is already in your requirements)

CALLED BY:
  payments/services.py → _create_ticket_from_txn() calls send_ticket_email()
  payments/views.py → ticket_confirmation() calls get_ticket_qr_base64()
"""
import io
import hmac
import hashlib
import base64
import logging
from datetime import datetime

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# QR CODE GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_ticket_qr_data(ticket):
    """
    Generate a tamper-proof QR code payload for a ticket.
    
    Format: ZOZA:{ticket_code}:{event_id}:{quantity}:{signature}
    
    The signature is HMAC-SHA256 of the payload using Django's SECRET_KEY,
    so counterfeit QR codes can be detected instantly at the gate.
    The scanner can verify offline without hitting the database.
    """
    payload = f"{ticket.ticket_code}:{ticket.event_id}:{ticket.quantity}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()[:16]  # First 16 chars is enough for verification
    return f"ZOZA:{payload}:{signature}"


def generate_qr_image(data, box_size=10, border=2):
    """
    Generate a QR code image as a BytesIO buffer (PNG format).
    
    Args:
        data: String to encode in the QR code
        box_size: Size of each QR module in pixels (default 10)
        border: Border width in QR modules (default 2)
    
    Returns:
        BytesIO containing PNG image, or None if qrcode library not installed
    """
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_H
        
        qr = qrcode.QRCode(
            version=None,           # Auto-detect size
            error_correction=ERROR_CORRECT_H,  # 30% error correction (survives damage)
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create image — black modules on white background for maximum scan reliability
        img = qr.make_image(
            fill_color="#0A0A0A",     # ZOZA black
            back_color="#FFFFFF",     # White for scanability
        )
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
        
    except ImportError:
        logger.warning("[QR] qrcode library not installed. Run: pip install qrcode[pil]")
        return None
    except Exception as e:
        logger.error(f"[QR] Generation error: {str(e)}")
        return None


def get_ticket_qr_base64(ticket):
    """
    Generate QR code and return as base64 data URI string.
    Used in templates: <img src="{{ qr_code }}">
    
    Returns:
        String like "data:image/png;base64,iVBOR..." or empty string on failure
    """
    try:
        qr_data = generate_ticket_qr_data(ticket)
        qr_buf = generate_qr_image(qr_data, box_size=8, border=2)
        if qr_buf:
            qr_buf.seek(0)
            b64 = base64.b64encode(qr_buf.read()).decode('utf-8')
            return f"data:image/png;base64,{b64}"
    except Exception as e:
        logger.error(f"[QR BASE64] Error: {str(e)}")
    return ""


# ═══════════════════════════════════════════════════════════════════════════════
# TICKET IMAGE GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_ticket_image(ticket, qr_buffer=None):
    """
    Generate a branded ZOZAPRIME ticket image (1200x600 JPEG).
    
    Layout:
    - Left side: ZOZAPRIME branding, event details, ticket code
    - Right side: QR code with "SCAN TO ENTER" label
    - Bottom bar: zozaprime.com footer
    
    Args:
        ticket: Ticket model instance
        qr_buffer: BytesIO with QR code PNG (optional)
    
    Returns:
        BytesIO containing JPEG image, or None on failure
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Ticket dimensions
        W = 1200
        H = 600
        
        # Create base image with ZOZA black background
        img = Image.new('RGB', (W, H), '#0A0A0A')
        draw = ImageDraw.Draw(img)
        
        # ── Load fonts (DejaVu is available on Render/Linux) ──
        def load_font(name, size):
            """Try multiple font paths, fallback to default."""
            paths = [
                f"/usr/share/fonts/truetype/dejavu/{name}.ttf",
                f"/usr/share/fonts/truetype/liberation/Liberation{name}.ttf",
                f"/usr/share/fonts/TTF/{name}.ttf",
            ]
            for path in paths:
                try:
                    return ImageFont.truetype(path, size)
                except (OSError, IOError):
                    continue
            return ImageFont.load_default()
        
        font_brand = load_font("DejaVuSans-Bold", 26)
        font_title = load_font("DejaVuSans-Bold", 34)
        font_label = load_font("DejaVuSans", 16)
        font_value = load_font("DejaVuSans", 20)
        font_code = load_font("DejaVuSansMono-Bold", 30)
        font_footer = load_font("DejaVuSans", 14)
        
        # ── Top accent bar (coral red) ──
        draw.rectangle([0, 0, W, 5], fill='#F05252')
        
        # ── ZOZAPRIME branding ──
        draw.text((40, 25), "ZOZAPRIME", fill='#F05252', font=font_brand)
        
        # ── Event title (truncate if too long) ──
        title = ticket.event.title
        if len(title) > 35:
            title = title[:32] + "..."
        draw.text((40, 75), title, fill='#FFFFFF', font=font_title)
        
        # ── Divider line ──
        draw.line([(40, 125), (720, 125)], fill='#333333', width=1)
        
        # ── Event details ──
        cat_name = 'General'
        if ticket.ticket_category:
            cat_name = ticket.ticket_category.name
        
        details = [
            ("DATE", ticket.event.date.strftime('%B %d, %Y \u2022 %I:%M %p')),
            ("VENUE", ticket.event.location[:45]),
            ("TICKET", cat_name),
            ("ATTENDEE", ticket.buyer_name),
            ("QTY", str(ticket.quantity)),
            ("AMOUNT", f"KES {ticket.total_amount:,.0f}"),
        ]
        
        y = 145
        for label, value in details:
            draw.text((40, y), label, fill='#666666', font=font_label)
            draw.text((180, y), value, fill='#FFFFFF', font=font_value)
            y += 36
        
        # ── Ticket code (prominent) ──
        draw.line([(40, y + 8), (720, y + 8)], fill='#333333', width=1)
        draw.text((40, y + 20), "TICKET CODE", fill='#666666', font=font_label)
        draw.text((40, y + 45), ticket.ticket_code, fill='#F05252', font=font_code)
        
        # ── QR code area (right side) ──
        qr_x = 800
        qr_y = 40
        qr_size = 380
        
        # White background for QR
        draw.rectangle(
            [qr_x - 10, qr_y - 10, qr_x + qr_size + 10, qr_y + qr_size + 10],
            fill='#FFFFFF'
        )
        
        # Paste QR code if available
        if qr_buffer:
            qr_buffer.seek(0)
            qr_img = Image.open(qr_buffer)
            qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
            img.paste(qr_img, (qr_x, qr_y))
        
        # "SCAN TO ENTER" label
        draw.text(
            (qr_x + 100, qr_y + qr_size + 15),
            "SCAN TO ENTER",
            fill='#666666',
            font=font_label
        )
        
        # ── Bottom footer bar ──
        draw.rectangle([0, H - 35, W, H], fill='#141414')
        draw.text((40, H - 28), "zozaprime.com", fill='#444444', font=font_footer)
        draw.text(
            (W - 250, H - 28),
            "Powered by ZOZAPRIME",
            fill='#444444',
            font=font_footer
        )
        
        # ── Save to buffer ──
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=95)
        output.seek(0)
        return output
        
    except ImportError:
        logger.error("[TICKET IMG] Pillow not installed")
        return None
    except Exception as e:
        logger.error(f"[TICKET IMG] Generation error: {str(e)}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL DELIVERY
# ═══════════════════════════════════════════════════════════════════════════════

def send_ticket_email(ticket):
    """
    Send ticket confirmation email with QR code and ticket image attached.
    
    Never blocks the purchase flow — if email fails, ticket is still valid.
    
    Attachments:
    1. ZOZAPRIME_Ticket_{code}.jpg — Full branded ticket image with QR
    2. QR_{code}.png — Standalone QR code for easy saving
    
    Args:
        ticket: Ticket model instance
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Generate QR code
        qr_data = generate_ticket_qr_data(ticket)
        qr_buffer = generate_qr_image(qr_data)
        
        # Generate branded ticket image with QR embedded
        ticket_image = generate_ticket_image(ticket, qr_buffer)
        
        # Get category name safely
        cat_name = 'General'
        if ticket.ticket_category:
            cat_name = ticket.ticket_category.name
        
        subject = f"\U0001F3AB Your Ticket \u2014 {ticket.event.title}"
        
        # ── Plain text version (for email clients that don't support HTML) ──
        text_body = f"""Hey {ticket.buyer_name}!

Your ticket for {ticket.event.title} is confirmed!

EVENT DETAILS
-----------------------
Event:    {ticket.event.title}
Date:     {ticket.event.date.strftime('%B %d, %Y at %I:%M %p')}
Venue:    {ticket.event.location}
Ticket:   {cat_name}
Quantity: {ticket.quantity}
Amount:   KES {ticket.total_amount:,.0f}
Code:     {ticket.ticket_code}

IMPORTANT
-----------------------
- Your ticket image is attached to this email
- Show the QR code at the entrance for scanning
- Screenshot this email as backup
- Arrive on time — gates open 30 minutes before the event

See you there!

— ZOZAPRIME
zozaprime.com
"""
        
        # ── HTML version (branded ZOZAPRIME design) ──
        html_body = f"""
<div style="max-width:600px;margin:0 auto;background:#0A0A0A;font-family:Arial,Helvetica,sans-serif;color:#FFFFFF;">
  
  <!-- Header -->
  <div style="padding:24px 32px;border-bottom:3px solid #F05252;">
    <span style="font-size:22px;font-weight:bold;color:#F05252;">ZOZAPRIME</span>
  </div>
  
  <!-- Body -->
  <div style="padding:32px;">
    
    <!-- Success message -->
    <h1 style="font-size:24px;font-weight:bold;margin:0 0 8px;color:#FFFFFF;">Payment Successful!</h1>
    <p style="color:#999999;margin:0 0 24px;font-size:14px;">Your tickets have been confirmed</p>
    
    <!-- Event Details Card -->
    <div style="background:#1A1A1A;border-radius:12px;padding:24px;margin-bottom:20px;">
      <h3 style="color:#F05252;margin:0 0 16px;font-size:14px;text-transform:uppercase;letter-spacing:1px;">Event Details</h3>
      <table style="width:100%;font-size:14px;border-collapse:collapse;">
        <tr>
          <td style="padding:8px 0;color:#888888;">Event</td>
          <td style="padding:8px 0;text-align:right;font-weight:bold;color:#FFFFFF;">{ticket.event.title}</td>
        </tr>
        <tr>
          <td style="padding:8px 0;color:#888888;">Date</td>
          <td style="padding:8px 0;text-align:right;color:#FFFFFF;">{ticket.event.date.strftime('%B %d, %Y \u2022 %I:%M %p')}</td>
        </tr>
        <tr>
          <td style="padding:8px 0;color:#888888;">Venue</td>
          <td style="padding:8px 0;text-align:right;color:#FFFFFF;">{ticket.event.location}</td>
        </tr>
        <tr>
          <td style="padding:8px 0;color:#888888;">Ticket</td>
          <td style="padding:8px 0;text-align:right;color:#FFFFFF;">{cat_name}</td>
        </tr>
        <tr>
          <td style="padding:8px 0;color:#888888;">Quantity</td>
          <td style="padding:8px 0;text-align:right;color:#FFFFFF;">{ticket.quantity}</td>
        </tr>
      </table>
    </div>
    
    <!-- Ticket Code Card -->
    <div style="background:#1A1A1A;border-radius:12px;padding:24px;margin-bottom:20px;text-align:center;">
      <p style="color:#888888;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;">Your Ticket Code</p>
      <p style="font-size:28px;font-weight:bold;color:#F05252;letter-spacing:3px;margin:0;font-family:'Courier New',monospace;">{ticket.ticket_code}</p>
    </div>
    
    <!-- Total Amount -->
    <div style="background:#F05252;border-radius:12px;padding:20px;text-align:center;margin-bottom:20px;">
      <span style="font-size:14px;color:rgba(255,255,255,0.8);">Total Paid</span>
      <div style="font-size:28px;font-weight:bold;color:#FFFFFF;">KES {ticket.total_amount:,.0f}</div>
    </div>
    
    <!-- Important Info -->
    <div style="background:#1A1A1A;border-radius:12px;padding:20px;margin-bottom:20px;">
      <p style="color:#F05252;font-weight:bold;margin:0 0 12px;font-size:14px;">Important Information</p>
      <ul style="color:#999999;font-size:13px;padding-left:20px;margin:0;line-height:2;">
        <li>Your ticket image with QR code is attached to this email</li>
        <li>Show the QR code at the venue entrance for scanning</li>
        <li>Save your ticket code: <strong style="color:#FFFFFF;">{ticket.ticket_code}</strong></li>
        <li>Screenshot this email as backup</li>
        <li>Arrive on time — gates open 30 minutes before</li>
      </ul>
    </div>
    
  </div>
  
  <!-- Footer -->
  <div style="padding:20px 32px;background:#141414;text-align:center;">
    <p style="font-size:12px;color:#444444;margin:0;">
      zozaprime.com \u2022 Kenya's #1 Ticketing Platform
    </p>
  </div>
  
</div>
"""
        
        # ── Create and send email ──
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[ticket.buyer_email],
        )
        email.attach_alternative(html_body, "text/html")
        
        # Attach ticket image (branded, with QR embedded)
        if ticket_image:
            ticket_image.seek(0)
            email.attach(
                f"ZOZAPRIME_Ticket_{ticket.ticket_code}.jpg",
                ticket_image.read(),
                "image/jpeg"
            )
        
        # Attach standalone QR code (so fans can save just the QR)
        if qr_buffer:
            qr_buffer.seek(0)
            email.attach(
                f"QR_{ticket.ticket_code}.png",
                qr_buffer.read(),
                "image/png"
            )
        
        email.send(fail_silently=False)
        
        logger.info(f"[EMAIL] Ticket email sent to {ticket.buyer_email}")
        print(f"[EMAIL] \u2705 Sent to {ticket.buyer_email}")
        return True
        
    except Exception as e:
        logger.error(f"[EMAIL] Failed to send ticket email: {str(e)}")
        print(f"[EMAIL] \u274C Failed: {str(e)}")
        return False