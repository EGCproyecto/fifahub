from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class UVLDatasetForm(FlaskForm):
    name = StringField("Nombre", validators=[DataRequired(message="Please provide a dataset name.")])
