def otp_email_template(otp: str, purpose: str) -> str:
    return f"""
    <html>
      <body>
        <h2>{purpose} OTP</h2>
        <p>Your OTP is:</p>
        <h1>{otp}</h1>
        <p>This OTP is valid for 10 minutes.</p>
      </body>
    </html>
    """
