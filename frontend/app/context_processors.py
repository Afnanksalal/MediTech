def auth_status(request):
    return {'is_authenticated': request.user.is_authenticated}
