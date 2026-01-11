import pytest
from app.utils.qr import generate_qr_code
from aiogram.types import BufferedInputFile

def test_generate_qr_code():
    data = "https://example.com/sub"
    result = generate_qr_code(data)
    
    assert isinstance(result, BufferedInputFile)
    assert result.filename == "subscription_qr.png"
    assert len(result.data) > 0
