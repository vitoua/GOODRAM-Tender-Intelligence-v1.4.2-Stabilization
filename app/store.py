from datetime import datetime
class Store:
 def __init__(self):self.data={};self.runs=[];self.last_update=None
 def replace(self,results):
  self.data={};self.runs=[]
  for source,items,error,stats in results:
   for item in items:self.data[source+':'+item.procurement_id]=item
   self.runs.append({'source':source,'status':'error' if error else 'ok','count':len(items),'error':str(error)[:2500] if error else '','stats':stats})
  self.last_update=datetime.now()
store=Store()
