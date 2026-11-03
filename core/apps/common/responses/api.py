from rest_framework.response import Response


def api_response(success, message, data=None, errors=None, status=200):
    return Response(
        {
            "success": success,
            "message": message,
            "data": data,
            "errors": errors,
        },
        status=status,
    )
