from email.policy import HTTP
from django.contrib.sessions.models import Session
from datetime import datetime
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.views import APIView
from users.api.serializers import UserTokenSerializer
from users.api.authentication_mixins import Authentication


class UserToken(Authentication, APIView):
    def get(self, request, *args, **kwargs):
        #username = request.GET.get('username')
        try:
            user_token =  Token.objects.get_or_create(user = self.user)
            user = UserTokenSerializer(self.user)
            return Response({
                'token': user_token.key,
                'user': user.data
            })
        except:
            return Response({
                'error': 'Credenciales enviadas incorrectas'
            }, status = status.HTTP_400_BAD_REQUEST)

class Login(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        login_serializer = self.serializer_class(data = request.data, context = {'request': request})
        if login_serializer.is_valid():
            user = login_serializer.validated_data['user']
            if user.is_active:
                token, created =  Token.objects.get_or_create(user = user)
                user_serializer =  UserTokenSerializer(user)
                if created: 
                    return Response({'token': token.key, 'user': user_serializer.data, 'message' : 'login correcto'}, status =  status.HTTP_201_CREATED)
                else:
                    all_sessions =  Session.objects.filter(expire_date__gte = datetime.now())
                    if all_sessions.exists():
                        for session in all_sessions:
                            session_data = session.get_decoded()
                            if user.id == int(session_data.get('_auth_user_id')):
                                session.delete()
                    token.delete()
                    token = Token.objects.create(user = user)
                    return Response({'token': token.key, 'user': user_serializer.data, 'message' : 'login correcto'}, status =  status.HTTP_201_CREATED)
            else:
                return Response({'error':'Usuario no activo'}, status = status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'error':'Credenciales invalidad'}, status = status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Hi'}, status = status.HTTP_200_OK)


class Logout(APIView):
    
    def get(self,request,*args,**kwargs):
        try:

            token = request.GET.get('token') # el front tiene que mandarlo en esa variable, sino no funcionara. el el header
            token = Token.objects.filter(key = token).first()
            if token:
                user = token.user
                all_sessions =  Session.objects.filter(expire_date__gte = datetime.now())
                if all_sessions.exists():
                    for session in all_sessions:
                        session_data = session.get_decoded()
                        if user.id == int(session_data.get('_auth_user_id')):
                            session.delete()
                token.delete()
                token_message = 'Token eliminado'
                session_message = 'Sesiones eliminadas'
                return Response({'toke_message': token_message, 'session_message': session_message}, status = status.HTTP_200_OK)
            return Response({'error':'Sessiones no activas'}, status = status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error':'Token no encontrado'}, status = status.HTTP_409_CONFLICT)