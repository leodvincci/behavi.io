from django.core import serializers
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.forms.models import model_to_dict
from rest_framework.permissions import AllowAny
from django.middleware.csrf import get_token
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from .models import *
import random as randGen

User = get_user_model()

user_session = None  # global variable to store session


# Create your views here.
@api_view(["POST"])
def registration(request):
    first_name = request.data["first_name"]
    last_name = request.data["last_name"]
    email = request.data["email"]
    password = request.data["password"]
    app_user = User.objects.create_user(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        username=email,
    )
    app_user.save()
    print(app_user)
    return JsonResponse({"success": True})


@api_view(["POST"])
@permission_classes([AllowAny])
def set_session_user(request):
    session_id = request.data["session"]
    user = authUser(session_id)

    #

    print("User stored:", user)
    return JsonResponse({"success": True, "user": model_to_dict(user)})


def authUser(session_id):
    session = Session.objects.get(session_key=session_id)
    uid = session.get_decoded().get("_auth_user_id")
    user = User.objects.get(pk=uid)
    return user


@api_view(["POST"])
@permission_classes([AllowAny])
def user_login(request):
    username = request.data["username"]
    password = request.data["password"]
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)

        return JsonResponse(
            {
                "success": True,
                "user": model_to_dict(user),
                "tokens": {
                    "csrf-token": get_token(request),
                    "session": request.session.session_key,
                },
            }
        )
    else:
        return JsonResponse({"success": False})


@api_view(["POST"])
def user_logout(request):
    logout(request)
    return JsonResponse({"success": True})


@api_view(["GET"])
def question(request, question_id=None, category_txt=None):
    if question_id:
        try:
            questions = list(Question.objects.filter(id=question_id).values())
            return JsonResponse({"questions": questions})
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"success": False})

    elif category_txt:
        try:
            the_cat = list(Category.objects.filter(category_txt=category_txt).values())
            questions = list(
                Question.objects.filter(category=the_cat[0]["id"]).values()
            )

            return JsonResponse({"questions": questions})
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"success": False})
    else:
        try:
            questions = list(Question.objects.all().values())
            return JsonResponse({"questions": questions})
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"success": False})


@api_view(["GET"])
def category(request):
    categories = list(Category.objects.all().values())
    print(categories)
    return JsonResponse({"categories": categories})


@api_view(["GET"])
# Returns token and session id
def tokens(request):
    return JsonResponse(
        {
            "csrf-token": get_token(request),
            "session": request.session.session_key,
        }
    )


@api_view(["POST", "PUT", "GET", "DELETE"])
def response_handling(request, question_id, response_id=None):
    if request.method == "POST":
        try:
            response_S = request.data["response_S"]
            response_T = request.data["response_T"]
            response_A = request.data["response_A"]
            response_R = request.data["response_R"]
            vid_link = request.data["vid_link"]
            isPrivate = request.data["isPrivate"]

            new_response = Response.objects.create(
                app_user=User.objects.get(email=user),
                question=Question.objects.get(pk=question_id),
                response_S=response_S,
                response_T=response_T,
                response_A=response_A,
                response_R=response_R,
                vid_link=vid_link,
                isPrivate=isPrivate,
                feedbackCounter=0,
            )

            print(new_response)
            new_response.save()
            return JsonResponse({"success": True})

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"success": False})

    """Takes data from request, iterates through each key/value and updates response by id, saves response"""
    if request.method == "PUT":
        try:
            if response_id:
                response = get_object_or_404(Response, id=response_id, app_user=user)
                data = request.data
                for key, value in data.items():
                    setattr(response, key, value)
                response.save()
                return JsonResponse({"success": True})
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"success": False})

    if request.method == "GET":
        # GET single response
        if response_id:
            response = get_object_or_404(Response, id=response_id, app_user=user)
            response_dict = model_to_dict(response)
            return JsonResponse({"response": response_dict})
        # GET all of a user's responses
        else:
            try:
                responses = list(Response.objects.filter(app_user=user).values())
                return JsonResponse({"responses": responses})
            except Exception as e:
                print(f"Error: {e}")
                return JsonResponse({"responses": []})

    if request.method == "DELETE":
        try:
            response = get_object_or_404(Response, id=response_id, app_user=user)
            response.delete()
            return JsonResponse({"success": True})
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"success": False})


@api_view(["POST", "GET", "DELETE"])
def feedback_handling(request, response_id, feedback_id=None):
    if request.method == "POST":
        try:
            feedback_text = request.data["feedback_text"]
            response = get_object_or_404(Response, id=response_id)

            new_feedback = Feedback.objects.create(
                response=Response.objects.get(pk=response_id),
                feedback_text=feedback_text,
            )

            new_feedback.save()
            response.feedbackCounter += 1
            response.save()

            return JsonResponse({"success": True})

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"success": False})

    if request.method == "GET":
        try:
            feedbacks = Feedback.objects.filter(response=response_id)
            feedback_list = []

            for feedback in feedbacks:
                feedback_list.append(feedback.feedback_text)

            return JsonResponse({"feedback": feedback_list})

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"success": False})

    if request.method == "DELETE":
        try:
            feedback = get_object_or_404(Feedback, id=feedback_id)
            response = get_object_or_404(Response, id=feedback.response)

            feedback.delete()

            response.feedbackCounter -= 1
            response.save()
            return JsonResponse({"success": True})

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"success": False})


@api_view(["POST", "GET", "DELETE"])
def favorite_handling(request, question_id, favorite_id=None):
    user = authUser(request)

    # Adds question to "FavoritedQuestion" table for easy access to all favorites, also sets the 'isFavorite' field on the Questions model to True for easy access that way
    if request.method == "POST":
        try:
            question = get_object_or_404(Question, id=question_id)

            # Fix from response_handling applied here as well
            auth = request.data["auth"]
            session = Session.objects.get(session_key=auth)
            uid = session.get_decoded().get("_auth_user_id")
            user = User.objects.get(pk=uid)

            new_favorite = FavoritedQuestion.objects.create(
                app_user=User.objects.get(email=user),
                question=Question.objects.get(pk=question_id),
            )

            new_favorite.save()

            question.isFavorite = True
            question.save()

            return JsonResponse({"success": True})

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"success": False})

    # GET's all favorites
    if request.method == "GET":
        try:
            favorites = list(FavoritedQuestion.objects.filter(app_user=user).values())

            return JsonResponse({"favorites": favorites})
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"success": False})

    # DELETE's favorite from table, resets question 'isFavorite' value to False
    if request.method == "DELETE":
        try:
            favorite = get_object_or_404(
                FavoritedQuestion, id=favorite_id, app_user=user
            )
            question = get_object_or_404(Question, id=favorite.question)
            favorite.delete()
            question.isFavorite = False
            question.save()

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"success": False})


@api_view(["GET"])
def random(request):
    questions_count = len(list(Question.objects.all()))
    random_number = randGen.randint(1, questions_count)
    rand_question = Question.objects.filter(pk=random_number)
    return JsonResponse({"question": model_to_dict(rand_question.get())})
