from dataclasses import dataclass,field
from datetime import datetime
@dataclass
class Tender:
 id:str;source:str;country:str;title:str;buyer:str='';value:float|None=None;currency:str='';deadline:datetime|None=None;published:datetime|None=None;url:str='';description:str='';procurement_id:str='';cpv:list[str]=field(default_factory=list);value_eur:float|None=None;translations:dict=field(default_factory=dict);source_links:dict=field(default_factory=dict)
 def title_for(self,lang):return self.translations.get(lang,{}).get('title') or self.title
 def desc_for(self,lang):return self.translations.get(lang,{}).get('description') or self.description
