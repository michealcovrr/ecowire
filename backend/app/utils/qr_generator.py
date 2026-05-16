import io
import base64


def generate_qr_base64(user_id: str) -> str | None:
    """
    Generate a base64-encoded PNG QR for the user ID.
    Returns None if PIL/qrcode aren't available (e.g. some serverless
    runtimes), so the caller can degrade gracefully instead of 500'ing.
    """
    try:
        import qrcode   # noqa
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(user_id)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")
    except Exception as e:
        print(f"[qr_generator] failed: {type(e).__name__}: {e}", flush=True)
        return None
