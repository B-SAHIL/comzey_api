from api.models import ProjectWorker
from projectdailylogs.models import DailyLog
from projectplans.models import Plan
from projecttasks.models import Task
from projectdocuments.models import  EOT, ROI,   EOTReceiver,  IncidentReport, PunchList, PunchListReceiver, ROIReceiver, Safety, SiteRiskAssessment, Document, ToolBox, ToolBoxReceiver, VariationReceiver, Variations

def builder_count(self, request, count,*args, **kwargs):
    variations=(len(VariationReceiver.objects.filter(
                receiver=self.request.user,
                variation__project=request.query_params['project_id'],receiver_watch="false"))+
                len(Variations.objects.filter(
                sender=self.request.user,
                project=request.query_params['project_id'],sender_watch="false")))
    eot=(len(EOTReceiver.objects.filter(
                receiver=self.request.user,
                eot__project=request.query_params['project_id'],receiver_watch="false"))+
                len(EOT.objects.filter(
                sender=self.request.user,
                project=request.query_params['project_id'],sender_watch="false")))
    toolbox=(len(ToolBoxReceiver.objects.filter(
                receiver=self.request.user,
                toolbox__project=request.query_params['project_id'],receiver_watch="false"))+
                len(ToolBox.objects.filter(
                sender=self.request.user,
                project=request.query_params['project_id'],sender_watch="false")))
    roi=(len(ROIReceiver.objects.filter(
                receiver=self.request.user,
                roi__project=request.query_params['project_id'],receiver_watch="false"))+
                len(ROI.objects.filter(
                sender=self.request.user,
                project=request.query_params['project_id'],sender_watch="false")))
    punchlist=(len(PunchListReceiver.objects.filter(
                receiver=self.request.user,
                punchlist__project=request.query_params['project_id'],receiver_watch="false"))+
                len(PunchList.objects.filter(
                sender=self.request.user,
                project=request.query_params['project_id'],sender_watch="false")))
    general_total=punchlist+roi+eot+toolbox 
    plan=Plan.objects.filter(project__builder=self.request.user,
                project=request.query_params['project_id'],builder_watch="false")
    docs=Document.objects.filter(project__builder=self.request.user,
        project=request.query_params['project_id'],builder_watch="false")
    people=ProjectWorker.objects.filter(project__builder=self.request.user,
        project=request.query_params['project_id'],builder_watch="false")
    task=Task.objects.filter(project__builder=self.request.user,
                project=request.query_params['project_id'],builder_watch="false")
    schedule=Task.objects.filter(project__builder=self.request.user,
                project=request.query_params['project_id'],builder_watch_schedule="false",
                worker_action="accepted")
    daily_work_report=DailyLog.objects.filter(project__builder=self.request.user,
                project=request.query_params['project_id'],builder_watch="false") 
    site_risk_assessment=len(SiteRiskAssessment.objects.filter(
                project__builder=self.request.user,
                project=request.query_params['project_id'],builder_watch="false"))      
    payload={"all_count":{"plan":len(plan),
            "docs":{"docs_total":len(docs)+general_total+site_risk_assessment+variations,
                "specifications_and_product_information":len(Document.objects.filter(
                project__builder=self.request.user,project=request.query_params['project_id'],
                builder_watch="false",type="specifications_and_product_information")),
                "safety":{"safety_total":site_risk_assessment,
                    "safe_work_method_statement":0,
                    "material_safety_data_sheets":0,
                    "work_health_and_safety_plan":0,
                    "site_risk_assessment":site_risk_assessment,
                    "incident_report":0},
                "variations":variations,
                "general":{"general_total":general_total,
                    "toolbox":toolbox,
                    "roi":roi,
                    "eot":eot,
                    "punchlist":punchlist}},
            "people":len(people),
            "daily":{"daily_total":len(task)+len(schedule)+len(daily_work_report),
                "task":len(task),
                "schedule":len(schedule),
                "daily_work_report":len(daily_work_report)
            }}}

    payload.update(count)
    return payload
  
