EVENT_LEAD_OUTREACH={
'name':'Event Lead Outreach','steps':[
{'type':'trigger','config':{'event':'event.attendee_captured'}},
{'type':'ai_classify','config':{'output_key':'qualification','prompt':'Evaluate the prospect fit and buying intent using only this context: {{context}}'}},
{'type':'ai_generate','config':{'output_key':'outreach_draft','json_mode':True,'prompt':'Create concise personalized outreach using only verified facts in this context: {{context}}'}},
{'type':'human_approval','config':{'action_type':'outreach','risk_level':'medium','editable_context_key':'outreach_draft','message':'Review the AI-generated outreach before execution.'}},
{'type':'crm_update','config':{'fields':{'workflow_status':'approved_for_outreach'}}}
]}
