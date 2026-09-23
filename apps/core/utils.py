import os
from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.uploadedfile import InMemoryUploadedFile


def optimize_image(
    image_field,
    max_width: int = 1200,
    max_height: int = 1200,
    quality: int = 85,
    convert_to_webp: bool = True
) -> InMemoryUploadedFile:
    """
    Ridimensiona e comprime un'immagine mantenendo le proporzioni.
    Convertibile in WebP per la massima efficienza web.
    """
    img = Image.open(image_field)

    # Correzione orientamento basata sui metadati EXIF
    img = ImageOps.exif_transpose(img)

    # Conversione in RGB se l'immagine è in RGBA o P (evita errori in conversione JPEG/WebP)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Ridimensionamento proporzionale (Thumbnail)
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    output = BytesIO()
    
    if convert_to_webp:
        filename = f"{os.path.splitext(image_field.name)[0]}.webp"
        img.save(output, format='WEBP', quality=quality, optimize=True)
        content_type = 'image/webp'
    else:
        filename = image_field.name
        img.save(output, format='JPEG', quality=quality, optimize=True)
        content_type = 'image/jpeg'

    output.seek(0)

    return InMemoryUploadedFile(
        file=output,
        field_name='ImageField',
        name=filename,
        content_type=content_type,
        size=output.getbuffer().nbytes,
        charset=None
    )