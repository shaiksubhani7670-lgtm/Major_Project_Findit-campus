"""
FindIt Campus — Email Notification Service
Sends email alerts for match found, claim approved, welcome, and verification events.
Uses Flask-Mail with Gmail SMTP (finditcampus@gmail.com).
"""

import threading
from flask import current_app
from flask_mail import Message
from app import mail


def _send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            print(f"[EmailService] Email sent successfully to {msg.recipients}")
        except Exception as e:
            print(f"[EmailService] Failed to send email to {msg.recipients}: {e}")


def _send_email(subject, recipients, body_html, body_text=None):
    """Send an email with HTML body. Synchronous on Vercel, threaded locally."""
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=body_html,
            body=body_text or ''
        )
        import os
        if os.getenv('VERCEL'):
            try:
                mail.send(msg)
                print(f"[EmailService] Synchronous serverless email sent to {recipients}")
                return True
            except Exception as e:
                print(f"[EmailService] Failed to send email to {recipients}: {e}")
                return False

        try:
            app = current_app._get_current_object()
            thr = threading.Thread(target=_send_async_email, args=(app, msg))
            thr.daemon = True
            thr.start()
            return True
        except RuntimeError:
            mail.send(msg)
            print(f"[EmailService] Synchronous email sent to {recipients}")
            return True
    except Exception as e:
        print(f"[EmailService] Failed to send email to {recipients}: {e}")
        return False


def send_verification_email(student, token, app_url="http://localhost:5000"):
    """
    Send an email verification link to the student's email address from finditcampus@gmail.com.
    """
    if not student or not student.college_email:
        return False

    verify_url = f"{app_url}/verify-email?token={token}"
    subject = "✉️ Verify Your Email Address — FindIt Campus"

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#2563eb,#7c3aed);padding:32px 24px;text-align:center;">
        <h1 style="color:#fff;font-size:22px;margin:0;">✉️ Verify Your Email Address</h1>
        <p style="color:#bfdbfe;font-size:13px;margin:8px 0 0 0;">FindIt Campus — Smart Lost &amp; Found</p>
      </div>
      <div style="padding:28px 24px;">
        <p style="font-size:15px;color:#1e293b;">Hi <strong>{student.student_name}</strong>,</p>
        <p style="color:#475569;font-size:14px;line-height:1.6;">
          Please verify your email address (<strong>{student.college_email}</strong>) to activate mandatory instant email notifications when items matching your reports are found.
        </p>

        <div style="text-align:center;margin:32px 0;">
          <a href="{verify_url}" style="background:#2563eb;color:#fff;text-decoration:none;padding:14px 32px;border-radius:10px;font-weight:700;font-size:15px;display:inline-block;box-shadow:0 4px 12px rgba(37,99,235,0.3);">
            ✅ Verify My Email Now
          </a>
        </div>

        <p style="color:#94a3b8;font-size:12px;text-align:center;">
          Or copy and paste this URL into your browser:<br>
          <a href="{verify_url}" style="color:#2563eb;word-break:break-all;">{verify_url}</a>
        </p>
      </div>
      <div style="background:#f8fafc;padding:16px 24px;text-align:center;border-top:1px solid #f1f5f9;">
        <p style="color:#94a3b8;font-size:11px;margin:0;">Sent by FindIt Campus (finditcampus@gmail.com) · GIST</p>
      </div>
    </div>
    """
    return _send_email(subject, [student.college_email], html)


def send_match_found_email(student, lost_item, found_item, match_score):
    """
    Notify a student that a potential match was found for their lost item.
    """
    if not student or not student.college_email:
        return False

    subject = f"🎯 Potential Match Found — {lost_item.item_name}"
    score_pct = round(match_score * 100 if match_score <= 1 else match_score, 1)

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#2563eb,#4f46e5);padding:32px 24px;text-align:center;">
        <h1 style="color:#fff;font-size:22px;margin:0;">🎯 Potential Match Found!</h1>
        <p style="color:#bfdbfe;font-size:13px;margin:8px 0 0 0;">FindIt Campus — Smart Lost &amp; Found</p>
      </div>
      <div style="padding:28px 24px;">
        <p style="font-size:15px;color:#1e293b;">Hi <strong>{student.student_name}</strong>,</p>
        <p style="color:#475569;font-size:14px;">Great news! We found a potential match for your lost item.</p>
        
        <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0 0 8px 0;font-size:13px;color:#0369a1;font-weight:700;text-transform:uppercase;letter-spacing:.05em;">Your Lost Item</p>
          <p style="margin:0;font-size:18px;font-weight:700;color:#0c4a6e;">{lost_item.item_name}</p>
          <p style="margin:4px 0 0 0;font-size:12px;color:#475569;">{lost_item.category} · {lost_item.color} · {lost_item.location}</p>
        </div>

        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0 0 8px 0;font-size:13px;color:#15803d;font-weight:700;text-transform:uppercase;letter-spacing:.05em;">Matched Found Item</p>
          <p style="margin:0;font-size:18px;font-weight:700;color:#14532d;">{found_item.item_name}</p>
          <p style="margin:4px 0 0 0;font-size:12px;color:#475569;">{found_item.category} · {found_item.color} · {found_item.location}</p>
        </div>

        <div style="text-align:center;background:#fefce8;border:1px solid #fde68a;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0;font-size:28px;font-weight:800;color:#92400e;">Match Score: {score_pct}%</p>
          <p style="margin:4px 0 0 0;font-size:12px;color:#78350f;">AI Confidence Score</p>
        </div>

        <p style="color:#475569;font-size:14px;">Log in to your dashboard to review this match and verify your claim.</p>
        <div style="text-align:center;margin-top:24px;">
          <a href="https://findit-virid.vercel.app/dashboard" style="background:#2563eb;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:700;font-size:14px;">Go to Dashboard</a>
        </div>
      </div>
      <div style="background:#f8fafc;padding:16px 24px;text-align:center;">
        <p style="color:#94a3b8;font-size:11px;margin:0;">FindIt Campus · Geethanjali Institute of Science &amp; Technology</p>
      </div>
    </div>
    """
    return _send_email(subject, [student.college_email], html)


