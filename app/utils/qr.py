import qrcode
from io import BytesIO
from aiogram.types import BufferedInputFile

def generate_qr_code(data: str) -> BufferedInputFile:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    
    return BufferedInputFile(buf.read(), filename="subscription_qr.png")
