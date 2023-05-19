import base64
import json
from re import T
import requests
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from accounts.models import User
import datetime
from rest_framework import mixins, viewsets
from accountspayments.models import Payment,Subscription,Subscriber
from accountspayments.serializers import CreatePaymentSerializer,CreatePlansSerializer,CreateProductSerializer,CreateSubscriptionSerializer,GetSubscriptionIdSerializer,CycleExecutionsSerializer, SubscriberSerializer, SubscriberSerializer, OutstandingBalanceSerializer, BillingInfoSerializer
from comzey_api.salesforce import salesforce
from decouple import config
# includes ----------->>>>>>>>>ProductViewset, PlansViewset, SubscriptionViewset, PaymentViewset
class ProductViewset(viewsets.GenericViewSet, mixins.CreateModelMixin,mixins.RetrieveModelMixin,mixins.ListModelMixin):
    permission_classes=[AllowAny]
    queryset = User.objects.none()
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateProductSerializer
    def create(self, request, *args, **kwargs):
        user=request.user,
        client_id = config('CLIENT_ID')
        client_secret = config('CLIENT_SECRET')
        url = "https://api.sandbox.paypal.com/v1/oauth2/token"
        data = {
                    "client_id":client_id,
                    "client_secret":client_secret,
                    "grant_type":"client_credentials"
                }
        headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": "Basic {0}".format(base64.b64encode((client_id + ":" + client_secret).encode()).decode())
                }

        token = requests.post(url, data, headers=headers)
        access_token=token.json()
        url = "https://api-m.sandbox.paypal.com/v1/catalogs/products"
        data = request.data
        headers = {'Content-type': 'application/json'}
        r = requests.post(url, data=json.dumps(data), headers=headers, auth=(client_id, client_secret))
        result=r.json()
        data1={'name':result.get('id')}
        serializer = self.get_serializer(data=data1)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(r.json())

    def list(self, request, *args, **kwargs):
        client_id = config('CLIENT_ID')
        client_secret = config('CLIENT_SECRET')
        url = "https://api.sandbox.paypal.com/v1/oauth2/token"
        data = {
                    "client_id":client_id,
                    "client_secret":client_secret,
                    "grant_type":"client_credentials"
                }
        headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": "Basic {0}".format(base64.b64encode((client_id + ":" + client_secret).encode()).decode())
                }

        token = requests.post(url, data, headers=headers)
        access_token=token.json()
        url = "https://api-m.sandbox.paypal.com/v1/catalogs/products/"
        data = request.data
        headers = {'Content-type': 'application/json'}
        r = requests.get(url, headers=headers, auth=(client_id, client_secret))
        return Response(r.json())

class PlansViewset(viewsets.GenericViewSet, mixins.CreateModelMixin):
    permission_classes=[AllowAny]
    queryset = User.objects.none()
    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePlansSerializer
    def create(self, request, *args, **kwargs):
        user=request.user
        client_id = config('CLIENT_ID')
        client_secret = config('CLIENT_SECRET')

        url = "https://api.sandbox.paypal.com/v1/oauth2/token"
        data = {
                    "client_id":client_id,
                    "client_secret":client_secret,
                    "grant_type":"client_credentials"
                }
        headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": "Basic {0}".format(base64.b64encode((client_id + ":" + client_secret).encode()).decode())
                }

        token = requests.post(url, data, headers=headers)
        access_token=token.json()
        url = "https://api-m.sandbox.paypal.com/v1/billing/plans"
        data = request.data
        headers = {'Content-type': 'application/json'}
        r = requests.post(url, data=json.dumps(data), headers=headers, auth=(client_id, client_secret))
        result=r.json()
        data1={'name':result.get('id'),'product':result.get('product_id')}
        serializer = self.get_serializer(data=data1)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(r.json())