def worker_count(self, request, count,*args, **kwargs):
    variations=(len(VariationReceiver.objects.filter(
                receiver=self.request.user,
                variation__project=request.query_params['project_id'],receiver_watch="false"))+
                len(Variations.objects.filter(
                sender=self.request.user,
                project=request.query_params['project_id'],sender_watch="false")))
    eot=(len(EOTReceiver.objects.filter(
                receiver=self.request.user,
                eot__project=request.query_params['project_id'],receiver_watch="false"))+
                len(EOT.objects.filter(
                sender=self.request.user,
                project=request.query_params['project_id'],sender_watch="false")))
    toolbox=(len(ToolBoxReceiver.objects.filter(
                receiver=self.request.user,
                toolbox__project=request.query_params['project_id'],receiver_watch="false"))+
                len(ToolBox.objects.filter(
                sender=self.request.user,
                project=request.query_params['project_id'],sender_watch="false")))
    roi=(len(ROIReceiver.objects.filter(
                receiver=self.request.user,
                roi__project=request.query_params['project_id'],receiver_watch="false"))+
                len(ROI.objects.filter(
                sender=self.request.user,
                project=request.query_params['project_id'],sender_watch="false")))
    punchlist=(len(PunchListReceiver.objects.filter(
                receiver=self.request.user,
                punchlist__project=request.query_params['project_id'],receiver_watch="false"))+
                len(PunchList.objects.filter(
                sender=self.request.user,
                project=request.query_params['project_id'],sender_watch="false")))
    general_total=punchlist+roi+eot+toolbox 
    plan=Plan.objects.filter(project__worker=self.request.user,
        project=request.query_params['project_id'],worker_watch="false")
    docs=Document.objects.filter(project__worker=self.request.user,
        project=request.query_params['project_id'],worker_watch="false")
    people=ProjectWorker.objects.filter(project__worker=self.request.user,
        project=request.query_params['project_id'],worker_watch="false")
    task=Task.objects.filter(project__worker=self.request.user,
                project=request.query_params['project_id'],worker_watch="false")
    schedule=Task.objects.filter(project__worker=self.request.user,
                project=request.query_params['project_id'],worker_watch_schedule="false",
                worker_action="accepted")
    daily_work_report=DailyLog.objects.filter(project__worker=self.request.user,
                project=request.query_params['project_id'],worker_watch="false")
    safe_work_method_statement=len(Safety.objects.filter(
                project__worker=self.request.user,project=request.query_params['project_id'],
                worker_watch="false",type="safe_work_method_statement"))
    material_safety_data_sheets=len(Safety.objects.filter(
                project__worker=self.request.user,project=request.query_params['project_id'],
                worker_watch="false",type="material_safety_data_sheets"))
    work_health_and_safety_plan=len(Safety.objects.filter(
                project__worker=self.request.user,project=request.query_params['project_id'],
                worker_watch="false",type="work_health_and_safety_plan"))
    site_risk_assessment=len(SiteRiskAssessment.objects.filter(
                assigned_to=self.request.user,
                project=request.query_params['project_id'],assigned_to_watch="false"))
    incident_report=(len(IncidentReport.objects.filter(
                person_completing_form=self.request.user,
                project=request.query_params['project_id'],person_completing_form_watch="false"))+
                len(IncidentReport.objects.filter(
                witness_of_incident=self.request.user,
                project=request.query_params['project_id'],witness_of_incident_watch="false")))
    safety_total=safe_work_method_statement+material_safety_data_sheets+work_health_and_safety_plan+site_risk_assessment+incident_report

    payload={"all_count":{"plan":len(plan),
            "docs":{"docs_total":len(docs)+general_total+safety_total+variations,
                "specifications_and_product_information":len(Document.objects.filter(
                project__worker=self.request.user,project=request.query_params['project_id'],
                worker_watch="false",type="specifications_and_product_information")),
                "safety":{"safety_total":safety_total,
                    "safe_work_method_statement":safe_work_method_statement,
                    "material_safety_data_sheets":material_safety_data_sheets,
                    "work_health_and_safety_plan":work_health_and_safety_plan,
                    "site_risk_assessment":site_risk_assessment,
                    "incident_report":incident_report},
                "variations":variations,
                "general":{"general_total":general_total,
                    "toolbox":toolbox,
                    "roi":roi,
                    "eot":eot,
                    "punchlist":punchlist}},
            "people":len(people),
            "daily":{"daily_total":len(task)+len(schedule)+len(daily_work_report),
                "task":len(task),
                "schedule":len(schedule),
                "daily_work_report":len(daily_work_report)
            }}}
    payload.update(count)
    return payload

