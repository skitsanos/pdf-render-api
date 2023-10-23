import base64
from json import JSONDecodeError
import io

from weasyprint import HTML

from flask import Response, make_response, request, g
from jsonschema.exceptions import ValidationError

schema = {
    "type": "object",
    "properties": {
        "raw": {
            "type": "boolean"
        },
        "url": {
            "type": "object",
        },
        "content": {
            "type": "object",
        },
    }
}


def handler():
    global html

    if request.content_length is None:
        return make_response({
            'error': {
                'message': 'Empty body'
            }
        }, 400)

    try:
        json_data = request.get_json()

        if 'url' not in json_data and 'content' not in json_data:
            g.app.logger.error('Incorrect JSON passed')

            return make_response({
                'error': {
                    'message': 'Expecting either url or content'
                }
            }, 400)

        if 'url' in json_data:
            g.app.logger.info(f'Processing URL {json_data["url"]}')
            html = HTML(url=json_data["url"])

        if 'content' in json_data:
            g.app.logger.info(f'Processing HTML content')
            html = HTML(string=json_data["content"])

        buffer = io.BytesIO()
        html.write_pdf(target=buffer)
        buffer.seek(0)
        pdf_data = buffer.getvalue()

        base64_encoded_pdf = base64.b64encode(pdf_data).decode('utf-8')

        if 'raw' not in json_data or json_data['raw'] == False:
            return make_response({
                "result": base64_encoded_pdf
            }, 200)

        response = Response(pdf_data, content_type='application/pdf')
        response.headers['Content-Disposition'] = 'inline; filename=untitled.pdf'
        return response

    except ValidationError as e:
        # JSON data is not valid based on the schema
        validation_error_message = e.message

        return make_response({
            'error': {
                'message': validation_error_message
            }
        }, 400)

    except JSONDecodeError:
        return make_response({
            'error': {
                'message': 'JSON Decoding error'
            }
        }, 400)
