Download Payroll Tracker
Download the latest version here → https://github.com/Ediazpy/Payroll-tracker/releases/tag/v1.0.0

Thrive Payroll Tracker – Installation Guide
Download

You can download the latest signed version of the Thrive Payroll Tracker from the link below:

Download Thrive Payroll Tracker [(Latest Release)](https://github.com/Ediazpy/Payroll-tracker/releases/tag/v1.0.0)

In the Assets section, download:

Thrive-Payroll-Tracker.exe — the signed payroll application

selfsigned.cer — the certificate that allows Windows to trust the app

Step 1 — Install the Certificate (One-Time Setup)

Before running the app for the first time:

Locate selfsigned.cer (you can find it in the dist/ folder or the latest release).

Right-click → Install Certificate

Select Local Machine → click Next

Choose Place all certificates in the following store

Click Browse → select Trusted Root Certification Authorities

Click OK → Next → Finish

Approve any Windows security prompt that appears.

Once this is done, your computer will recognize Emmanuel Diaz Payroll Tracker as a trusted publisher.

Step 2 — Run the Application

Double-click Thrive-Payroll-Tracker.exe

If SmartScreen appears (first time only), click:

More info → Run anyway

The Payroll Tracker will open normally.

After installing the certificate once, you won’t see warnings again.

Troubleshooting

If Windows still shows a warning:
Make sure the certificate was installed under Local Machine → Trusted Root Certification Authorities (not Current User).

If antivirus flags it:
This is common for unsigned or self-signed apps. Once the cert is trusted, the alert should disappear.

About

Thrive Payroll Tracker is a secure internal tool developed by
Emmanuel Diaz to manage payroll, commissions, and invoices efficiently.

Built with Python + PyInstaller, digitally signed for authenticity.
All data stays local — no external connections or cloud dependencies.
