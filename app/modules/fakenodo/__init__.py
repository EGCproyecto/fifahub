from core.blueprints.base_blueprint import BaseBlueprint
from .routes import bp

fakenodo_bp = BaseBlueprint("fakenodo", __name__, template_folder="templates")
