from flask import Blueprint
from api import questions
from api.api_exceptions import ArethaAPIException

def create_blueprint():
    blueprint = Blueprint("example", __name__)

    # return examples to be used for educational components
    @blueprint.route('/api/example/<question>')
    def counterexample(question):
        try:
            example = questions.get_example(question)

            if example is False:
                raise ArethaAPIException(
                    "Unable to find a match for requested example", status=404)

            return {
                "text": example["text"],
                "impacts": example["impacts"],
                "geodata": example["geodata"],
                "devices": example["devices"]
            }
        except Exception as e:
            raise ArethaAPIException(
                "Internal error while fetching example", status=500, internal=e)

    return blueprint
