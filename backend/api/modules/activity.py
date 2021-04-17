from flask import Blueprint

def create_blueprint(Activity):
    blueprint = Blueprint("activity", __name__)
    
    @blueprint.route('/<pid>/<category>/<action>')
    def activity(pid, category, action):
        Activity.insert(
            Activity.pid=pid,
            Activity.category=category,
            Activity.action=action
        ).execute()

        return {"message": "activity logged"}

        
    return blueprint
