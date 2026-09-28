import React from "react";
import {api, getToken, setToken} from "./api/client.js";
import {Badge, Button, Card, Drawer, EmptyState, ErrorState, Field, Icon, Input, MetricCard, Modal, Select, Skeleton, Status, Textarea} from "./components/ui.js";

const h = React.createElement;
const H = (type, props, ...children) => h(type, props, ...children.flat(Infinity).filter(x => x !== false && x !== undefined));
const F = (...children) => H(React.Fragment, null, children);
const {useCallback, useEffect, useState} = React;

const NAV = [
  {group:"GROWTH", items:[["dashboard","Dashboard","dashboard"],["leads","Leads","leads"],["events","Events","events"],["content","Content Studio","insight"],["meeting-intelligence","Meeting Intelligence","insight"]]},
  {group:"AUTOMATION", items:[["workflows","Workflows","workflow"],["runs","Automation Runs","run"],["approvals","Approvals","approval"]]},
  {group:"ANALYTICS", items:[["analytics","Analytics","analytics"]]},
  {group:"SYSTEM", items:[["settings","Settings","settings"]]},
];
const TITLES = Object.fromEntries(NAV.flatMap(g => g.items.map(x => [x[0], x[1]])));
const LEAD_STATUSES = ["new","qualified","engaged","needs_review","contacted","converted","disqualified"];
const routeFromHash = () => location.hash.replace(/^#\/?/, "").split("/")[0] || "dashboard";
const fmtDate = v => v ? new Date(v).toLocaleString([], {month:"short", day:"numeric", hour:"2-digit", minute:"2-digit"}) : "—";
const pct = v => `${Number(v || 0).toFixed(1)}%`;
const statusTone = s => ({qualified:"success",converted:"success",engaged:"info",contacted:"info",needs_review:"warning",disqualified:"danger",new:"neutral"}[s] || "neutral");
const nodeTitle = t => ({trigger:"Trigger",ai_classify:"AI Qualification",ai_generate:"AI Generate",human_approval:"Human Approval",crm_update:"CRM Update"}[t] || t);

function useLoad(loader, deps = []) {
  const [data,setData] = useState(null);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState(null);
  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { setData(await loader()); }
    catch (e) { setError(e.message || "Request failed"); }
    finally { setLoading(false); }
  }, deps);
  useEffect(() => { load(); }, [load]);
  return {data,loading,error,reload:load,setData};
}

function SectionHead({eyebrow,title,action}) {
  return H("div", {className:"section-head"},
    H("div", null, eyebrow && H("p", {className:"eyebrow"}, eyebrow), H("h2", null, title)),
    action
  );
}
function Toast({toast}) { return toast ? H("div", {className:`toast toast-${toast.tone || "success"}`, role:"status"}, toast.message) : null; }
function Info({label,value}) { return H("div", {className:"info"}, H("span", null, label), H("strong", null, value)); }

