from http.client import NO_CONTENT
from sre_constants import SUCCESS
from wsgiref import headers
from decouple import config
from rest_framework.response import Response
from django.template.loader import render_to_string
import requests
import json
import threading
def salesforce(switch,payload_data,request=None,*args,**kwargs):
    URL = "https://7zbnxmqrp4.execute-api.ap-southeast-2.amazonaws.com/"
    if switch=="SIGNUP" or switch=="UPDATEPROFILE":
      payload= {"EventType": "",
                "EventAction": "",
                "AppCustomerId": "",
                "ClientId": "",
                "WorkerId": "",
                "BuilderId": "",
                "FirstName": "",
                "LastName": "",
                "Email": "",
                "Phone": "",
                "SignUpDate": "",
                "Company":"",
                "Occupation":""
                }
      payload.update(payload_data)
      print(payload)
      res = requests.post(url = URL,json=json.dumps(payload_data))
      print(res.status_code)
      return Response(res.status_code)
    elif switch=="SUBSCRIBED":
                payload= {"EventType": "",
                  "EventAction": "",
                  "AppOrderId": "",
                  "AppId" : "",
                  "OrderDate": "",
                  "OrderAmount": "",    
                  "OrderStatus": ""
                  }
                payload.update(payload_data)
                print(payload)
                res = requests.post(url = URL,json=payload_data)
                print(res.status_code)
                return Response(res.status_code)
    elif switch=="RENEWED":
                payload= {"EventType": "",
                        "EventAction": "",
                        "AppOrderId": "",
                        "AppId" : "",
                        "OrderDate": "",
                        "OrderAmount": "",
                        "OrderStatus": ""
                }
                payload.update(payload_data)
                print(payload)
                res = requests.post(url = URL,json=payload_data)
                print(res.status_code)
                return Response(res.status_code)
    elif switch=="CANCELLED":
                payload= {"EventType": "",
                        "EventAction": "",
                        "AppOrderId": "",
                        "AppId" : "",
                        "OrderDate": "",
                        "OrderAmount": "",
                        "OrderStatus": ""
                }
                payload.update(payload_data)
                print(payload)
                res = requests.post(url = URL,json=payload_data)
                print(res.status_code)
                return Response(res.status_code)
    else:
          return NO_CONTENT
          

def salesforce_hit(switch,data_object,request=None):
  x = threading.Thread(target=salesforce,args=(switch,data_object,request))
  x.start()