from django import urls
from django.urls import path
from django.urls.conf import include
from rest_framework.routers import DefaultRouter
from projectdocuments.api import   DocumentViewset, IncidentReportViewset, IncidentTypeViewset, PunchListViewset, SiteRiskAssessmentQuestionsViewset, ROIViewset,EOTViewset, SafetyViewset, SiteRiskAssessmentViewset, ToolBoxViewset, VariationsViewset,SiteRiskAssessmentRelationViewset

router = DefaultRouter()
router.register('document',DocumentViewset,basename='document')
router.register('safety',SafetyViewset,basename='safety')
router.register('incidenttype',IncidentTypeViewset,'incident_type')
router.register('incidentreport',IncidentReportViewset,basename='incidentreport')
router.register('variation',VariationsViewset,basename='variation')
router.register('roi',ROIViewset ,basename='roi')
router.register('eot',EOTViewset ,basename='eot')
router.register('toolbox',ToolBoxViewset ,basename='toolbox')
router.register('punchlist',PunchListViewset ,basename='punchlist')
router.register('siteriskassessment',SiteRiskAssessmentViewset ,basename='siteriskassessment')
router.register('siteriskassessmentquestion',SiteRiskAssessmentQuestionsViewset ,basename='siteriskassessmentquestion')
router.register('siteriskassessmentrelation',SiteRiskAssessmentRelationViewset ,basename='siteriskassessmentrelation')

urlpatterns = [
    path('', include(router.urls)),
]
