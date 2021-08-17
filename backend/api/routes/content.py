from flask import Blueprint
from datetime import datetime


def create_blueprint(Content):
    blueprint = Blueprint("content", __name__)
    
    # return a list of live but not completed content
    @blueprint.route('/')
    def get_content():
        current_timestamp = datetime.now()
        content = list(
            Content.select()
            .where(
                (Content.live < current_timestamp) &
                (Content.complete == False))
            .dicts()
            .execute())

        return {"content": content}

    # mark content as set, and record the pre and post responses
    # TODO this should be a POST request as well
    @blueprint.route('/set/<name>/<pre>/<post>', methods=["POST"])
    def set_content(name, pre, post):
        (Content
         .update(complete=True, pre=pre[:200], post=post[:200])
         .where(Content.name == name)
         .execute())

        return {"message": "Request processed", "success": "unknown"}

    return blueprint