def send_match_found_to_finder_email(student, lost_item, found_item, match_score):
    """
    Notify a finder student that a potential match was found for the item they reported finding.
    """
    if not student or not student.college_email:
        return False

    subject = f"🎯 Potential Match Found — {found_item.item_name}"
    score_pct = round(match_score * 100 if match_score <= 1 else match_score, 1)

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#059669,#2563eb);padding:32px 24px;text-align:center;">
        <h1 style="color:#fff;font-size:22px;margin:0;">🎯 Potential Owner Found!</h1>
        <p style="color:#bfdbfe;font-size:13px;margin:8px 0 0 0;">FindIt Campus — Smart Lost &amp; Found</p>
      </div>
      <div style="padding:28px 24px;">
        <p style="font-size:15px;color:#1e293b;">Hi <strong>{student.student_name}</strong>,</p>
        <p style="color:#475569;font-size:14px;">Great news! An item you reported finding has a potential match with a reported lost item.</p>
        
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0 0 8px 0;font-size:13px;color:#15803d;font-weight:700;text-transform:uppercase;letter-spacing:.05em;">Your Found Item</p>
          <p style="margin:0;font-size:18px;font-weight:700;color:#14532d;">{found_item.item_name}</p>
          <p style="margin:4px 0 0 0;font-size:12px;color:#475569;">{found_item.category} · {found_item.color} · {found_item.location}</p>
        </div>

        <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0 0 8px 0;font-size:13px;color:#0369a1;font-weight:700;text-transform:uppercase;letter-spacing:.05em;">Matched Lost Item Report</p>
          <p style="margin:0;font-size:18px;font-weight:700;color:#0c4a6e;">{lost_item.item_name}</p>
          <p style="margin:4px 0 0 0;font-size:12px;color:#475569;">{lost_item.category} · {lost_item.color} · {lost_item.location}</p>
        </div>

        <div style="text-align:center;background:#fefce8;border:1px solid #fde68a;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0;font-size:28px;font-weight:800;color:#92400e;">Match Score: {score_pct}%</p>
          <p style="margin:4px 0 0 0;font-size:12px;color:#78350f;">AI Confidence Score</p>
        </div>

        <p style="color:#475569;font-size:14px;">The student who lost this item has been alerted. Once they verify their ownership claim, you will be notified to arrange collection.</p>
        <div style="text-align:center;margin-top:24px;">
          <a href="https://findit-virid.vercel.app/dashboard" style="background:#2563eb;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:700;font-size:14px;">Go to Dashboard</a>
        </div>
      </div>
      <div style="background:#f8fafc;padding:16px 24px;text-align:center;">
        <p style="color:#94a3b8;font-size:11px;margin:0;">FindIt Campus · Geethanjali Institute of Science &amp; Technology</p>
      </div>
    </div>
    """
    return _send_email(subject, [student.college_email], html)


def send_claim_approved_email(student, finder_details, item_name='Lost Item', category='General'):
    """
    Notify the lost-item claimant that their ownership verification has been approved.
    Includes the finder's contact details (Name, Email, Phone) and handover instructions.
    Subject: FindIt Campus — Possible Match Verified
    """
    if not student or not student.college_email:
        return False

    subject = "FindIt Campus — Possible Match Verified"
    phone_val = finder_details.get('phone_number') or 'Not provided'

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#059669,#0d9488);padding:32px 24px;text-align:center;">
        <h1 style="color:#fff;font-size:22px;margin:0;">✅ Possible Match Verified!</h1>
        <p style="color:#a7f3d0;font-size:13px;margin:8px 0 0 0;">FindIt Campus — Smart Lost &amp; Found</p>
      </div>
      <div style="padding:28px 24px;">
        <p style="font-size:15px;color:#1e293b;">Hi <strong>{student.student_name}</strong>,</p>
        <p style="color:#475569;font-size:14px;line-height:1.6;">
          Your ownership verification has been approved. The finder has reported your item and you can now contact them to arrange its return.
        </p>

        <!-- Item Info -->
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:14px 16px;margin:18px 0;">
          <table style="width:100%;font-size:13px;color:#334155;border-collapse:collapse;">
            <tr><td style="padding:3px 0;color:#64748b;width:40%;">Item Name:</td><td style="font-weight:700;color:#0f172a;">{item_name}</td></tr>
            <tr><td style="padding:3px 0;color:#64748b;">Category:</td><td style="font-weight:600;">{category}</td></tr>
            <tr><td style="padding:3px 0;color:#64748b;">Verification Status:</td><td><span style="background:#dcfce7;color:#15803d;padding:2px 8px;border-radius:999px;font-weight:700;font-size:11px;">Approved</span></td></tr>
          </table>
        </div>
        
        <!-- Finder's Details -->
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0 0 12px 0;font-size:13px;color:#15803d;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">Finder's Contact Details</p>
          <table style="width:100%;font-size:13px;color:#1e293b;border-collapse:collapse;">
            <tr><td style="padding:5px 0;color:#64748b;width:40%;">Finder Name:</td><td style="font-weight:700;">{finder_details.get('student_name','N/A')}</td></tr>
            <tr><td style="padding:5px 0;color:#64748b;">Finder College Email:</td><td><a href="mailto:{finder_details.get('college_email','')}" style="color:#2563eb;font-weight:600;text-decoration:none;">{finder_details.get('college_email','N/A')}</a></td></tr>
            <tr><td style="padding:5px 0;color:#64748b;">Finder Phone Number:</td><td style="font-weight:600;">{phone_val}</td></tr>
          </table>
        </div>

        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:14px 16px;margin:20px 0;">
          <p style="margin:0 0 6px 0;font-size:12px;color:#1e40af;font-weight:700;text-transform:uppercase;">Handover Instructions</p>
          <ol style="margin:0;padding-left:18px;font-size:13px;color:#334155;line-height:1.6;">
            <li>Contact the finder via phone or college email above.</li>
            <li>Agree on a safe, public campus location (e.g. Library, Main Office, Canteen) for item handover.</li>
            <li>After receiving your item, confirm receipt on FindIt Campus to close the report.</li>
          </ol>
        </div>

        <div style="text-align:center;margin-top:24px;">
          <a href="https://findit-virid.vercel.app/matches" style="background:#059669;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:700;font-size:14px;display:inline-block;">View Match &amp; Handover Details</a>
        </div>
      </div>
      <div style="background:#f8fafc;padding:16px 24px;text-align:center;border-top:1px solid #f1f5f9;">
        <p style="color:#94a3b8;font-size:11px;margin:0;">FindIt Campus · Geethanjali Institute of Science &amp; Technology</p>
      </div>
    </div>
    """
    return _send_email(subject, [student.college_email], html)


