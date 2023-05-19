from accounts.models import User,Occupation
from api.models import Project,Address,Quotation
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings



jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER



class AdminPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class OccupationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Occupation
        fields = ('id', 'name')

    def __str__(self):
        return self.name
    
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('id', 'name', 'longitude', 'latitude')

    def __str__(self):
        return self.name
    

class QuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quotation
        fields = ('id', 'file')


class UserSerializer(serializers.ModelSerializer):
    print("here in serializer")
    occupation = OccupationSerializer()
    jwt_token = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['email', 'password','first_name','last_name','user_type','occupation','jwt_token']
        extra_kwargs = {'password': {'write_only': True}}

    def get_jwt_token(self, obj):
        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        return token.encode('utf-8')



class UserListSerializer(serializers.ModelSerializer):
    occupation = OccupationSerializer()
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name','user_type' , 'occupation', 'profile_picture')


class ProjectSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    client = UserSerializer()
    builder = UserSerializer()
    quotations = QuotationSerializer(many=True)

    class Meta:
        model = Project
        fields = (
            'id',
            'name',
            'address',
            'client',
            'description',
            'scope_of_work',
            'created_date',
            'last_updated',
            'worker',
            'status',
            'quotations',
            'builder',
        
            
        )
        
        
class AdminUpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email']
        
        
    def update(self, instance, validated_data):
        instance.username = validated_data.get('username',instance.username)
        instance.email = validated_data.get('email',instance.email)
        instance.save()
        return instance


class AdminChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length = 255,style = {'input_type':'password','write_only':True})
    new_password = serializers.CharField(max_length = 255,style = {'input_type':'password','write_only':True})
    confirm_password = serializers.CharField(max_length = 255,style = {'input_type':'password','write_only':True})
    
    def update(self, instance, validated_data):
        instance.set_password(validated_data.get('new_password'))
        instance.save()
        return instance
    # class Meta:
    #     fields = ['old_password','new_password','confirm_password']
    # # def validate(self,data):
    # #     new_password = data.get('new_password')
    # #     confirm_password = data.get('confirm_password')
    # #     old_password = data.get('old_password')
    # #     user = self.context.get('user')
        
    # #     if new_password != confirm_password:
    # #         raise serializers.ValidationError({'message':'Password do not match'})
    # #     elif len(new_password) < 8:
    # #         raise serializers.ValidationError({'message':'Password should be at least 8 characters'})
    # #     elif old_password == new_password :
    # #         raise serializers.ValidationError({'message':'old password and new password should not be same'})
    # #     else:
    # #         user.set_password(new_password)
    # #         user.save()
    # #         return data
    # #validate old password
    # # def validate_old_password(self, value):
    # #     user = self.context.get('user')
    # #     if not user.check_password(value):
    # #         raise PlainValidationError('old password is not correct')
    # #     return value



# from accounts.models import User
# from rest_framework import serializers
# from rest_framework_jwt.settings import api_settings

# jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
# jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

# class UserSerializer(serializers.ModelSerializer):
#     print("here in serializer")
#     jwt_token = serializers.SerializerMethodField()
#     class Meta:
#         model = User
#         fields = ['email', 'password','first_name','last_name','user_type','jwt_token']
#         extra_kwargs = {'password': {'write_only': True}}

#     def get_jwt_token(self, obj):
#         payload = jwt_payload_handler(obj)
#         print(payload,"payload")
#         token = jwt_encode_handler(payload)
#         print(type(token))
#         return token