ALLOWED={
"pending":{"running","failed","cancelled"},
"running":{"waiting_approval","completed","failed","cancelled"},
"waiting_approval":{"running","failed","cancelled"},
"completed":set(),"failed":{"running","cancelled"},"cancelled":set()}
def can_transition(current:str,target:str)->bool:return target in ALLOWED.get(current,set())