class SubscriptionViewset(viewsets.GenericViewSet, mixins.CreateModelMixin,mixins.RetrieveModelMixin):
    permission_classes=[AllowAny]
    queryset = User.objects.none()
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateSubscriptionSerializer
    def create(self, request, *args, **kwargs):
        try:
            user=request.user
            if user.user_type=="builder":
                client_id = config('CLIENT_ID')
                client_secret = config('CLIENT_SECRET')
                url = "https://api.sandbox.paypal.com/v1/oauth2/token"
                data = {
                            "client_id":client_id,
                            "client_secret":client_secret,
                            "grant_type":"client_credentials"
                        }
                headers = {
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Authorization": "Basic {0}".format(base64.b64encode((client_id + ":" + client_secret).encode()).decode())
                        }

                token = requests.post(url, data, headers=headers)
                access_token=token.json()
                url = "https://api-m.sandbox.paypal.com/v1/billing/subscriptions"
                data = request.data
                headers = {'Content-type': 'application/json'}
                print(headers)
                r = requests.post(url, data=json.dumps(data), headers=headers, auth=(client_id, client_secret))
                print(r)
                print(client_id)
                print(client_secret)
                print(r.json())
                result=r.json()
                data1={'name':result.get('id'),'start_time':request.data.get('start_time'),'plan':request.data.get('plan_id'),'status':result.get('status')}
                serializer = self.get_serializer(data=data1)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                return Response(r.json())
            else:
                return Response(data='You donot have the permissiion to perform this Action.', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(e)

    def retrieve(self, request, *args, **kwargs):
        if request.query_params.get('subscription_id'):
            try:
                instance =Subscription.objects.get(
                    name=request.query_params['subscription_id'])
                
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a subscription ID.', status=status.HTTP_404_NOT_FOUND)

        client_id = config('CLIENT_ID')
        client_secret = config('CLIENT_SECRET')
        url = "https://api.sandbox.paypal.com/v1/oauth2/token"
        data = {
                    "client_id":client_id,
                    "client_secret":client_secret,
                    "grant_type":"client_credentials"
                }
        headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": "Basic {0}".format(base64.b64encode((client_id + ":" + client_secret).encode()).decode())
                }

        token = requests.post(url, data, headers=headers)
        access_token=token.json()
        url = "https://api-m.sandbox.paypal.com/v1/billing/subscriptions/"+request.query_params['subscription_id']+'/'
        data = request.data
        headers = {'Content-type': 'application/json'}
        r = requests.get(url, headers=headers, auth=(client_id, client_secret))
        return Response(r.json())
    


    @action(methods=['POST'],detail=False,url_path='cancel',url_name='cancel_subscription')
    def cancel_subscription(self, request, *args, **kwargs):
        if request.query_params.get('subscription_id'):
            try:
                instance =Subscription.objects.get(
                    name=request.query_params['subscription_id'])
                
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a subscription ID.', status=status.HTTP_404_NOT_FOUND)

        client_id = config('CLIENT_ID')
        client_secret = config('CLIENT_SECRET')
        url = "https://api.sandbox.paypal.com/v1/oauth2/token"
        data = {
                    "client_id":client_id,
                    "client_secret":client_secret,
                    "grant_type":"client_credentials"
                }
        headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": "Basic {0}".format(base64.b64encode((client_id + ":" + client_secret).encode()).decode())
                }

        token = requests.post(url, data, headers=headers)
        access_token=token.json()

        url = "https://api-m.sandbox.paypal.com/v1/billing/subscriptions/"+request.query_params['subscription_id']+'/'+'suspend'+'/'
        data = request.data
        headers = {'Content-type': 'application/json'}
        r = requests.post(url, data=json.dumps(data), headers=headers, auth=(client_id, client_secret))
        if r.status_code==204:
            subscription_update=Subscription.objects.get(name=request.query_params['subscription_id'])
            subscription_update.status='CANCELLED'
            subscription_update.save()
            payment_update=Payment.objects.get(subscription=request.query_params['subscription_id'])
            payment_update.status='CANCELLED'
            payment_update.save()
            user_subscribed=User.objects.get(id=request.user.id)
            user_subscribed.is_subscription='NO_ACTIVE_PLAN'
            user_subscribed.save()
        else:
            return Response(data='something went wrong',status=status.HTTP_400_BAD_REQUEST)
        switch="CANCELLED"
        try:
                payload_data={"EventType": "subscription",
                  "EventAction": "cancelled",
                  "AppOrderId": request.query_params['subscription_id'],
                  "AppId" : request.user.id,
                  "OrderDate":datetime.datetime.now().date().strftime("%m_%d_%Y"),
                  "OrderAmount": "$10",
                  "OrderStatus": "Success"
                  }
                salesforce(switch,payload_data,request)
        except Exception as e:
                print(e)
        return Response(data='subscription_cancelled',status=status.HTTP_200_OK)
        
    @action(methods=['POST'],detail=False,url_path='activate',url_name='reactivate_subscription')
    def reactivate_subscription(self, request, *args, **kwargs):
        if request.query_params.get('subscription_id'):
            try:
                instance =Subscription.objects.get(
                    name=request.query_params['subscription_id'])
                
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a subscription ID.', status=status.HTTP_404_NOT_FOUND)

        client_id = config('CLIENT_ID')
        client_secret = config('CLIENT_SECRET')
        url = "https://api.sandbox.paypal.com/v1/oauth2/token"
        data = {
                    "client_id":client_id,
                    "client_secret":client_secret,
                    "grant_type":"client_credentials"
                }
        headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": "Basic {0}".format(base64.b64encode((client_id + ":" + client_secret).encode()).decode())
                }

        token = requests.post(url, data, headers=headers)
        access_token=token.json()
        url = "https://api-m.sandbox.paypal.com/v1/billing/subscriptions/"+request.query_params['subscription_id']+'/'+'activate/'
        data = request.data
        headers = {'Content-type': 'application/json'}
        r = requests.post(url, data=json.dumps(data), headers=headers, auth=(client_id, client_secret))
        if r.status_code==204:
            subscription_update=Subscription.objects.get(name=request.query_params['subscription_id'])
            subscription_update.status='REACTIVATED'
            subscription_update.save()
            payment_update=Payment.objects.get(subscription=request.query_params['subscription_id'])
            payment_update.status='REACTIVATED'
            payment_update.save()
            user_subscribed=User.objects.get(id=request.user.id)
            user_subscribed.is_subscription='REGULAR'
            user_subscribed.save()
        else:
            return Response(data='something went wrong',status=status.HTTP_400_BAD_REQUEST)
        switch="RENEWED"
        try:
                payload_data={"EventType": "subscription",
                "EventAction": "renewed",
                "AppOrderId": request.query_params['subscription_id'],
                "AppId" : request.user.id,
                "OrderDate":datetime.datetime.now().date().strftime("%m_%d_%Y"),
                "OrderAmount": "$10",
                "OrderStatus": "Success"
                }
                salesforce(switch,payload_data,request)
        except Exception as e:
                print(e)
        return Response(data='subscription_activated',status=status.HTTP_200_OK)

