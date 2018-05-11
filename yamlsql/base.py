import decimal
import json
import traceback

from flask import request, make_response

from funcy import decorator

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

@decorator
def api_request(func):
    try:
        params = request.args.to_dict() or {}
        if request.method == 'POST':
            params.update(request.json or {})
        resp_data = json.dumps({
            'status': 'ok',
            'data': func(**params)
            }, cls=DecimalEncoder)
    except Exception, e:
        traceback.print_exc()
        resp_data = json.dumps({
            'status': 'error',
            'err_msg': e.message
            }, cls=DecimalEncoder)
    response = make_response(resp_data)
    response.headers['Content-Type'] = 'application/json'
    return response


def emacs_converter(processor):
    @decorator
    def converter(func):
        if request.headers.get('User-Agent') == 'emacs':
            return processor(func())
        return func()
    return converter