def send_claim_approved_to_finder_email(student, claimant_details, item_name='Found Item', category='General'):
    """
    Notify the finder that the lost-item owner's claim has been successfully verified.
    Includes the lost user's contact details (Name, Email, Phone) and handover instructions.
    Subject: FindIt Campus — Ownership Verified
    """
    if not student or not student.college_email:
        return False

    subject = "FindIt Campus — Ownership Verified"
    phone_val = claimant_details.get('phone_number') or 'Not provided'

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#2563eb,#7c3aed);padding:32px 24px;text-align:center;">
        <h1 style="color:#fff;font-size:22px;margin:0;">🎉 Ownership Verified!</h1>
        <p style="color:#bfdbfe;font-size:13px;margin:8px 0 0 0;">FindIt Campus — Smart Lost &amp; Found</p>
      </div>
      <div style="padding:28px 24px;">
        <p style="font-size:15px;color:#1e293b;">Hi <strong>{student.student_name}</strong>,</p>
        <p style="color:#475569;font-size:14px;line-height:1.6;">
          The ownership of the item has been successfully verified. You can now contact the owner to arrange the handover.
        </p>

        <!-- Item Info -->
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:14px 16px;margin:18px 0;">
          <table style="width:100%;font-size:13px;color:#334155;border-collapse:collapse;">
            <tr><td style="padding:3px 0;color:#64748b;width:40%;">Item Name:</td><td style="font-weight:700;color:#0f172a;">{item_name}</td></tr>
            <tr><td style="padding:3px 0;color:#64748b;">Category:</td><td style="font-weight:600;">{category}</td></tr>
            <tr><td style="padding:3px 0;color:#64748b;">Verification Status:</td><td><span style="background:#dcfce7;color:#15803d;padding:2px 8px;border-radius:999px;font-weight:700;font-size:11px;">Approved</span></td></tr>
          </table>
        </div>

        <!-- Owner's Details -->
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0 0 12px 0;font-size:13px;color:#1e40af;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">Owner's Contact Details</p>
          <table style="width:100%;font-size:13px;color:#1e293b;border-collapse:collapse;">
            <tr><td style="padding:5px 0;color:#64748b;width:40%;">Lost User Name:</td><td style="font-weight:700;">{claimant_details.get('student_name','N/A')}</td></tr>
            <tr><td style="padding:5px 0;color:#64748b;">Lost User College Email:</td><td><a href="mailto:{claimant_details.get('college_email','')}" style="color:#2563eb;font-weight:600;text-decoration:none;">{claimant_details.get('college_email','N/A')}</a></td></tr>
            <tr><td style="padding:5px 0;color:#64748b;">Lost User Phone Number:</td><td style="font-weight:600;">{phone_val}</td></tr>
          </table>
        </div>

        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:14px 16px;margin:20px 0;">
          <p style="margin:0 0 6px 0;font-size:12px;color:#15803d;font-weight:700;text-transform:uppercase;">Handover Instructions</p>
          <ol style="margin:0;padding-left:18px;font-size:13px;color:#334155;line-height:1.6;">
            <li>Coordinate with the owner via phone or email above to arrange handover.</li>
            <li>Meet at a public campus location (e.g. Library counter, Dept staff room).</li>
            <li>After handing over the physical item, click "Mark Item as Handed Over" on your matches page.</li>
          </ol>
        </div>

        <p style="color:#475569;font-size:13px;">Thank you for being a responsible campus citizen! You've earned <strong>+50 points</strong> on the FindIt Campus leaderboard. 🏆</p>
        <div style="text-align:center;margin-top:24px;">
          <a href="https://findit-virid.vercel.app/matches" style="background:#2563eb;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:700;font-size:14px;display:inline-block;">View Match &amp; Handover Details</a>
        </div>
      </div>
      <div style="background:#f8fafc;padding:16px 24px;text-align:center;border-top:1px solid #f1f5f9;">
        <p style="color:#94a3b8;font-size:11px;margin:0;">FindIt Campus · Geethanjali Institute of Science &amp; Technology</p>
      </div>
    </div>
    """
    return _send_email(subject, [student.college_email], html)




def send_welcome_email(student):
    """
    Send a welcome email to a student when they first log in.
    """
    if not student or not student.college_email:
        return False

    subject = "👋 Welcome to FindIt Campus!"

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#2563eb,#7c3aed);padding:32px 24px;text-align:center;">
        <h1 style="color:#fff;font-size:22px;margin:0;">👋 Welcome to FindIt Campus!</h1>
        <p style="color:#bfdbfe;font-size:13px;margin:8px 0 0 0;">Smart Lost &amp; Found · GIST</p>
      </div>
      <div style="padding:28px 24px;">
        <p style="font-size:15px;color:#1e293b;">Hi <strong>{student.student_name}</strong>,</p>
        <p style="color:#475569;font-size:14px;">Welcome to FindIt Campus! You can now report lost items, browse found items, and get AI-powered match notifications.</p>
        
        <div style="background:#eff6ff;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0 0 8px 0;font-weight:700;color:#1e40af;font-size:13px;">Your Account Details</p>
          <p style="margin:0;font-size:13px;color:#1e293b;">🎓 Roll Number: <strong>{student.roll_number}</strong></p>
          <p style="margin:4px 0 0 0;font-size:13px;color:#1e293b;">📧 Email: <strong>{student.college_email}</strong></p>
          <p style="margin:4px 0 0 0;font-size:13px;color:#1e293b;">🏛️ Department: <strong>{student.department}</strong></p>
        </div>

        <div style="text-align:center;margin-top:24px;">
          <a href="https://findit-virid.vercel.app/dashboard" style="background:#2563eb;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:700;font-size:14px;">Go to Dashboard</a>
        </div>
      </div>
      <div style="background:#f8fafc;padding:16px 24px;text-align:center;">
        <p style="color:#94a3b8;font-size:11px;margin:0;">FindIt Campus · Geethanjali Institute of Science &amp; Technology</p>
      </div>
    </div>
    """
    return _send_email(subject, [student.college_email], html)