class PaymentViewset(viewsets.GenericViewSet, mixins.CreateModelMixin,mixins.RetrieveModelMixin):
    permission_classes=[AllowAny]
    def get_queryset(self): 
        if self.action=="create" :
            return User.objects.none()
        else:
            return Payment.objects.filter(user=self.request.user)
    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePaymentSerializer
        if self.action=='list':
            return GetSubscriptionIdSerializer
    def create(self, request, *args, **kwargs):
        try:
            client_id = config('CLIENT_ID')
            client_secret = config('CLIENT_SECRET')
            url = "https://api.sandbox.paypal.com/v1/oauth2/token"
            data = {
                        "client_id":client_id,
                        "client_secret":client_secret,
                        "grant_type":"client_credentials"
                    }
            headers = {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Authorization": "Basic {0}".format(base64.b64encode((client_id + ":" + client_secret).encode()).decode())
                    }

            token = requests.post(url, data, headers=headers)
            access_token=token.json()
            url = "https://api-m.sandbox.paypal.com/v1/billing/subscriptions/"+request.query_params['subscription_id']+'/'
            headers = {'Content-type': 'application/json'}
            result = requests.get(url, headers=headers, auth=(client_id, client_secret))
            result=result.json()
            data={
            "status": result.get('status'),
            "status_update_time": result.get('status_update_time'),
            "id": result.get('id'),
            "plan_id": result.get('plan_id'),
            "start_time": result.get('start_time'),
            "subscriber": {
                "email_address": result.get('subscriber').get('email_address'),
                "payer_id": result.get('subscriber').get('payer_id')
            },
            "billing_info": {
                "outstanding_balance": {
                    "currency_code": result.get('billing_info').get('outstanding_balance').get('currency_code'),
                    "value": result.get('billing_info').get('outstanding_balance').get('value')
                },
                "cycle_executions":[
                    {
                        "tenure_type": result.get('billing_info').get('cycle_executions')[0].get('tenure_type'),
                        "sequence": result.get('billing_info').get('cycle_executions')[0].get('sequence'),
                        "cycles_completed": result.get('billing_info').get('cycle_executions')[0].get('cycles_completed'),
                        "cycles_remaining": result.get('billing_info').get('cycle_executions')[0].get('cycles_remaining'),
                        "current_pricing_scheme_version": result.get('billing_info').get('cycle_executions')[0].get('current_pricing_scheme_version'),
                        "total_cycles": result.get('billing_info').get('cycle_executions')[0].get('total_cycles')
                    }
                ],
                "next_billing_time": result.get('billing_info').get('next_billing_time'),
                "failed_payments_count":  result.get('billing_info').get('failed_payments_count')
            },
            "create_time": result.get('create_time'),
            "update_time": result.get('update_time'),
        }
            cycle_executions=data.get('billing_info').get('cycle_executions')[0]
            serializer_cycle_executions = CycleExecutionsSerializer(data=cycle_executions)
            serializer_cycle_executions.is_valid(raise_exception=True)
            self.perform_create(serializer_cycle_executions)

            if Subscriber.objects.filter(email_address=data.get('subscriber').get('email_address')).exists():
                    subscriber = Subscriber.objects.get(email_address=data.get('subscriber').get('email_address'))
                    serializer_subscriber = SubscriberSerializer(subscriber, data=data.get('subscriber'))
                    serializer_subscriber.is_valid(raise_exception=True)
                    serializer_subscriber.update(instance=subscriber,validated_data=data.get('subscriber'))
            else:
                subscriber=data.get('subscriber')
                subscriber.pop('name', None)
                serializer_subscriber= SubscriberSerializer(data=subscriber)
                serializer_subscriber.is_valid(raise_exception=True)
                self.perform_create(serializer_subscriber)


            outstanding_balance=data.get('billing_info').get('outstanding_balance')
            serializer_outstanding_balance = OutstandingBalanceSerializer(data=outstanding_balance)
            serializer_outstanding_balance.is_valid(raise_exception=True)
            self.perform_create(serializer_outstanding_balance)

            billing_info=data.get('billing_info')
            billing_info['cycle_executions']=serializer_cycle_executions.data.get('id')
            billing_info['outstanding_balance']=serializer_outstanding_balance.data.get('id')
            serializer_billing_info = BillingInfoSerializer(data=billing_info)
            serializer_billing_info.is_valid(raise_exception=True)
            self.perform_create(serializer_billing_info)

            data1=request.data
            data1['status']=result.get('status')
            data1['start_time']=result.get('start_time')
            data1['subscription']=result.get('id')
            data1['plan']=result.get('plan_id')
            data1['create_time']=result.get('create_time')
            data1['status_update_time']=result.get('status_update_time')
            data1['update_time']=result.get('update_time')
            data1['subscriber']=serializer_subscriber.data.get('id')
            data1['billing_info']=serializer_billing_info.data.get('id')
            data1['user']=request.user.id
            serializer = self.get_serializer(data=data1)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            subscription_update=Subscription.objects.get(name=result.get('id'))
            subscription_update.status=result.get('billing_info').get('cycle_executions')[0].get('tenure_type')
            subscription_update.save()
            subscription_update.start_time=result.get('start_time')
            subscription_update.save()
            user_subscribed=User.objects.get(id=request.user.id)
            if user_subscribed.is_subscription=='TRIAL':
                switch="SUBSCRIBED"
                try:
                        payload_data={"EventType": "subscription",
                        "EventAction": "new",
                        "AppOrderId": result.get('id'),
                        "AppId" : request.user.id,
                        "OrderDate":datetime.datetime.now().date().strftime("%m_%d_%Y"),
                        "OrderAmount": "$10",
                        "OrderStatus": "Success"
                        }
                        salesforce(switch,payload_data,request)
                except Exception as e:
                        print(e)
           
            else:
                switch="RENEWED"
                try:
                        payload_data={"EventType": "subscription",
                        "EventAction": "renewed",
                        "AppOrderId": result.get('id'),
                        "AppId" : request.user.id,
                        "OrderDate":datetime.datetime.now().date().strftime("%m_%d_%Y"),
                        "OrderAmount": "$10",
                        "OrderStatus": "Success"
                        }
                        salesforce(switch,payload_data,request)
                except Exception as e:
                        print(e)
            user_subscribed.is_subscription=result.get('billing_info').get('cycle_executions')[0].get('tenure_type')
            user_subscribed.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            return Response(e)
    def list(self, request, *args, **kwargs):
        if self .request.user:
            # if self.filter_queryset(self.get_queryset()):
            #     queryset =Payment.objects.filter(user=request.user.id,status='ACTIVE')
            # if self.filter_queryset(self.get_queryset()):
            #     queryset =Payment.objects.filter(user=request.user.id).order_by('-id')
            #     serializer = self.get_serializer(queryset, many=True)
            #     return Response(serializer.data[0])
            if self.filter_queryset(self.get_queryset()):
                queryset =Payment.objects.filter(user=request.user.id).order_by('-id')
            else:
                return Response(data='Currently No Active Subscriptions.', status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data='Please Specify user_id', status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)