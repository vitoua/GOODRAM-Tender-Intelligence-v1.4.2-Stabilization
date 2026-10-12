from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
 app_language:str='pl'; apify_api_token:str=''; azure_translator_key:str=''; azure_translator_region:str=''; libretranslate_url:str=''; libretranslate_api_key:str=''
 model_config=SettingsConfigDict(env_file='.env',extra='ignore')
settings=Settings()