def send_item_recovered_email(student, item, role='owner'):
    """
    Notify a student that their item has been marked as Recovered.
    role='owner' → sent to the lost-item owner.
    role='finder' → sent to the finder.
    """
    if not student or not student.college_email:
        return False

    item_name = item.item_name if item else 'Item'
    if role == 'finder':
        subject = f"FindIt Campus — Item Successfully Returned 🎉"
        headline = "Item Successfully Returned!"
        body = (
            f"The owner has confirmed receipt of \"{item_name}\". "
            f"Thank you for being a responsible member of the FindIt Campus community! "
            f"You have earned <strong>+50 points</strong> on the leaderboard."
        )
    else:
        subject = f"FindIt Campus — Item Recovered ✅"
        headline = "Your Item Has Been Recovered!"
        body = (
            f"You have confirmed receipt of \"{item_name}\". "
            f"Your item has been marked as <strong>Recovered</strong> in FindIt Campus. "
            f"We hope this experience was helpful!"
        )

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#059669,#0d9488);padding:32px 24px;text-align:center;">
        <h1 style="color:#fff;font-size:22px;margin:0;">🎉 {headline}</h1>
        <p style="color:#a7f3d0;font-size:13px;margin:8px 0 0 0;">FindIt Campus — Smart Lost &amp; Found</p>
      </div>
      <div style="padding:28px 24px;">
        <p style="font-size:15px;color:#1e293b;">Hi <strong>{student.student_name}</strong>,</p>
        <p style="color:#475569;font-size:14px;line-height:1.6;">{body}</p>
        <div style="text-align:center;margin-top:24px;">
          <a href="https://findit-virid.vercel.app/dashboard" style="background:#059669;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:700;font-size:14px;">Go to Dashboard</a>
        </div>
      </div>
      <div style="background:#f8fafc;padding:16px 24px;text-align:center;">
        <p style="color:#94a3b8;font-size:11px;margin:0;">FindIt Campus · Geethanjali Institute of Science &amp; Technology</p>
      </div>
    </div>
    """
    return _send_email(subject, [student.college_email], html)


def send_handover_arranged_email(student, item_name, other_party_name, role='owner'):
    """
    Notify a student that the physical handover has been arranged.
    role='owner' → lost user being notified that finder marked handed over.
    role='finder' → finder being notified that owner confirmed receipt.
    """
    if not student or not student.college_email:
        return False

    if role == 'finder':
        subject = f"FindIt Campus — Handover Confirmed"
        body = f"{other_party_name} has confirmed receipt of \"{item_name}\". The item has been successfully returned."
    else:
        subject = f"FindIt Campus — Finder Has Handed Over Your Item"
        body = f"The finder has marked \"{item_name}\" as handed over. Please confirm receipt on your dashboard."

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#2563eb,#7c3aed);padding:32px 24px;text-align:center;">
        <h1 style="color:#fff;font-size:22px;margin:0;">📦 Handover Update</h1>
        <p style="color:#bfdbfe;font-size:13px;margin:8px 0 0 0;">FindIt Campus — Smart Lost &amp; Found</p>
      </div>
      <div style="padding:28px 24px;">
        <p style="font-size:15px;color:#1e293b;">Hi <strong>{student.student_name}</strong>,</p>
        <p style="color:#475569;font-size:14px;line-height:1.6;">{body}</p>
        <div style="text-align:center;margin-top:24px;">
          <a href="https://findit-virid.vercel.app/matches" style="background:#2563eb;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:700;font-size:14px;">View Matches</a>
        </div>
      </div>
      <div style="background:#f8fafc;padding:16px 24px;text-align:center;">
        <p style="color:#94a3b8;font-size:11px;margin:0;">FindIt Campus · Geethanjali Institute of Science &amp; Technology</p>
      </div>
    </div>
    """
    return _send_email(subject, [student.college_email], html)


