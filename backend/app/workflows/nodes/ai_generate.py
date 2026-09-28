from app.ai.gateway import AIGateway
from app.workflows.engine.template import render_prompt, secure_prompt
class AIGenerateNode:
    def __init__(self,db,organization_id): self.db=db; self.organization_id=organization_id
    def run(self,context,config,run,step_index):
        prompt=config.get('prompt');
        if not prompt: raise ValueError('ai_generate requires config.prompt')
        result=AIGateway(self.db,self.organization_id).generate('generation',secure_prompt(render_prompt(prompt,context.data)),bool(config.get('json_mode')))
        context.set(config.get('output_key','generated'),result['output']); return {'pause':False}
