"""OCR service for receipt extraction using LangChain with OpenAI."""

import base64
import logging

import httpx
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from enum import Enum
from pydantic import BaseModel

from app.config import settings
from app.models.receipt import DocumentExtraction, ReceiptExtraction, TransferExtraction

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """Document types for classification."""

    RECEIPT = "receipt"
    TRANSFER = "transfer"


class ClassificationSchema(BaseModel):
    """Schema for document classification."""

    document_type: DocumentType


# Pydantic schemas for structured output (simplified for OpenAI compatibility)
class ItemSchema(BaseModel):
    """Schema for individual receipt item."""

    description: str
    amount: float
    count: int


class ReceiptLLMSchema(BaseModel):
    """Schema for LLM to extract receipt data."""

    merchant: str
    date: str
    total_amount: float
    tip: float
    items: list[ItemSchema]


class TransferLLMSchema(BaseModel):
    """Schema for LLM to extract transfer data."""

    recipient: str
    amount: float
    description: str | None = None


def _initialize_openai_model(temperature: float = 0.2) -> ChatOpenAI:
    """Initialize OpenAI model with LangChain.

    Args:
        temperature: Model temperature for consistency (default 0.2)

    Returns:
        ChatOpenAI: Initialized model

    Raises:
        ValueError: If OPENAI_API_KEY not configured
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured in environment variables")

    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=temperature,
        max_tokens=2048,
    )


async def download_image_from_url(image_url: str) -> tuple[bytes, str]:
    """Download image from URL and return content with MIME type.

    Args:
        image_url: URL of the image to download

    Returns:
        tuple: (image_content, mime_type)

    Raises:
        ValueError: If URL is invalid, download fails, or file is not an image
        RuntimeError: If HTTP request fails
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"Downloading image from URL: {image_url}")
            response = await client.get(image_url)
            response.raise_for_status()

            # Get content type from headers or guess from URL
            content_type = response.headers.get("content-type", "")
            if content_type:
                mime_type = content_type.split(";")[0].strip()
            else:
                # Try to guess from URL extension
                if image_url.lower().endswith((".jpg", ".jpeg")):
                    mime_type = "image/jpeg"
                elif image_url.lower().endswith(".png"):
                    mime_type = "image/png"
                elif image_url.lower().endswith(".webp"):
                    mime_type = "image/webp"
                elif image_url.lower().endswith(".gif"):
                    mime_type = "image/gif"
                else:
                    mime_type = "image/jpeg"  # Default

            # Validate it's an image
            if not mime_type.startswith("image/"):
                raise ValueError(f"URL does not point to an image. Content-Type: {mime_type}")

            image_content = response.content
            if not image_content:
                raise ValueError("Downloaded image is empty")

            logger.info(
                f"Successfully downloaded image: {len(image_content)} bytes, type: {mime_type}"
            )
            return image_content, mime_type

    except httpx.HTTPError as e:
        logger.error(f"HTTP error downloading image: {str(e)}")
        raise RuntimeError(f"Failed to download image from URL: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error downloading image: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to download image: {str(e)}") from e