def client_count(self, request, count,*args, **kwargs):
    variations=(len(VariationReceiver.objects.filter(
                receiver=self.request.user,
                variation__project=request.query_params['project_id'],receiver_watch="false"))+
                len(Variations.objects.filter(
                sender=self.request.user,
                project=request.query_params['project_id'],sender_watch="false")))
    eot=(len(EOTReceiver.objects.filter(
                receiver=self.request.user,
                eot__project=request.query_params['project_id'],receiver_watch="false"))+
                len(EOT.objects.filter(
                sender=self.request.user,
                project=request.query_params['project_id'],sender_watch="false")))
    toolbox=(len(ToolBoxReceiver.objects.filter(
                receiver=self.request.user,
                toolbox__project=request.query_params['project_id'],receiver_watch="false"))+
                len(ToolBox.objects.filter(
                sender=self.request.user,
                project=request.query_params['project_id'],sender_watch="false")))
    roi=(len(ROIReceiver.objects.filter(
                receiver=self.request.user,
                roi__project=request.query_params['project_id'],receiver_watch="false"))+
                len(ROI.objects.filter(
                sender=self.request.user,
                project=request.query_params['project_id'],sender_watch="false")))
    punchlist=(len(PunchListReceiver.objects.filter(
                receiver=self.request.user,
                punchlist__project=request.query_params['project_id'],receiver_watch="false"))+
                len(PunchList.objects.filter(
                sender=self.request.user,
                project=request.query_params['project_id'],sender_watch="false")))
    general_total=punchlist+roi+eot+toolbox 
    plan=Plan.objects.filter(project__client=self.request.user,
        project=request.query_params['project_id'],client_watch="false")
    docs=Document.objects.filter(project__client=self.request.user,
        project=request.query_params['project_id'],client_watch="false")
    people=ProjectWorker.objects.filter(project__client=self.request.user,
        project=request.query_params['project_id'],client_watch="false")
    task=Task.objects.filter(project__client=self.request.user,
                project=request.query_params['project_id'],client_watch="false")
    schedule=Task.objects.filter(project__client=self.request.user,
                project=request.query_params['project_id'],client_watch_schedule="false",
                worker_action="accepted")
    daily_work_report=DailyLog.objects.filter(project__client=self.request.user,
                project=request.query_params['project_id'],client_watch="false")
    safe_work_method_statement=len(Safety.objects.filter(
                project__client=self.request.user,project=request.query_params['project_id'],
                client_watch="false",type="safe_work_method_statement"))
    material_safety_data_sheets=len(Safety.objects.filter(
                project__client=self.request.user,project=request.query_params['project_id'],
                client_watch="false",type="material_safety_data_sheets"))
    work_health_and_safety_plan=len(Safety.objects.filter(
                project__client=self.request.user,project=request.query_params['project_id'],
                client_watch="false",type="work_health_and_safety_plan"))
    site_risk_assessment=len(SiteRiskAssessment.objects.filter(
                assigned_to=self.request.user,
                project=request.query_params['project_id'],assigned_to_watch="false"))
    incident_report=(len(IncidentReport.objects.filter(
                person_completing_form=self.request.user,
                project=request.query_params['project_id'],person_completing_form_watch="false"))+
                len(IncidentReport.objects.filter(
                witness_of_incident=self.request.user,
                project=request.query_params['project_id'],witness_of_incident_watch="false")))
    safety_total=safe_work_method_statement+material_safety_data_sheets+work_health_and_safety_plan+site_risk_assessment+incident_report


    payload={"all_count":{"plan":len(plan),
            "docs":{"docs_total":len(docs)+general_total+safety_total+variations,
                "specifications_and_product_information":len(Document.objects.filter(
                project__client=self.request.user,project=request.query_params['project_id'],
                client_watch="false",type="specifications_and_product_information")),
                "safety":{"safety_total":safety_total,
                    "safe_work_method_statement":safe_work_method_statement,
                    "material_safety_data_sheets":material_safety_data_sheets,
                    "work_health_and_safety_plan":work_health_and_safety_plan,
                    "site_risk_assessment":site_risk_assessment,
                    "incident_report":incident_report},
                "variations":variations,
                "general":{"general_total":general_total,
                    "toolbox":toolbox,
                    "roi":roi,
                    "eot":eot,
                    "punchlist":punchlist}},
            "people":len(people),
            "daily":{"daily_total":len(task)+len(schedule)+len(daily_work_report),
                "task":len(task),
                "schedule":len(schedule),
                "daily_work_report":len(daily_work_report)
            }}}
    payload.update(count)
    return payload