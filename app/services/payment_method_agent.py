"""Payment method parsing agent using LangChain and OpenAI structured outputs."""

import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.models.payment_method_parsing import PaymentMethodInfo
from app.config.settings import settings

logger = logging.getLogger(__name__)


# System prompt for payment method extraction
PAYMENT_METHOD_SYSTEM_PROMPT = """Eres un asistente experto en extraer información de métodos de pago de mensajes en español.

Tu tarea es analizar el mensaje del usuario y extraer:
1. El nombre del banco o método de pago (ej: "Banco de Chile", "Yape", "Plin", "Transferencia")
2. La descripción completa con toda la información bancaria proporcionada

Los usuarios pueden proporcionar información bancaria en diferentes formatos:
- Multi-línea con nombre, RUT, banco, tipo de cuenta, número de cuenta, email
- Formato simple como "Banco: información"
- Formato con "Método de pago: nombre, descripción"

Ejemplo de formato multi-línea:
Diego Navarrete
20.667.798-8
Banco de Chile
Cuenta Corriente
00-801-65885-03
d.navarrete1301@gmail.com

En este caso:
- bank_name: "Banco de Chile"
- description: Todo el texto completo manteniendo el formato original

Instrucciones:
- Identifica el nombre del banco o método de pago (generalmente aparece en una línea separada o es el nombre más relevante)
- Mantén toda la información en la descripción, preservando el formato original
- Si el mensaje NO es sobre un método de pago, marca is_payment_method como false
- Sé tolerante con diferentes formatos y variaciones
"""


class PaymentMethodAgent:
    """Agent for extracting payment method information from user messages."""
    
    def __init__(self):
        """Initialize the payment method agent."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
        )
        
        # Create structured output LLM
        self.structured_llm = self.llm.with_structured_output(PaymentMethodInfo)
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", PAYMENT_METHOD_SYSTEM_PROMPT),
            ("user", "Mensaje del usuario: {user_message}\n\nExtrae la información del método de pago.")
        ])
        
        # Create chain
        self.chain = self.prompt | self.structured_llm
    
    async def extract_payment_method(self, user_message: str) -> PaymentMethodInfo:
        """Extract payment method information from user message.
        
        Args:
            user_message: The user's message containing payment method information
            
        Returns:
            PaymentMethodInfo with extracted bank name and description
        """
        logger.info(f"Extracting payment method from message: {user_message}")
        
        try:
            result = await self.chain.ainvoke({"user_message": user_message})
            logger.info(f"Extracted payment method: bank_name={result.bank_name}, is_payment_method={result.is_payment_method}")
            return result
        except Exception as e:
            logger.error(f"Error extracting payment method: {e}", exc_info=True)
            # Return default empty info on error
            return PaymentMethodInfo(
                bank_name="",
                description="",
                is_payment_method=False
            )


# Global instance
payment_method_agent = PaymentMethodAgent()


async def extract_payment_method_from_message(message: str) -> PaymentMethodInfo:
    """Extract payment method information from a message.
    
    Args:
        message: User's message containing payment method information
        
    Returns:
        PaymentMethodInfo with extracted information
    """
    return await payment_method_agent.extract_payment_method(message)

