class TriggerNode:
    def __init__(self,db,organization_id): pass
    def run(self,context,config,run,step_index): context.set('trigger',config.get('event','manual')); return {'pause':False}
