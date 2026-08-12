
import httpx
import json
import logging
from app.config import config

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.timeout = config.OLLAMA_TIMEOUT
    
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        '''
        Generate a response from the Ollama model.
        
        Args:
            system_prompt: The system prompt to set the behavior
            user_prompt: The user prompt/question
            
        Returns:
            The generated response text
            
        Raises:
            Exception: If there's an error communicating with Ollama
        '''
        url = f'{self.base_url}/api/chat'
        
        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': user_prompt
                }
            ],
            'stream': False
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                return result['message']['content'].strip()
        except httpx.ConnectError:
            logger.error(f'Failed to connect to Ollama at {self.base_url}')
            raise Exception(f'Ollama is not available. Please make sure Ollama is running and accessible at {self.base_url}')
        except httpx.HTTPStatusError as e:
            logger.error(f'Ollama returned HTTP {e.response.status_code}: {e.response.text}')
            raise Exception(f'Ollama returned an error: {e.response.status_code}')
        except httpx.RequestError as e:
            logger.error(f'Error communicating with Ollama: {e}')
            raise Exception(f'Error communicating with Ollama: {str(e)}')
        except KeyError as e:
            logger.error(f'Unexpected response format from Ollama: {e}')
            raise Exception('Unexpected response format from Ollama')
        except Exception as e:
            logger.error(f'Unexpected error calling Ollama: {e}')
            raise Exception(f'Unexpected error calling Ollama: {str(e)}')
    
    async def health_check(self) -> dict:
        '''
        Check if Ollama is available and the model is accessible.
        
        Returns:
            A dictionary with status information
        '''
        try:
            # Try to list models to see if Ollama is running
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f'{self.base_url}/api/tags')
                response.raise_for_status()
                
                models_data = response.json()
                available_models = [model['name'] for model in models_data.get('models', [])]
                
                # Check if our configured model is available
                # Ollama appends ":latest" tag, so normalise before comparing
                def _base(name: str) -> str:
                    return name.split(":")[0]

                configured_base = _base(self.model)
                if any(configured_base == _base(m) for m in available_models):
                    return {
                        'status': 'healthy',
                        'ollama': 'connected',
                        'model_available': True
                    }
                else:
                    logger.warning(f'Model {self.model} not found in available models: {available_models}')
                    return {
                        'status': 'degraded',
                        'ollama': 'model_not_found',
                        'model_available': False,
                        'available_models': available_models
                    }
        except httpx.ConnectError:
            logger.error(f'Failed to connect to Ollama at {self.base_url}')
            return {
                'status': 'degraded',
                'ollama': 'unavailable',
                'error': f'Cannot connect to Ollama at {self.base_url}'
            }
        except Exception as e:
            logger.error(f'Error checking Ollama health: {e}')
            return {
                'status': 'degraded',
                'ollama': 'error',
                'error': str(e)
            }

