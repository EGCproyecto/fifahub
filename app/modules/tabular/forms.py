from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, StringField, FileField
from wtforms.validators import DataRequired, Optional, NumberRange, Regexp, ValidationError


class TabularDatasetForm(FlaskForm):
    """Formulario para subir datasets tabulares CSV"""

    name = StringField("Nombre", validators=[DataRequired(message="Indica un nombre.")])

    csv_file = FileField("CSV", validators=[DataRequired(message="Sube un archivo .csv")])

    delimiter = StringField(
        "Delimitador",
        default=",",
        validators=[
            DataRequired(message="Indica el delimitador."),
            Regexp(r"^.{1}$", message="El delimitador debe ser un único carácter."),
        ],
    )

    encoding = StringField("Encoding", default="utf-8")

    has_header = BooleanField("Tiene cabecera", default=True)

    sample_rows = IntegerField(
        "Filas de muestra",
        default=20,
        validators=[Optional(), NumberRange(min=0, max=200, message="0–200 filas.")],
    )

    def validate_delimiter(self, field):
        if field.data == "\\t":
            raise ValidationError("Pega un TAB real, no la secuencia \\t.")
