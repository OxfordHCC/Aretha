from flask import Blueprint


def create_blueprint(Content):
    blueprint = Blueprint("content", __name__)
    
    # return a list of live but not completed content
    @blueprint.route('/')
    def content():
        content = DB_MANAGER.execute("select * from content where live < current_timestamp and complete = false", ())
        return content

    # mark content as set, and record the pre and post responses
    # TODO this should be a POST request as well
    @blueprint.route('/set/<name>/<pre>/<post>')
    def contentSet(name, pre, post):
        DB_MANAGER.execute("update content set complete = true, pre = %s, post = %s where name = %s", (pre[:200], post[:200], name))
        return {"message": "Request processed", "success": "unknown"}

    return blueprint
