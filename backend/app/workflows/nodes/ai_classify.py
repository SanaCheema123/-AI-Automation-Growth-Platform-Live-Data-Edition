from app.ai.gateway import AIGateway
from app.workflows.engine.template import render_prompt, secure_prompt
class AIClassifyNode:
    def __init__(self,db,organization_id): self.db=db; self.organization_id=organization_id
    def run(self,context,config,run,step_index):
        prompt=config.get('prompt');
        if not prompt: raise ValueError('ai_classify requires config.prompt')
        result=AIGateway(self.db,self.organization_id).generate('classification',secure_prompt(render_prompt(prompt,context.data)),True)
        context.set(config.get('output_key','classification'),result['output']); return {'pause':False}
