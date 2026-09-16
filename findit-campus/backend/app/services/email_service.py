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


def send_claim_approved_email(student, finder_details):
    """
    Notify the lost-item claimant that their ownership claim was approved.
    Includes the finder's contact details (Name, Roll, Dept, Email, Phone).
    """
    if not student or not student.college_email:
        return False

    subject = "✅ Claim Approved — Collect Your Item!"
    phone_row = f"<tr><td style=\"padding:4px 0;color:#64748b;\">Phone</td><td style=\"font-weight:600;\">{finder_details.get('phone_number','Not provided')}</td></tr>" if finder_details.get('phone_number') else ""

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#059669,#0d9488);padding:32px 24px;text-align:center;">
        <h1 style="color:#fff;font-size:22px;margin:0;">✅ Claim Approved!</h1>
        <p style="color:#a7f3d0;font-size:13px;margin:8px 0 0 0;">FindIt Campus — Smart Lost &amp; Found</p>
      </div>
      <div style="padding:28px 24px;">
        <p style="font-size:15px;color:#1e293b;">Hi <strong>{student.student_name}</strong>,</p>
        <p style="color:#475569;font-size:14px;">Your ownership claim has been verified and approved! Here are the finder's contact details so you can collect your item.</p>
        
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0 0 12px 0;font-size:13px;color:#15803d;font-weight:700;text-transform:uppercase;">Finder's Contact Details</p>
          <table style="width:100%;font-size:13px;color:#1e293b;border-collapse:collapse;">
            <tr><td style="padding:4px 0;color:#64748b;">Name</td><td style="font-weight:600;">{finder_details.get('student_name','N/A')}</td></tr>
            <tr><td style="padding:4px 0;color:#64748b;">Roll No</td><td style="font-weight:600;font-family:monospace;">{finder_details.get('roll_number','N/A')}</td></tr>
            <tr><td style="padding:4px 0;color:#64748b;">Department</td><td style="font-weight:600;">{finder_details.get('department','N/A')}</td></tr>
            <tr><td style="padding:4px 0;color:#64748b;">Email</td><td><a href="mailto:{finder_details.get('college_email','')}" style="color:#2563eb;">{finder_details.get('college_email','N/A')}</a></td></tr>
            {phone_row}
          </table>
        </div>

        <p style="color:#475569;font-size:13px;">Please contact the finder directly to arrange collection. Congratulations on recovering your item! 🎉</p>
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


def send_claim_approved_to_finder_email(student, claimant_details):
    """
    Notify the finder that the lost-item owner's claim has been approved.
    Includes the claimant's (lost user's) contact details (Name, Roll, Dept, Email, Phone)
    so the finder can arrange return of the item.
    """
    if not student or not student.college_email:
        return False

    subject = "🎉 Ownership Verified — Item Can Be Returned!"
    phone_row = f"<tr><td style=\"padding:4px 0;color:#64748b;\">Phone</td><td style=\"font-weight:600;\">{claimant_details.get('phone_number','Not provided')}</td></tr>" if claimant_details.get('phone_number') else ""

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#2563eb,#7c3aed);padding:32px 24px;text-align:center;">
        <h1 style="color:#fff;font-size:22px;margin:0;">🎉 Ownership Verified!</h1>
        <p style="color:#bfdbfe;font-size:13px;margin:8px 0 0 0;">FindIt Campus — Smart Lost &amp; Found</p>
      </div>
      <div style="padding:28px 24px;">
        <p style="font-size:15px;color:#1e293b;">Hi <strong>{student.student_name}</strong>,</p>
        <p style="color:#475569;font-size:14px;">The owner of the item you found has successfully verified their ownership claim. Please contact them to arrange the return of the item.</p>

        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0 0 12px 0;font-size:13px;color:#1e40af;font-weight:700;text-transform:uppercase;">Owner's Contact Details</p>
          <table style="width:100%;font-size:13px;color:#1e293b;border-collapse:collapse;">
            <tr><td style="padding:4px 0;color:#64748b;">Name</td><td style="font-weight:600;">{claimant_details.get('student_name','N/A')}</td></tr>
            <tr><td style="padding:4px 0;color:#64748b;">Roll No</td><td style="font-weight:600;font-family:monospace;">{claimant_details.get('roll_number','N/A')}</td></tr>
            <tr><td style="padding:4px 0;color:#64748b;">Department</td><td style="font-weight:600;">{claimant_details.get('department','N/A')}</td></tr>
            <tr><td style="padding:4px 0;color:#64748b;">Email</td><td><a href="mailto:{claimant_details.get('college_email','')}" style="color:#2563eb;">{claimant_details.get('college_email','N/A')}</a></td></tr>
            {phone_row}
          </table>
        </div>

        <p style="color:#475569;font-size:13px;">Thank you for being a responsible community member! You've earned <strong>+50 points</strong> on the FindIt Campus leaderboard. 🏆</p>
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