async def scan_receipt(
    file_content: bytes, mime_type: str, custom_prompt: str | None = None
) -> DocumentExtraction:
    """Scan document image using LangChain with OpenAI and structured outputs.

    Uses Pydantic models for automatic validation and type safety.
    Detects if the document is a receipt or transfer and extracts data accordingly.

    Args:
        file_content: Binary content of the image file
        mime_type: MIME type of the image (e.g., 'image/jpeg', 'image/png')
        custom_prompt: Optional custom instruction to prepend. If None, uses default.

    Returns:
        DocumentExtraction: Validated document data (receipt or transfer)

    Raises:
        ValueError: If API key is missing, API call fails, or response is invalid
        RuntimeError: If OpenAI API returns an error
    """
    try:
        # Initialize model
        model = _initialize_openai_model()

        # Encode image to base64 for LangChain
        image_b64 = base64.b64encode(file_content).decode()
        image_url = f"data:{mime_type};base64,{image_b64}"

        # Step 1: Classify document type with structured output
        classify_prompt = (
            custom_prompt
            or """Analiza cuidadosamente esta imagen y clasifícala.

CRITERIOS PARA 'transfer' (Transferencia/Depósito):
- Es una captura de pantalla de app bancaria o comprobante digital.
- Contiene palabras como: "Transferencia realizada", "Comprobante", "Destinatario", "Monto transferido", "Cuenta origen/destino".
- Muestra datos bancarios: Banco, RUT/DNI, Nro de operación.
- NO tiene lista de productos consumidos.

CRITERIOS PARA 'receipt' (Boleta/Recibo):
- Es una foto de un papel físico o ticket digital de compra.
- Contiene: Lista de productos/platos, precios individuales, "Total a pagar", "Propina", "Mesa", "Garzón".
- Nombre de un restaurante, tienda o comercio.
- Desglose de IVA o impuestos.

Selecciona el tipo de documento correcto."""
        )

        classify_message = HumanMessage(
            content=[
                {"type": "text", "text": classify_prompt},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]
        )

        logger.info("Classifying document type with OpenAI structured output")
        classifier_model = model.with_structured_output(ClassificationSchema)
        classification = await classifier_model.ainvoke([classify_message])
        doc_type = classification.document_type.value

        logger.info(f"Document classified as: {doc_type}")

        # Step 2: Extract structured data based on type
        if doc_type == "receipt":
            # Configure model with structured output for receipts
            structured_model = model.with_structured_output(ReceiptLLMSchema)

            extract_prompt = """Eres un experto en extracción de datos de boletas y recibos financieros.
Analiza la imagen y extrae la siguiente información estructurada:

REGLAS DE EXTRACCIÓN:
1. merchant: Nombre del comercio, restaurante o proveedor.
2. date: Fecha del documento en formato YYYY-MM-DD.
3. total_amount: Monto TOTAL pagado (incluyendo propina e impuestos).
4. tip: Busca explícitamente 'Propina', 'Tip', 'Servicio' o 'Service Charge'. Si no aparece nada explícito, el valor es 0.
5. items: Lista detallada de ítems consumidos.
   - description: Nombre del producto/plato.
   - amount: Precio unitario o total por línea.
   - count: Cantidad (default 1 si no se especifica).

IMPORTANTE:
- Si hay descuentos, el total_amount debe ser el monto FINAL pagado.
- Sé preciso con los montos numéricos.
"""

            extract_message = HumanMessage(
                content=[
                    {"type": "text", "text": extract_prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ]
            )

            logger.info("Extracting receipt data with structured output")
            llm_data = await structured_model.ainvoke([extract_message])

            # Convert LLM schema to app schema using model_validate with aliases
            receipt_dict = {
                "merchant": llm_data.merchant,
                "date": llm_data.date,  # Use alias "date" instead of "receipt_date"
                "total_amount": llm_data.total_amount,
                "tip": llm_data.tip,
                "items": [
                    {
                        "description": item.description,
                        "amount": item.amount,
                        "count": item.count,
                    }
                    for item in llm_data.items
                ],
            }
            receipt_data = ReceiptExtraction.model_validate(receipt_dict)

            document_extraction = DocumentExtraction(
                document_type="receipt",
                receipt=receipt_data,
                transfer=None,
            )

            logger.info(
                f"Successfully extracted receipt: {receipt_data.merchant}, "
                f"Total: ${receipt_data.total_amount}, Tip: ${receipt_data.tip}"
            )

        else:  # transfer
            # Configure model with structured output for transfers
            structured_model = model.with_structured_output(TransferLLMSchema)

            extract_prompt = """Eres un experto en extracción de datos de transferencias bancarias.
Analiza la imagen y extrae la siguiente información estructurada:

REGLAS DE EXTRACCIÓN:
1. recipient: Nombre del destinatario, cuenta destino o beneficiario.
2. amount: Monto transferido (número positivo).
3. description: Glosa, mensaje, comentario o referencia de la transferencia (si existe).

IMPORTANTE:
- Ignora saldos de cuenta, busca el monto de la transacción específica.
- Extrae el nombre completo del destinatario si es posible.
"""

            extract_message = HumanMessage(
                content=[
                    {"type": "text", "text": extract_prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ]
            )

            logger.info("Extracting transfer data with structured output")
            llm_data = await structured_model.ainvoke([extract_message])

            # Convert LLM schema to app schema
            transfer_data = TransferExtraction(
                recipient=llm_data.recipient,
                amount=llm_data.amount,
                description=llm_data.description,
            )

            document_extraction = DocumentExtraction(
                document_type="transfer",
                receipt=None,
                transfer=transfer_data,
            )

            logger.info(
                f"Successfully extracted transfer: Recipient={transfer_data.recipient}, Amount=${transfer_data.amount}"
            )

        return document_extraction

    except ValueError as e:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Error calling OpenAI API via LangChain: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to process document with OpenAI: {str(e)}") from e
