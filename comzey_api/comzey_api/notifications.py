import email
from django.http import request
from pyfcm import FCMNotification
from decouple import config
from django.template.loader import render_to_string
from django.core.mail.message import EmailMultiAlternatives
from mailjet_rest import Client
import logging
import threading
import time
from projectnotifications.models import FcmNotifications

push_service = FCMNotification(api_key="AAAAFaUbRcc:APA91bHDhfg81ln9fUvl6-1TADvb3dz5Mz18kyG5BKIiMq6Zjl5mkqO93vswCGNbaA_RoehK8XmZzjj3edmTd5zYmmc9lfX5FoO27DZmbbC8hL3uL21C0_JXizwuoOtDlVw9b9k-mikC")

def subscribe(username,id):
  return push_service.subscribe_registration_ids_to_topic([username], topic_name="buildezi_%d"%id)
  
def send_notification(user,title,message,data_object,badge,request=None,*args,**kwargs):

  # email_context = {'first_name':user.first_name,
  #                   'last_name':user.last_name,
  #                   'message': message,
  #                   'base_url':f"{request.scheme}://{request.META['HTTP_HOST']}" if request else ''}
  # body = render_to_string(template_name='notification_email.html',context=email_context)

  # email_message = EmailMultiAlternatives(subject="Buildezi Notification", body=body,from_email=config('EMAIL_HOST_USER'),to= [user.email])
  # email_message.attach_alternative(body,'text/html')
  # email_message.send()
  # # user.email_user(subject="Buildezi Notification",message=email_message, from_email=config('EMAIL_HOST_USER'))
  # return push_service.notify_topic_subscribers(data_message=data_object,topic_name="buildezi_%d"%user.id, message_body=message,message_title=title,click_action =".NotificationHandler")
    data_object=payload(data_object)
    # api_key = config('MJ_APIKEY_PUBLIC')
    # api_secret = config('MJ_APIKEY_PRIVATE')
    # mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    # data = {
    #   'Messages': [
    #     {
    #       "From": {
    #         "Email": "darren_bedford14@outlook.com",
    #         "Name": "BUILD EZI"
    #       },
    #       "To": [
    #         {
    #           "Email": user.email,
    #           "Name": user.first_name
    #         }
    #       ],
    #       "TemplateID": 3726057,
    #       "TemplateLanguage": True,
    #       "Subject": "Notification From BUILD EZI",
    #       "Variables": {
    #     "firstname": user.first_name,
    #     "lastname": user.last_name,
    #     "message": message
    #   }
    #     }
    #   ]
    # }
    # result = mailjet.send.create(data=data)
    # print (result.status_code)
    # print (result.json())
    # print(badge)
    return push_service.notify_topic_subscribers(data_message=data_object,topic_name="buildezi_%d"%user.id, message_body=message,message_title=title,badge=badge,click_action =".NotificationHandler")

def payload(data_object):
  payload= {

          "title": -1,

          "message": -1,

          "notification_type":-1,

          "project_id":-1,

          'receiver_id':-1,

          "task_id":-1,

          "dailylog_id":-1,

          "plan_id":-1,

          "product_information_id":-1,
          
          "variation_id":-1,

          "roi_id":-1,

          "eot_id":-1,

          "punchlist_id":-1,
          
          "safety_id":-1,

          "incident_report":-1,

          "site_risk":-1,

          "toolbox_id":-1,

          "sender_id":-1,

          "fromNotification":True,

          
        }
  payload.update(data_object)
  return payload

def send_notification_thread(user,title,message,data_object,badge,request=None):
  x = threading.Thread(target=send_notification,args=(user,title,message,data_object,badge,request))
  x.start()