def send_handover_issue_email(student, item_name, other_party_name, issue_description=None):
    """
    Notify student that a handover issue was reported.
    """
    if not student or not student.college_email:
        return False

    subject = f"FindIt Campus — Handover Issue Reported"
    issue_text = f"<p style='color:#ef4444;'><strong>Reported Issue:</strong> {issue_description}</p>" if issue_description else ""

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#ef4444,#dc2626);padding:32px 24px;text-align:center;">
        <h1 style="color:#fff;font-size:22px;margin:0;">⚠️ Handover Issue Reported</h1>
        <p style="color:#fecaca;font-size:13px;margin:8px 0 0 0;">FindIt Campus — Smart Lost &amp; Found</p>
      </div>
      <div style="padding:28px 24px;">
        <p style="font-size:15px;color:#1e293b;">Hi <strong>{student.student_name}</strong>,</p>
        <p style="color:#475569;font-size:14px;line-height:1.6;">
          A handover issue has been reported regarding the item <strong>"{item_name}"</strong>.
        </p>
        {issue_text}
        <p style="color:#475569;font-size:14px;line-height:1.6;">
          Please communicate with {other_party_name} or visit the Student Affairs office if assistance is needed.
        </p>
        <div style="text-align:center;margin-top:24px;">
          <a href="https://findit-virid.vercel.app/matches" style="background:#ef4444;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:700;font-size:14px;">View Matches</a>
        </div>
      </div>
      <div style="background:#f8fafc;padding:16px 24px;text-align:center;">
        <p style="color:#94a3b8;font-size:11px;margin:0;">FindIt Campus · Geethanjali Institute of Science &amp; Technology</p>
      </div>
    </div>
    """
    return _send_email(subject, [student.college_email], html)


def send_lost_item_self_recovered_email(student, item_name):
    """
    Send confirmation email when lost user recovers item themselves.
    Subject: FindIt Campus — Lost Item Marked as Recovered
    """
    if not student or not student.college_email:
        return False

    subject = "FindIt Campus — Lost Item Marked as Recovered"
    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#059669,#10b981);padding:32px 24px;text-align:center;">
        <h1 style="color:#fff;font-size:22px;margin:0;">🎉 Item Marked as Recovered!</h1>
        <p style="color:#d1fae5;font-size:13px;margin:8px 0 0 0;">FindIt Campus — Smart Lost &amp; Found</p>
      </div>
      <div style="padding:28px 24px;">
        <p style="font-size:15px;color:#1e293b;">Hi <strong>{student.student_name}</strong>,</p>
        <p style="color:#475569;font-size:14px;line-height:1.6;">
          Your lost-item report for <strong>"{item_name}"</strong> has been marked as recovered by you and is no longer active for AI matching.
        </p>
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0;font-size:13px;color:#15803d;font-weight:600;">
            Status: <strong>Recovered by Owner</strong>
          </p>
          <p style="margin:4px 0 0 0;font-size:12px;color:#475569;">
            This report will no longer receive new match alerts or appear on campus community boards.
          </p>
        </div>
        <div style="text-align:center;margin-top:24px;">
          <a href="https://findit-virid.vercel.app/my-reports" style="background:#059669;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:700;font-size:14px;display:inline-block;">View My Reports</a>
        </div>
      </div>
      <div style="background:#f8fafc;padding:16px 24px;text-align:center;">
        <p style="color:#94a3b8;font-size:11px;margin:0;">FindIt Campus · Geethanjali Institute of Science &amp; Technology</p>
      </div>
    </div>
    """
    return _send_email(subject, [student.college_email], html)