function Auth({onAuth}) {
  const [mode,setMode] = useState("login");
  const [form,setForm] = useState({organization_name:"",name:"",email:"",password:""});
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState("");
  async function submit(e) {
    e.preventDefault(); setBusy(true); setError("");
    try {
      const result = mode === "login"
        ? await api.auth.login({email:form.email,password:form.password})
        : await api.auth.register(form);
      setToken(result.access_token); onAuth(result);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  return H("main", {className:"auth-page"},
    H("section", {className:"auth-brand"},
      H("div", {className:"brand-mark large"}, "A"),
      H("p", {className:"eyebrow"}, "LIVE AI GROWTH OPERATIONS"),
      H("h1", null, "Run your growth workflows on real business data."),
      H("p", null, "Manage live leads and events, use free-tier AI providers, review AI actions, and monitor automation execution from one operating layer."),
      H("div", {className:"auth-flow"}, ["Live CRM","AI Qualification","Human Approval","Automation"].map((x,i) => H("div", {key:x}, H("span", null, i+1), x)))
    ),
    H("section", {className:"auth-card"},
      H("div", null,
        H("p", {className:"eyebrow"}, mode === "login" ? "WELCOME BACK" : "CREATE WORKSPACE"),
        H("h2", null, mode === "login" ? "Sign in to your workspace" : "Create a live workspace"),
        H("p", {className:"muted"}, mode === "login" ? "Use your organization account to continue." : "New workspaces start empty. No sample or demo records are inserted.")
      ),
      error && H("div", {className:"form-error", role:"alert"}, error),
      H("form", {onSubmit:submit,className:"form-stack"},
        mode === "register" && F(
          H(Field,{label:"Organization"},H(Input,{required:true,value:form.organization_name,onChange:e=>setForm({...form,organization_name:e.target.value}),placeholder:"Acme Growth"})),
          H(Field,{label:"Your name"},H(Input,{required:true,value:form.name,onChange:e=>setForm({...form,name:e.target.value}),placeholder:"Alex Morgan"}))
        ),
        H(Field,{label:"Email"},H(Input,{required:true,type:"email",value:form.email,onChange:e=>setForm({...form,email:e.target.value}),placeholder:"you@company.com"})),
        H(Field,{label:"Password",hint:mode === "register" ? "Minimum 10 characters" : null},H(Input,{required:true,type:"password",minLength:mode === "register" ? 10 : 1,value:form.password,onChange:e=>setForm({...form,password:e.target.value}),placeholder:"••••••••••••"})),
        H(Button,{type:"submit",variant:"primary",disabled:busy},busy ? "Working…" : mode === "login" ? "Sign in" : "Create workspace")
      ),
      H("button", {className:"auth-switch",onClick:()=>{setMode(mode === "login" ? "register" : "login");setError("");}}, mode === "login" ? "Need a workspace? Create one" : "Already have an account? Sign in")
    )
  );
}

function AICopilot({context,runtime}) {
  const suggestions=["What leads need follow-up today?","Which prospects show the strongest buying signals?","What should I review before outreach?"];
  const [question,setQuestion]=useState(""); const [result,setResult]=useState(null); const [busy,setBusy]=useState(false); const [error,setError]=useState("");
  const ready=runtime?.ai_ready === true;
  async function ask(value=question){if(!value.trim()||!ready)return;setQuestion(value);setBusy(true);setError("");try{setResult(await api.ai.copilot({question:value,context}));}catch(e){setError(e.message);}finally{setBusy(false);}}
  return H(Card,{className:"copilot-card"},
    H("div",{className:"copilot-head"},H("div",{className:"copilot-orb"},"✦"),H("div",{className:"grow"},H("p",{className:"eyebrow"},"AI GROWTH COPILOT"),H("h3",null,"Ask questions about your live workspace")),H(Badge,{tone:ready?"success":"warning"},ready?(result?.provider||runtime.ai_provider):"AI key required")),
    !ready&&H("div",{className:"ai-response"},H("strong",null,"AI is not configured"),H("small",null,"Add a free-tier GEMINI_API_KEY or GROQ_API_KEY in the backend .env file. CRM, events, workflows and approvals remain usable without AI.")),
    H("div",{className:"copilot-input"},H(Input,{value:question,onChange:e=>setQuestion(e.target.value),onKeyDown:e=>{if(e.key==="Enter")ask();},placeholder:"Ask about leads, approvals or workflows…","aria-label":"Ask AI Growth Copilot",disabled:!ready}),H(Button,{variant:"primary",onClick:()=>ask(),disabled:busy||!ready},busy?"Analyzing…":"Ask AI")),
    ready&&H("div",{className:"suggestion-row"},suggestions.map(x=>H("button",{key:x,onClick:()=>ask(x)},x))),
    error&&H(ErrorState,{message:error}),
    busy&&H("div",{className:"ai-processing"},H("span",{className:"spinner"}),"AI is analyzing your request…"),
    result&&H("div",{className:"ai-response"},H("strong",null,result.output?.answer||"Analysis complete"),result.output?.recommended_actions?.length&&H("ul",null,result.output.recommended_actions.map(x=>H("li",{key:x},x))),result.fallback&&H("small",null,"The primary free-tier provider failed, so the configured secondary provider completed this request."))
  );
}

function Dashboard({go,runtime}) {
  const stats = useLoad(() => api.analytics(30), []);
  const leads = useLoad(() => api.leads.list("?page_size=5"), []);
  const approvals = useLoad(() => api.approvals.list(), []);
  const runs = useLoad(() => api.workflows.runs(), []);
  const m = stats.data?.metrics || {};
  const metricArea = stats.loading ? H(Skeleton,{lines:4}) : stats.error ? H(ErrorState,{message:stats.error,onRetry:stats.reload}) : H("div",{className:"metric-grid"},
    H(MetricCard,{label:"Total Leads",metric:m.total_leads}),
    H(MetricCard,{label:"Qualified Leads",metric:m.qualified_leads}),
    H(MetricCard,{label:"Active Workflows",metric:m.active_workflows}),
    H(MetricCard,{label:"Pending Approvals",metric:m.pending_approvals}),
    H(MetricCard,{label:"Conversion Rate",metric:m.conversion_rate,format:pct}),
    H(MetricCard,{label:"Automation Success",metric:m.automation_success_rate,format:pct})
  );
  const leadContent = leads.loading ? H(Skeleton,{}) : leads.error ? H(ErrorState,{message:leads.error,onRetry:leads.reload}) : !leads.data?.items?.length
    ? H(EmptyState,{title:"No leads yet",description:"Add your first lead to start qualification and follow-up workflows.",action:H(Button,{variant:"primary",onClick:()=>go("leads")},"Add Lead")})
    : H("div",{className:"list"},leads.data.items.map(x=>H("div",{className:"list-row",key:x.id},
        H("div",{className:"avatar"},x.name.slice(0,2).toUpperCase()),
        H("div",{className:"grow"},H("strong",null,x.name),H("small",null,[x.company,x.persona].filter(Boolean).join(" · ")||"Profile incomplete")),
        H(Badge,{tone:statusTone(x.status)},x.status.replaceAll("_"," ")),
        H("span",{className:"score"},x.score == null ? "—" : Math.round(x.score))
      )));
  const runContent = runs.loading ? H(Skeleton,{}) : runs.error ? H(ErrorState,{message:runs.error,onRetry:runs.reload}) : !runs.data?.length
    ? H(EmptyState,{title:"No workflow runs",description:"Run a workflow to see execution state and approvals here."})
    : H("div",{className:"timeline compact"},runs.data.slice(0,6).map(r=>H("div",{className:"timeline-item",key:r.id},
        H("span",{className:`timeline-dot ${r.status}`}),
        H("div",{className:"grow"},H("strong",null,r.trigger_type||"Manual run"),H("small",null,fmtDate(r.started_at))),
        H(Status,{value:r.status})
      )));
  return F(
    H("div",{className:"hero"},
      H("div",null,H("p",{className:"eyebrow"},"LIVE GROWTH COMMAND CENTER"),H("h1",null,"Your live growth operations, in one place."),H("p",{className:"hero-copy"},"Monitor real CRM records, events, workflows, approvals and automation execution. AI features use only configured external providers.")),
      H("div",{className:"hero-actions"},H(Button,{variant:"primary",icon:"plus",onClick:()=>go("workflows")},"Create Workflow"),H(Button,{icon:"plus",onClick:()=>go("leads")},"Add Lead"))
    ),
    metricArea,
    H("div",{className:"two-col"},
      H(Card,null,H(SectionHead,{eyebrow:"PIPELINE",title:"Recent leads",action:H(Button,{variant:"ghost",onClick:()=>go("leads")},"View all")}),leadContent),
      H(Card,null,H(SectionHead,{eyebrow:"AUTOMATION",title:"Recent execution",action:H(Button,{variant:"ghost",onClick:()=>go("runs")},"View runs")}),runContent)
    ),
    H(AICopilot,{runtime,context:{metrics:stats.data?.metrics||{},recent_leads:leads.data?.items||[],pending_approvals:approvals.data?.length||0,recent_runs:runs.data?.slice?.(0,5)||[]}}),
    H(Card,{className:"approval-strip"},
      H("div",{className:"approval-count"},approvals.loading?"…":approvals.data?.length||0),
      H("div",{className:"grow"},H("p",{className:"eyebrow"},"HUMAN-IN-THE-LOOP"),H("h3",null,"Actions waiting for review"),H("p",{className:"muted"},"Important AI-generated or CRM-changing actions stay paused until a human decides.")),
      H(Button,{variant:"primary",onClick:()=>go("approvals")},"Open Approval Center")
    )
  );
}

function AddLead({onClose,onSaved}) {
  const [f,setF]=useState({name:"",email:"",company:"",persona:"",status:"new"});
  const [busy,setBusy]=useState(false); const [error,setError]=useState("");
  async function save(e){e.preventDefault();setBusy(true);try{await api.leads.create({...f,email:f.email||null});onSaved();}catch(x){setError(x.message);}finally{setBusy(false);}}
  return H(Modal,{title:"Add lead",onClose},H("form",{className:"form-stack",onSubmit:save},
    error&&H("div",{className:"form-error"},error),
    H(Field,{label:"Name"},H(Input,{required:true,value:f.name,onChange:e=>setF({...f,name:e.target.value})})),
    H(Field,{label:"Email"},H(Input,{type:"email",value:f.email,onChange:e=>setF({...f,email:e.target.value})})),
    H(Field,{label:"Company"},H(Input,{value:f.company,onChange:e=>setF({...f,company:e.target.value})})),
    H(Field,{label:"Persona"},H(Input,{value:f.persona,onChange:e=>setF({...f,persona:e.target.value})})),
    H(Field,{label:"Status"},H(Select,{value:f.status,onChange:e=>setF({...f,status:e.target.value})},LEAD_STATUSES.map(s=>H("option",{key:s,value:s},s.replaceAll("_"," "))))),
    H("div",{className:"modal-actions"},H(Button,{onClick:onClose},"Cancel"),H(Button,{type:"submit",variant:"primary",disabled:busy},busy?"Saving…":"Add Lead"))
  ));
}
function LeadDrawer({lead,onClose,onSaved,notify}) {
  const [f,setF]=useState({status:lead.status,next_action:lead.next_action||"",score:lead.score??"",notes:lead.notes||""});
  const [busy,setBusy]=useState(false); const [aiBusy,setAiBusy]=useState(false);
  const [outreachBusy,setOutreachBusy]=useState(false); const [outreach,setOutreach]=useState(null); const [outreachError,setOutreachError]=useState("");
  async function qualify(){setAiBusy(true);try{const r=await api.leads.qualify(lead.id);setF({...f,score:r.lead.score??"",next_action:r.lead.next_action||""});onSaved(true,r.ai?.provider);}catch(e){notify(e.message,"danger");}finally{setAiBusy(false);}}
  async function draftOutreach(){setOutreachBusy(true);setOutreachError("");try{const r=await api.ai.outreach({prospect:lead,event:{},instruction:"Create a concise follow-up draft based only on verified CRM fields."});setOutreach(r);}catch(e){setOutreachError(e.message);}finally{setOutreachBusy(false);}}
  async function approveOutreach(){if(!outreach?.output)return;try{await api.approvals.create({action_type:"outreach",risk_level:"medium",title:`Review outreach for ${lead.name}`,value:outreach.output,context:{lead_id:lead.id}});notify("Outreach draft sent to Approval Center");}catch(e){notify(e.message,"danger");}}
  async function save(){setBusy(true);try{await api.leads.update(lead.id,{status:f.status,next_action:f.next_action||null,score:f.score===""?null:Number(f.score),notes:f.notes||null});onSaved();}catch(e){notify(e.message,"danger");}finally{setBusy(false);}}
  return H(Drawer,{title:lead.name,onClose},
    H("div",{className:"profile-head"},H("div",{className:"avatar xl"},lead.name.slice(0,2).toUpperCase()),H("div",null,H("h3",null,lead.company||"No company"),H("p",{className:"muted"},[lead.role,lead.persona].filter(Boolean).join(" · ")||"Profile details not connected"))),
    H("div",{className:"detail-grid"},H(Info,{label:"Email",value:lead.email||"—"}),H(Info,{label:"AI score",value:lead.score==null?"Not scored":`${Math.round(lead.score)} / 100`}),H(Info,{label:"Engagement",value:lead.engagement_score==null?"Not connected":`${Math.round(lead.engagement_score)}%`}),H(Info,{label:"Last activity",value:fmtDate(lead.last_activity_at)})),
    lead.qualification_reason&&H(Card,{className:"subcard"},H("p",{className:"eyebrow"},"AI QUALIFICATION"),H("p",null,lead.qualification_reason)),
    H("div",{className:"form-stack"},
      H(Field,{label:"Status"},H(Select,{value:f.status,onChange:e=>setF({...f,status:e.target.value})},LEAD_STATUSES.map(s=>H("option",{key:s,value:s},s.replaceAll("_"," "))))),
      H(Field,{label:"AI score"},H(Input,{type:"number",min:0,max:100,value:f.score,onChange:e=>setF({...f,score:e.target.value})})),
      H(Field,{label:"Suggested / next action"},H(Textarea,{value:f.next_action,onChange:e=>setF({...f,next_action:e.target.value}),rows:3})),
      H(Field,{label:"Notes"},H(Textarea,{value:f.notes,onChange:e=>setF({...f,notes:e.target.value}),rows:5})),
      H("div",{className:"drawer-actions"},H(Button,{onClick:qualify,disabled:aiBusy},aiBusy?"AI qualifying…":"Qualify with AI"),H(Button,{onClick:draftOutreach,disabled:outreachBusy},outreachBusy?"Drafting…":"Draft Outreach"),H(Button,{variant:"primary",onClick:save,disabled:busy},busy?"Saving…":"Save"))
    ),
    outreachError&&H(ErrorState,{message:outreachError}),
    outreach&&H(Card,{className:"subcard"},H("div",{className:"card-top"},H("p",{className:"eyebrow"},"OUTREACH DRAFT"),H(Badge,{tone:"info"},outreach.provider)),H("strong",null,outreach.output?.subject||"Follow-up"),H("p",{className:"outreach-message"},outreach.output?.message||""),H(Button,{variant:"primary",onClick:approveOutreach},"Send to Approval"))
  );
}

function Leads({notify}) {
  const [q,setQ]=useState(""); const [status,setStatus]=useState(""); const [selected,setSelected]=useState(null); const [showAdd,setShowAdd]=useState(false);
  const query=`?page_size=50${q?`&q=${encodeURIComponent(q)}`:""}${status?`&status=${status}`:""}`;
  const state=useLoad(()=>api.leads.list(query),[q,status]);
  let body;
  if(state.loading) body=H(Skeleton,{lines:6});
  else if(state.error) body=H(ErrorState,{message:state.error,onRetry:state.reload});
  else if(!state.data?.items?.length) body=H(EmptyState,{title:"No leads match this view",description:"Add a lead or change your filters to continue."});
  else body=H("div",{className:"table-wrap"},H("table",{className:"data-table"},
    H("thead",null,H("tr",null,["Lead","Status","Persona","AI score","Engagement","Next action","Updated"].map(x=>H("th",{key:x},x)))),
    H("tbody",null,state.data.items.map(x=>H("tr",{key:x.id,onClick:()=>setSelected(x),tabIndex:0,onKeyDown:e=>(e.key==="Enter"||e.key===" ")&&setSelected(x)},
      H("td",null,H("strong",null,x.name),H("small",null,x.company||x.email||"No company")),
      H("td",null,H(Badge,{tone:statusTone(x.status)},x.status.replaceAll("_"," "))),H("td",null,x.persona||"—"),
      H("td",null,x.score==null?H("span",{className:"muted"},"Not scored"):H("span",{className:"ai-score"},Math.round(x.score))),
      H("td",null,x.engagement_score==null?"—":`${Math.round(x.engagement_score)}%`),H("td",null,x.next_action||"—"),H("td",null,fmtDate(x.updated_at))
    )))
  ));
  return F(
    H(SectionHead,{eyebrow:"GROWTH / LEADS",title:"Revenue pipeline",action:H(Button,{variant:"primary",icon:"plus",onClick:()=>setShowAdd(true)},"Add Lead")}),
    H(Card,null,H("div",{className:"toolbar"},H("div",{className:"searchbox"},H(Icon,{name:"search",size:16}),H(Input,{value:q,onChange:e=>setQ(e.target.value),placeholder:"Search name, company, persona…","aria-label":"Search leads"})),H(Select,{value:status,onChange:e=>setStatus(e.target.value),"aria-label":"Filter lead status"},H("option",{value:""},"All statuses"),LEAD_STATUSES.map(s=>H("option",{value:s,key:s},s.replaceAll("_"," "))))),body),
    selected&&H(LeadDrawer,{lead:selected,notify,onClose:()=>setSelected(null),onSaved:async(stay=false,provider)=>{await state.reload();if(!stay)setSelected(null);notify(provider?`Lead qualified with ${provider}`:"Lead updated");}}),
    showAdd&&H(AddLead,{onClose:()=>setShowAdd(false),onSaved:async()=>{setShowAdd(false);await state.reload();notify("Lead created");}})
  );
}

function EventModal({onClose,onSaved}) {
  const [f,setF]=useState({name:"",target_persona:"",objective:"",event_date:"",status:"draft"}); const [error,setError]=useState("");
  async function save(e){e.preventDefault();try{await api.events.create({...f,event_date:f.event_date?new Date(f.event_date).toISOString():null});onSaved();}catch(x){setError(x.message);}}
  return H(Modal,{title:"Create event",onClose},H("form",{className:"form-stack",onSubmit:save},
    error&&H("div",{className:"form-error"},error),H(Field,{label:"Event name"},H(Input,{required:true,value:f.name,onChange:e=>setF({...f,name:e.target.value})})),
    H(Field,{label:"Target persona"},H(Input,{value:f.target_persona,onChange:e=>setF({...f,target_persona:e.target.value})})),H(Field,{label:"Objective"},H(Textarea,{rows:3,value:f.objective,onChange:e=>setF({...f,objective:e.target.value})})),
    H(Field,{label:"Event date"},H(Input,{type:"datetime-local",value:f.event_date,onChange:e=>setF({...f,event_date:e.target.value})})),
    H("div",{className:"modal-actions"},H(Button,{onClick:onClose},"Cancel"),H(Button,{type:"submit",variant:"primary"},"Create Event"))
  ));
}
function Events({notify}) {
  const state=useLoad(()=>api.events.list(),[]); const [show,setShow]=useState(false);
  const content=state.loading?H(Skeleton,{lines:5}):state.error?H(ErrorState,{message:state.error,onRetry:state.reload}):!state.data?.length?H(EmptyState,{title:"No events yet",description:"Create an event to coordinate attendee capture, qualification and follow-up."}):H("div",{className:"card-grid"},state.data.map(e=>H(Card,{key:e.id},
    H("div",{className:"card-top"},H(Status,{value:e.status}),H("span",{className:"muted small"},e.event_date?new Date(e.event_date).toLocaleDateString():"Date not set")),
    H("h3",null,e.name),H("p",{className:"muted"},e.objective||"No objective added."),H("div",{className:"meta-row"},H("span",null,"Persona"),H("strong",null,e.target_persona||"Not specified")),H("div",{className:"meta-row"},H("span",null,"Performance"),H("strong",{className:"muted"},"Not connected"))
  )));
  const flow=["EVENT","ATTENDEE CAPTURE","AI QUALIFICATION","SEGMENTATION","PERSONALIZED MESSAGE","HUMAN APPROVAL","OUTREACH","SIGNAL","FOLLOW-UP"];
  return F(H(SectionHead,{eyebrow:"GROWTH / EVENTS",title:"Event operations",action:H(Button,{variant:"primary",icon:"plus",onClick:()=>setShow(true)},"Create Event")}),H("div",{className:"flow-ribbon"},flow.flatMap((x,i)=>[H("span",{key:`s${i}`},x),i<flow.length-1?H("b",{key:`b${i}`},"→"):null])),content,show&&H(EventModal,{onClose:()=>setShow(false),onSaved:async()=>{setShow(false);await state.reload();notify("Event created");}}));
}

const TEMPLATE_DEF={steps:[
  {type:"trigger",config:{event:"event.attendee_captured"}},
  {type:"ai_classify",config:{output_key:"qualification",prompt:"Evaluate the prospect fit and buying intent using only this context: {{context}}"}},
  {type:"ai_generate",config:{output_key:"outreach_draft",json_mode:true,prompt:"Create concise personalized outreach using only verified facts in this context: {{context}}"}},
  {type:"human_approval",config:{action_type:"outreach",risk_level:"medium",editable_context_key:"outreach_draft",message:"Review the AI-generated outreach before execution."}},
  {type:"crm_update",config:{fields:{workflow_status:"approved_for_outreach"}}}
]};
function WorkflowCanvas({workflow}) {
  const steps=workflow.definition?.steps||[];
  return H(Card,{className:"canvas-card"},
    H("div",{className:"canvas-toolbar"},H("div",null,H("p",{className:"eyebrow"},"LINEAR EXECUTION GRAPH"),H("h3",null,workflow.name)),H("div",{className:"zoom"},H("span",null,"100%"))),
    H("div",{className:"canvas"},steps.flatMap((s,i)=>[
      H("div",{className:`node node-${s.type}`,key:`n${i}`},H("div",{className:"node-icon"},H(Icon,{name:s.type==="human_approval"?"approval":s.type.startsWith("ai_")?"insight":s.type==="crm_update"?"leads":"run"})),H("div",null,H("small",null,s.type.replaceAll("_"," ")),H("strong",null,nodeTitle(s.type)))),
      i<steps.length-1?H("div",{className:"connector",key:`c${i}`},"↓"):null
    ]),H("div",{className:"canvas-note"},"Branching, wait, webhook and outbound-send nodes are not enabled by the current backend engine and are intentionally not faked."))
  );
}
function WorkflowBuilder({workflow,onClose,onSaved}) {
  const initial=workflow||{name:"Untitled Growth Workflow",description:"",definition:{steps:[{type:"trigger",config:{event:"manual"}},{type:"human_approval",config:{action_type:"external_action",risk_level:"medium",message:"Review this action before continuing."}}]}};
  const [name,setName]=useState(initial.name); const [description,setDescription]=useState(initial.description||""); const [steps,setSteps]=useState((initial.definition?.steps||[]).map(x=>({...x,configText:JSON.stringify(x.config||{},null,2)}))); const [error,setError]=useState(""); const [busy,setBusy]=useState(false);
  const types=["trigger","ai_classify","ai_generate","human_approval","crm_update"];
  function update(i,key,value){setSteps(steps.map((x,idx)=>idx===i?{...x,[key]:value}:x));}
  function add(){setSteps([...steps,{type:"human_approval",configText:'{\n  "action_type": "external_action",\n  "risk_level": "medium",\n  "message": "Review before continuing."\n}'}]);}
  function move(i,delta){const j=i+delta;if(j<0||j>=steps.length)return;const next=[...steps];[next[i],next[j]]=[next[j],next[i]];setSteps(next);}
  async function save(e){e.preventDefault();setError("");try{const definition={steps:steps.map((x,i)=>{let config;try{config=JSON.parse(x.configText||"{}");}catch{throw new Error(`Step ${i+1} has invalid JSON configuration.`);}return {type:x.type,config};})};setBusy(true);if(workflow)await api.workflows.update(workflow.id,{name,description,definition});else await api.workflows.create({name,description,definition});onSaved();}catch(e){setError(e.message);}finally{setBusy(false);}}
  return H(Modal,{title:workflow?"Edit workflow":"Create workflow",onClose,wide:true},H("form",{className:"form-stack",onSubmit:save},error&&H("div",{className:"form-error"},error),H("div",{className:"builder-fields"},H(Field,{label:"Workflow name"},H(Input,{required:true,minLength:2,value:name,onChange:e=>setName(e.target.value)})),H(Field,{label:"Description"},H(Input,{value:description,onChange:e=>setDescription(e.target.value)}))),H("div",{className:"builder-head"},H("div",null,H("p",{className:"eyebrow"},"EXECUTION STEPS"),H("h3",null,"Linear workflow")),H(Button,{onClick:add,icon:"plus"},"Add Step")),H("div",{className:"builder-steps"},steps.map((step,i)=>H(Card,{key:i,className:"builder-step"},H("div",{className:"builder-step-top"},H("b",null,String(i+1).padStart(2,"0")),H(Select,{value:step.type,onChange:e=>update(i,"type",e.target.value)},types.map(t=>H("option",{key:t,value:t},nodeTitle(t)))),H("div",{className:"grow"}),H(Button,{variant:"ghost",onClick:()=>move(i,-1),disabled:i===0,title:"Move up"},"↑"),H(Button,{variant:"ghost",onClick:()=>move(i,1),disabled:i===steps.length-1,title:"Move down"},"↓"),H(Button,{variant:"ghost",onClick:()=>setSteps(steps.filter((_,idx)=>idx!==i)),disabled:steps.length===1},"Remove")),H(Field,{label:"Configuration (JSON)",hint:"Validated by the backend before the workflow is saved."},H(Textarea,{rows:6,value:step.configText,onChange:e=>update(i,"configText",e.target.value)}))))),H("div",{className:"modal-actions"},H(Button,{onClick:onClose},"Cancel"),H(Button,{type:"submit",variant:"primary",disabled:busy},busy?"Saving…":"Save Workflow"))));
}

function Workflows({notify}) {
  const state=useLoad(()=>api.workflows.list(),[]); const [selected,setSelected]=useState(null); const [busy,setBusy]=useState(false); const [builder,setBuilder]=useState(null);
  async function createTemplate(){setBusy(true);try{await api.workflows.create({name:"Event Lead Outreach",description:"Qualify an event attendee, draft outreach, pause for review, then update CRM.",definition:TEMPLATE_DEF});await state.reload();notify("Workflow created");}catch(e){notify(e.message,"danger");}finally{setBusy(false);}}
  let content;
  if(state.loading) content=H(Skeleton,{lines:5});
  else if(state.error) content=H(ErrorState,{message:state.error,onRetry:state.reload});
  else if(!state.data?.length) content=H(EmptyState,{title:"No workflows yet",description:"Create your first workflow to automate qualification and human-reviewed follow-up.",action:H(Button,{variant:"primary",onClick:createTemplate},"Create Workflow")});
  else content=H("div",{className:"workflow-layout"},
    H("div",{className:"workflow-list"},state.data.map(w=>H(Card,{key:w.id,className:`workflow-card ${selected?.id===w.id?"selected":""}`},
      H("button",{className:"workflow-select",onClick:()=>setSelected(w)},H("div",{className:"card-top"},H(Status,{value:w.active?"running":"draft"}),H("span",{className:"muted small"},`v${w.version}`)),H("h3",null,w.name),H("p",{className:"muted"},w.description||"No description")),
      H("div",{className:"inline-actions"},H(Button,{variant:"ghost",onClick:()=>setBuilder(w)},"Edit"),H(Button,{variant:"ghost",onClick:async()=>{try{await api.workflows.create({name:`${w.name} Copy`,description:w.description,definition:w.definition});await state.reload();notify("Workflow duplicated");}catch(e){notify(e.message,"danger");}}},"Duplicate"),H(Button,{variant:"ghost",onClick:async()=>{await api.workflows.activate(w.id,!w.active);await state.reload();notify(w.active?"Workflow deactivated":"Workflow activated");}},w.active?"Deactivate":"Activate"),H(Button,{variant:"ghost",icon:"run",onClick:async()=>{try{const r=await api.workflows.run(w.id,{input:{source:"manual_test"},idempotency_key:`ui-${Date.now()}`});notify(`Run ${r.status}`);}catch(e){notify(e.message,"danger");}}},"Test"))
    ))),selected?H(WorkflowCanvas,{workflow:selected}):H(Card,{className:"canvas-card"},H(EmptyState,{title:"Select a workflow",description:"Inspect its registered nodes and execution order here."}))
  );
  return F(H(SectionHead,{eyebrow:"AUTOMATION / WORKFLOWS",title:"Workflow studio",action:H("div",{className:"hero-actions"},H(Button,{onClick:createTemplate,disabled:busy},busy?"Creating…":"Quick Template"),H(Button,{variant:"primary",icon:"plus",onClick:()=>setBuilder({new:true})},"Create Workflow"))}),content,builder&&H(WorkflowBuilder,{workflow:builder.new?null:builder,onClose:()=>setBuilder(null),onSaved:async()=>{setBuilder(null);await state.reload();notify(builder.new?"Workflow created":"Workflow updated");}}));
}

function Runs({notify}) {
  const state = useLoad(() => api.workflows.runs(), []);
  const [detail,setDetail] = useState(null);
  async function open(id) {
    setDetail({loading:true});
    try { setDetail(await api.workflows.runDetail(id)); }
    catch (e) { setDetail({error:e.message}); }
  }
  let content;
  if (state.loading) content = H(Skeleton,{lines:6});
  else if (state.error) content = H(ErrorState,{message:state.error,onRetry:state.reload});
  else if (!state.data?.length) content = H(EmptyState,{title:"No workflow runs",description:"Execution history appears here after a workflow is tested or triggered."});
  else content = H(Card,null,
    H("div",{className:"table-wrap"},
      H("table",{className:"data-table"},
        H("thead",null,H("tr",null,["Run","Status","Trigger","Current step","Started","Completed"].map(x=>H("th",{key:x},x)))),
        H("tbody",null,state.data.map(r=>H("tr",{key:r.id,onClick:()=>open(r.id)},
          H("td",null,H("code",null,r.id.slice(0,8))),
          H("td",null,H(Status,{value:r.status})),
          H("td",null,r.trigger_type),
          H("td",null,r.current_node?nodeTitle(r.current_node):"—"),
          H("td",null,fmtDate(r.started_at)),
          H("td",null,fmtDate(r.completed_at))
        )))
      )
    )
  );
  let drawer = null;
  if (detail) {
    let drawerContent;
    if (detail.loading) drawerContent = H(Skeleton,{lines:5});
    else if (detail.error) drawerContent = H(ErrorState,{message:detail.error});
    else drawerContent = F(
      H("div",{className:"detail-grid"},
        H(Info,{label:"Status",value:detail.status}),
        H(Info,{label:"Trigger",value:detail.trigger_type}),
        H(Info,{label:"Started",value:fmtDate(detail.started_at)}),
        H(Info,{label:"Completed",value:fmtDate(detail.completed_at)})
      ),
      detail.error && H("div",{className:"form-error"},detail.error),
      detail.status==="failed"&&H(Button,{variant:"primary",icon:"refresh",onClick:async()=>{try{const r=await api.workflows.retry(detail.id);notify(`Retry ${r.status}`);open(detail.id);}catch(e){notify(e.message,"danger");}}},"Retry Failed Run"),
      H("div",{className:"timeline"},(detail.steps||[]).map(s=>H("div",{className:"timeline-item run-step",key:s.step_index},
        H("span",{className:`timeline-dot ${s.status}`}),
        H("div",{className:"grow"},H("strong",null,nodeTitle(s.node_type)),H("small",null,`${fmtDate(s.started_at)}${s.completed_at?` → ${fmtDate(s.completed_at)}`:""}`),s.error&&H("div",{className:"form-error"},s.error),H("details",null,H("summary",null,"Inspect input / output"),H("pre",{className:"step-payload"},JSON.stringify({input:s.input,output:s.output},null,2)))),
        H(Status,{value:s.status})
      )))
    );
    drawer = H(Drawer,{title:"Execution timeline",onClose:()=>setDetail(null)},drawerContent);
  }
  return F(H(SectionHead,{eyebrow:"AUTOMATION / RUNS",title:"Workflow execution"}),content,drawer);
}

function ApprovalEdit({approval,onClose,onApprove}) {
  const original=approval.payload?.editable_value; const [text,setText]=useState(typeof original==="string"?original:JSON.stringify(original,null,2));
  function value(){if(typeof original==="string")return text;try{return JSON.parse(text);}catch{return text;}}
  return H(Modal,{title:"Edit approval content",onClose,wide:true},
    H(Field,{label:"AI-generated content",hint:"Review carefully. AI output is untrusted until approved."},H(Textarea,{rows:14,value:text,onChange:e=>setText(e.target.value)})),
    H("div",{className:"modal-actions"},H(Button,{onClick:onClose},"Cancel"),H(Button,{variant:"primary",onClick:()=>onApprove(value())},"Approve & Continue"))
  );
}
function Approvals({notify}) {
  const state=useLoad(()=>api.approvals.list(),[]); const [editing,setEditing]=useState(null);
  async function act(id,kind,value){try{if(kind==="approve")await api.approvals.approve(id,{execute:true,edited_value:value});else await api.approvals.reject(id,{comment:"Rejected from Approval Center"});notify(kind==="approve"?"Approval approved and workflow resumed":"Approval rejected");setEditing(null);await state.reload();}catch(e){notify(e.message,"danger");}}
  const content=state.loading?H(Skeleton,{lines:6}):state.error?H(ErrorState,{message:state.error,onRetry:state.reload}):!state.data?.length?H(EmptyState,{title:"Approval queue is clear",description:"When a workflow reaches a human review node, the action will appear here before execution."}):H("div",{className:"approval-grid"},state.data.map(a=>{
    const editable=a.payload?.editable_value;
    return H(Card,{key:a.id,className:"approval-card"},H("div",{className:"card-top"},H(Status,{value:a.status}),H(Badge,{tone:a.risk_level==="high"?"danger":"warning"},`${a.risk_level} risk`)),H("p",{className:"eyebrow"},a.action_type.toUpperCase()),H("h3",null,a.payload?.message||"Review requested"),H("p",{className:"muted small"},`Created ${fmtDate(a.created_at)}`),editable!=null&&H("pre",{className:"draft-preview"},typeof editable==="string"?editable:JSON.stringify(editable,null,2)),H("div",{className:"approval-actions"},H(Button,{variant:"danger",icon:"x",onClick:()=>act(a.id,"reject")},"Reject"),editable!=null&&H(Button,{onClick:()=>setEditing(a)},"Edit"),H(Button,{variant:"primary",icon:"check",onClick:()=>act(a.id,"approve")},"Approve & Continue")));
  }));
  return F(H(SectionHead,{eyebrow:"AUTOMATION / APPROVAL CENTER",title:"Human review queue"}),content,editing&&H(ApprovalEdit,{approval:editing,onClose:()=>setEditing(null),onApprove:v=>act(editing.id,"approve",v)}));
}

function MeetingIntelligence({notify}) {
  const [notes,setNotes]=useState(""); const [result,setResult]=useState(null); const [busy,setBusy]=useState(false); const [error,setError]=useState("");
  async function analyze(){if(notes.trim().length<20){setError("Paste at least a short set of meeting notes first.");return;}setBusy(true);setError("");try{setResult(await api.ai.meeting({notes}));}catch(e){setError(e.message);}finally{setBusy(false);}}
  async function approve(){try{await api.approvals.create({action_type:"meeting_follow_up",risk_level:"medium",title:"Review meeting follow-up draft",value:result.output.follow_up_draft,context:{source:"meeting_intelligence"}});notify("Follow-up sent to Approval Center");}catch(e){notify(e.message,"danger");}}
  const out=result?.output;
  const list=(title,items)=>H(Card,{className:"analysis-section"},H("p",{className:"eyebrow"},title),items?.length?H("ul",null,items.map(x=>H("li",{key:x},x))):H("p",{className:"muted"},"No grounded items identified."));
  return F(
    H(SectionHead,{eyebrow:"INTELLIGENCE / MEETINGS",title:"Meeting Intelligence"}),
    H("div",{className:"two-col meeting-layout"},
      H(Card,null,H("p",{className:"eyebrow"},"SOURCE"),H("h3",null,"Turn a conversation into operating context"),H("p",{className:"muted"},"Paste meeting notes or a transcript. The result stays grounded in the text you provide."),H(Textarea,{rows:18,value:notes,onChange:e=>setNotes(e.target.value),placeholder:"Paste meeting notes or transcript…","aria-label":"Meeting notes"}),H("div",{className:"modal-actions"},H(Button,{variant:"primary",onClick:analyze,disabled:busy},busy?"Analyzing…":"Analyze Meeting")),error&&H(ErrorState,{message:error}),busy&&H("div",{className:"ai-processing"},H("span",{className:"spinner"}),"AI is analyzing your meeting…")),
      H(Card,{className:"meeting-summary"},!out?H(EmptyState,{title:"Analysis will appear here",description:"Summary, decisions, action items, signals, CRM updates and content opportunities are generated only after you analyze supplied notes."}):F(H("div",{className:"card-top"},H(Badge,{tone:"info"},result.provider),result.fallback&&H(Badge,{tone:"warning"},"secondary provider")),H("p",{className:"eyebrow"},"SUMMARY"),H("h3",null,out.summary),H("div",{className:"confidence"},H("span",null,"Confidence"),H("strong",null,`${Math.round((out.confidence||0)*100)}%`)),H("div",{className:"draft-block"},H("p",{className:"eyebrow"},"FOLLOW-UP DRAFT"),H("p",null,out.follow_up_draft),H(Button,{variant:"primary",onClick:approve},"Create Approval"))))
    ),
    out&&H("div",{className:"analysis-grid"},list("KEY DECISIONS",out.key_decisions),list("ACTION ITEMS",out.action_items),list("BUYING SIGNALS",out.buying_signals),list("RISKS",out.risks),list("CRM UPDATES",out.crm_updates),list("CONTENT OPPORTUNITIES",out.content_opportunities))
  );
}

function ContentStudio({notify}) {
  const [source,setSource]=useState(""); const [tone,setTone]=useState("professional"); const [result,setResult]=useState(null); const [drafts,setDrafts]=useState({}); const [busy,setBusy]=useState(false); const [error,setError]=useState(""); const [tab,setTab]=useState("linkedin_post");
  const tabs={linkedin_post:"LinkedIn",short_post:"Short post",long_form_post:"Long-form",newsletter:"Newsletter",campaign_idea:"Campaign idea"};
  async function generate(instruction=null){if(source.trim().length<3){setError("Add an idea, conversation or meeting insight first.");return;}setBusy(true);setError("");try{const next=await api.ai.content({source,tone,instruction});setResult(next);setDrafts(next.output||{});}catch(e){setError(e.message);}finally{setBusy(false);}}
  async function copy(){const text=drafts[tab];if(!text)return;try{await navigator.clipboard.writeText(text);notify("Copied to clipboard");}catch{notify("Clipboard is unavailable in this browser","danger");}}
  async function approve(){try{await api.approvals.create({action_type:"content",risk_level:"medium",title:`Review ${tabs[tab]} draft`,value:drafts[tab],context:{content_type:tab}});notify("Draft sent to Approval Center");}catch(e){notify(e.message,"danger");}}
  return F(H(SectionHead,{eyebrow:"GROWTH / CONTENT",title:"Content Studio"}),H("div",{className:"studio-layout"},
    H(Card,{className:"studio-input"},H("p",{className:"eyebrow"},"SOURCE CONTEXT"),H("h3",null,"Turn working context into publishable drafts"),H(Textarea,{rows:12,value:source,onChange:e=>setSource(e.target.value),placeholder:"Paste an idea, customer insight, event note or conversation…"}),H(Field,{label:"Tone"},H(Select,{value:tone,onChange:e=>setTone(e.target.value)},["professional","clear and concise","thought leadership","warm","analytical"].map(x=>H("option",{key:x,value:x},x)))),H(Button,{variant:"primary",onClick:()=>generate(),disabled:busy},busy?"Generating…":"Generate Content"),error&&H(ErrorState,{message:error}),H("p",{className:"muted small"},"No external publishing occurs from this page. Approved provider connections can be added later.")),
    H(Card,{className:"studio-output"},!result?H(EmptyState,{title:"Choose a source and generate",description:"You’ll get multiple reusable content formats without pretending anything was published."}):F(H("div",{className:"tabs"},Object.entries(tabs).map(([key,label])=>H("button",{key,className:tab===key?"active":"",onClick:()=>setTab(key)},label))),H(Textarea,{className:"content-editor",rows:16,value:drafts[tab]||"",onChange:e=>setDrafts(prev=>({...prev,[tab]:e.target.value})),"aria-label":`${tabs[tab]} draft`}),H("div",{className:"content-actions"},H(Button,{onClick:copy},"Copy"),H(Button,{onClick:()=>generate("Improve clarity and structure while preserving facts.")},"Improve"),H(Button,{onClick:()=>generate("Shorten the output while preserving the core point.")},"Shorten"),H(Button,{variant:"primary",onClick:approve},"Send to Approval")),H("small",{className:"muted"},`Generated with ${result.provider}${result.fallback?" via secondary provider":""}.`)))
  ));
}

function SearchModal({onClose,go}) {
  const [q,setQ]=useState(""); const [busy,setBusy]=useState(false); const [results,setResults]=useState([]); const [error,setError]=useState("");
  async function search(value=q){setQ(value);if(value.trim().length<2){setResults([]);return;}setBusy(true);setError("");try{const [leads,events,workflows]=await Promise.all([api.leads.list(`?page_size=8&q=${encodeURIComponent(value)}`),api.events.list(),api.workflows.list()]);const needle=value.toLowerCase();setResults([...(leads.items||[]).map(x=>({type:"Lead",label:x.name,meta:x.company||x.email,route:"leads"})),...events.filter(x=>`${x.name} ${x.objective||""}`.toLowerCase().includes(needle)).slice(0,5).map(x=>({type:"Event",label:x.name,meta:x.status,route:"events"})),...workflows.filter(x=>`${x.name} ${x.description||""}`.toLowerCase().includes(needle)).slice(0,5).map(x=>({type:"Workflow",label:x.name,meta:x.active?"Active":"Inactive",route:"workflows"}))]);}catch(e){setError(e.message);}finally{setBusy(false);}}
  useEffect(()=>{const id=setTimeout(()=>search(q),250);return()=>clearTimeout(id);},[q]);
  return H(Modal,{title:"Search workspace",onClose,wide:true},H("div",{className:"searchbox modal-search"},H(Icon,{name:"search",size:17}),H(Input,{autoFocus:true,value:q,onChange:e=>setQ(e.target.value),placeholder:"Search leads, events and workflows…"})),busy&&H(Skeleton,{lines:3}),error&&H(ErrorState,{message:error}),!busy&&q.length>=2&&!results.length&&H(EmptyState,{title:"No matches",description:"Try a lead name, company, event or workflow."}),H("div",{className:"search-results"},results.map((x,i)=>H("button",{key:`${x.type}-${x.label}-${i}`,onClick:()=>{go(x.route);onClose();}},H(Badge,{tone:"neutral"},x.type),H("div",{className:"grow"},H("strong",null,x.label),H("small",null,x.meta||"")),H("span",null,"→")))));
}

function Analytics() {
  const [days,setDays]=useState(30); const state=useLoad(()=>api.analytics(days),[days]);
  if(state.loading)return F(H(SectionHead,{eyebrow:"ANALYTICS / PERFORMANCE",title:"Growth performance"}),H(Skeleton,{lines:6}));
  if(state.error)return F(H(SectionHead,{eyebrow:"ANALYTICS / PERFORMANCE",title:"Growth performance"}),H(ErrorState,{message:state.error,onRetry:state.reload}));
  const data=state.data;
  return F(
    H(SectionHead,{eyebrow:"ANALYTICS / PERFORMANCE",title:"Growth performance",action:H("div",{className:"segmented"},[7,30,90].map(d=>H("button",{key:d,className:days===d?"active":"",onClick:()=>setDays(d)},`${d}D`)))}),
    H("div",{className:"metric-grid four"},H(MetricCard,{label:"Qualification Rate",metric:data.metrics.qualification_rate,format:pct}),H(MetricCard,{label:"Conversion Rate",metric:data.metrics.conversion_rate,format:pct}),H(MetricCard,{label:"Workflow Success",metric:data.metrics.automation_success_rate,format:pct}),H(MetricCard,{label:"AI Requests",metric:data.metrics.ai_requests})),
    H("div",{className:"two-col"},
      H(Card,null,H(SectionHead,{eyebrow:"LEAD FUNNEL",title:"Pipeline distribution"}),H("div",{className:"bar-chart"},Object.entries(data.funnel).map(([k,v])=>{const max=Math.max(1,...Object.values(data.funnel));return H("div",{className:"bar-row",key:k},H("span",null,k.replaceAll("_"," ")),H("div",{className:"bar-track"},H("i",{style:{width:`${v/max*100}%`}})),H("strong",null,v));}))),
      H(Card,null,H(SectionHead,{eyebrow:"WORKFLOW HEALTH",title:"Execution status"}),H("div",{className:"donut-wrap"},H("div",{className:"donut"},H("div",null,H("strong",null,Object.values(data.run_status).reduce((a,b)=>a+b,0)),H("span",null,"runs"))),H("div",{className:"legend"},Object.entries(data.run_status).map(([k,v])=>H("div",{key:k},H("span",{className:`legend-dot ${k}`}),H("span",null,k.replaceAll("_"," ")),H("strong",null,v))))))
    )
  );
}

function Settings({user,runtime}) {
  const integrations=useLoad(()=>api.integrations(),[]);
  const audit=useLoad(()=>api.audit(),[]);
  const aiReady=runtime?.ai_ready===true;
  let integrationContent;
  if(integrations.loading) integrationContent=H(Skeleton,{lines:4});
  else if(integrations.error) integrationContent=H(ErrorState,{message:integrations.error,onRetry:integrations.reload});
  else integrationContent=H("div",{className:"card-grid"},(integrations.data?.items||[]).map(x=>H(Card,{key:x.id},
    H("div",{className:"card-top"},H("p",{className:"eyebrow"},x.category),H(Status,{value:x.status})),
    H("h3",null,x.name),H("p",{className:"muted"},x.detail)
  )));
  let auditContent;
  if(audit.loading) auditContent=H(Skeleton,{lines:4});
  else if(audit.error) auditContent=H(ErrorState,{message:audit.error,onRetry:audit.reload});
  else if(!audit.data?.length) auditContent=H(EmptyState,{title:"No audit activity yet",description:"Live user and workflow changes will be recorded here."});
  else auditContent=H(Card,null,H("div",{className:"timeline"},audit.data.slice(0,12).map(x=>H("div",{className:"timeline-item",key:x.id},
    H("span",{className:"timeline-dot completed"}),
    H("div",{className:"grow"},H("strong",null,x.action.replaceAll("."," · ")),H("small",null,x.resource_type)),
    H("span",{className:"muted small"},fmtDate(x.created_at))
  ))));
  return F(
    H(SectionHead,{eyebrow:"SYSTEM",title:"Settings & Connections"}),
    H("div",{className:"two-col"},
      H(Card,null,H("p",{className:"eyebrow"},"WORKSPACE"),H("h3",null,user?.name||"Workspace user"),H("p",{className:"muted"},user?.email),H("div",{className:"meta-row"},H("span",null,"Role"),H("strong",null,user?.role||"member"))),
      H(Card,null,H("p",{className:"eyebrow"},"LIVE AI"),H("div",{className:"card-top"},H("h3",null,aiReady?"AI provider configured":"AI provider not configured"),H(Badge,{tone:aiReady?"success":"warning"},aiReady?(runtime?.ai_provider||"AI"):"key required")),H("p",{className:"muted"},aiReady?"AI calls run server-side against your configured provider. Human approval still controls external actions.":"Add GEMINI_API_KEY or GROQ_API_KEY to .env. No paid OpenAI or Anthropic key is required."),H("div",{className:"meta-row"},H("span",null,"Provider"),H("strong",null,runtime?.ai_provider||"Loading…")),H("div",{className:"meta-row"},H("span",null,"Model"),H("strong",null,runtime?.ai_model||"—")))
    ),
    H(SectionHead,{eyebrow:"CONNECTIONS",title:"Live data & optional integrations"}),
    integrationContent,
    H(SectionHead,{eyebrow:"SECURITY",title:"Recent audit activity"}),
    auditContent
  );
}

export default function App() {
  const [authed,setAuthed] = useState(Boolean(getToken()));
  const [user,setUser] = useState(null);
  const [route,setRoute] = useState(routeFromHash());
  const [sidebar,setSidebar] = useState(false);
  const [collapsed,setCollapsed] = useState(false);
  const [toast,setToast] = useState(null);
  const [pending,setPending] = useState(0);
  const [runtime,setRuntime] = useState(null);
  const [searchOpen,setSearchOpen] = useState(false);

  const notify = (message,tone="success") => {
    setToast({message,tone});
    setTimeout(() => setToast(null), 3000);
  };

  useEffect(() => {
    const fn = () => setRoute(routeFromHash());
    const unauthorized = () => { setAuthed(false); setUser(null); };
    const keys = e => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); if (authed) setSearchOpen(true); } };
    addEventListener("hashchange", fn); addEventListener("aigrowth:unauthorized", unauthorized); addEventListener("keydown", keys);
    return () => { removeEventListener("hashchange", fn); removeEventListener("aigrowth:unauthorized", unauthorized); removeEventListener("keydown", keys); };
  }, [authed]);

  useEffect(() => {
    if (!authed) return;
    api.auth.me().then(setUser).catch(e => {
      if (e.status === 401) { setToken(null); setAuthed(false); }
    });
    api.approvals.list().then(x => setPending(x.length)).catch(() => {});
    api.runtime().then(setRuntime).catch(() => setRuntime(null));
  }, [authed,route]);

  function go(r) { location.hash = `#/${r}`; setSidebar(false); }
  function logout() { setToken(null); setAuthed(false); setUser(null); }
  if (!authed) return H(Auth,{onAuth:()=>setAuthed(true)});

  const props = {go,notify,user,runtime};
  let page;
  if (route === "dashboard") page = H(Dashboard,props);
  else if (route === "leads") page = H(Leads,props);
  else if (route === "events") page = H(Events,props);
  else if (route === "workflows") page = H(Workflows,props);
  else if (route === "runs") page = H(Runs,props);
  else if (route === "approvals") page = H(Approvals,props);
  else if (route === "meeting-intelligence") page = H(MeetingIntelligence,props);
  else if (route === "content") page = H(ContentStudio,props);
  else if (route === "analytics") page = H(Analytics,props);
  else if (route === "settings") page = H(Settings,props);
  else page = H(Dashboard,props);

  const nav = H("nav",null,
    NAV.map((group,gi) => H("div",{className:"nav-group",key:gi},
      group.group && H("p",null,group.group),
      group.items.map(([key,label,icon]) => H("button",{
        key,
        onClick:()=>go(key),
        className:route === key ? "nav-item active" : "nav-item",
        title:label
      },
        H(Icon,{name:icon,size:17}),
        H("span",null,label),
        key === "approvals" && pending > 0 && H("b",null,pending)
      ))
    ))
  );

  const sidebarNode = H("aside",{className:`sidebar ${sidebar ? "open" : ""} ${collapsed ? "collapsed" : ""}`},
    H("div",{className:"brand"},
      H("div",{className:"brand-mark"},"A"),
      H("div",{className:"brand-copy"},H("strong",null,"Aster Growth"),H("small",null,"AI Operations OS")),
      H("button",{className:"collapse-button",onClick:()=>setCollapsed(!collapsed),title:collapsed?"Expand sidebar":"Collapse sidebar","aria-label":collapsed?"Expand sidebar":"Collapse sidebar"},collapsed?"›":"‹")
    ),
    nav,
    H("div",{className:"sidebar-foot"},
      H("div",{className:"avatar"},(user?.name || "U").slice(0,2).toUpperCase()),
      H("div",{className:"grow"},H("strong",null,user?.name || "User"),H("small",null,user?.role || "member")),
      H(Button,{variant:"ghost",icon:"logout",onClick:logout,title:"Log out"})
    )
  );

  const topbar = H("header",{className:"topbar"},
    H(Button,{variant:"ghost",icon:"menu",className:"mobile-menu",onClick:()=>setSidebar(!sidebar),title:"Menu"}),
    H("div",{className:"breadcrumb"},H("span",null,"AI Growth OS"),H("b",null,"/"),H("strong",null,TITLES[route] || "Dashboard")),
    H("div",{className:"top-actions"},
      H("button",{className:"global-search",onClick:()=>setSearchOpen(true),"aria-label":"Search workspace"},H(Icon,{name:"search",size:15}),H("span",null,"Search workspace"),H("kbd",null,"⌘K")),
      H("span",{className:`system-online ${runtime?.ai_ready?"":"offline"}`},H("i"),runtime?.ai_ready?`${runtime.ai_provider} online`:"AI not configured"),
      H("button",{className:"icon-button",onClick:()=>go("approvals"),"aria-label":`${pending} pending approvals`},
        H(Icon,{name:"bell",size:18}),
        pending > 0 && H("b",null,pending)
      ),
      H("div",{className:"avatar top-avatar"},(user?.name || "U").slice(0,2).toUpperCase())
    )
  );

  return H("div",{className:`app-shell ${collapsed ? "sidebar-collapsed" : ""}`},
    sidebarNode,
    H("div",{className:"main-shell"},topbar,H("main",{className:"content"},page)),
    sidebar && H("div",{className:"sidebar-scrim",onClick:()=>setSidebar(false)}),
    searchOpen&&H(SearchModal,{onClose:()=>setSearchOpen(false),go}),
    H(Toast,{toast})
  );
}
