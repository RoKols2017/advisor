from flasgger.utils import swag_from

@importer.route("/import/users", methods=["POST"])
@swag_from({
    'tags': ['Import'],
    'consumes': ['multipart/form-data'],
    'parameters': [
        {
            'name': 'file',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': 'CSV-файл с пользователями'
        }
    ],
    'responses': {
        200: {
            'description': 'Импорт завершён',
            'examples': {
                'application/json': {
                    "created": 10,
                    "errors": []
                }
            }
        }
    }
})
def import_users():
    ...
