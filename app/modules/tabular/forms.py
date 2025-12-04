import csv

from flask_wtf import FlaskForm
from wtforms import BooleanField, FileField, IntegerField, SelectField, StringField
from wtforms.validators import DataRequired, NumberRange, Optional, Regexp, ValidationError

FIFA_REQUIRED_COLUMNS = [
    "ID",
    "Name",
    "Age",
    "Nationality",
    "Overall",
    "Potential",
    "Club",
    "Value",
    "Wage",
    "Preferred Foot",
    "Weak Foot",
    "Skill Moves",
    "Position",
    "Height",
    "Weight",
]


def validate_fifa_schema(form, field):
    file_storage = getattr(field, "data", None)
    if not file_storage:
        return

    stream = getattr(file_storage, "stream", None)
    if stream is None:
        raise ValidationError("ValidationError: No se pudo leer el archivo CSV.")

    delimiter_value = getattr(getattr(form, "delimiter", None), "data", ",") or ","
    delimiter_value = "\t" if delimiter_value == "\\t" else delimiter_value
    encoding_value = getattr(getattr(form, "encoding", None), "data", None) or "utf-8"

    try:
        stream.seek(0)
        raw_line = stream.readline()
        if not raw_line:
            raise ValidationError("ValidationError: El archivo CSV está vacío.")

        try:
            header_line = raw_line.decode(encoding_value)
        except UnicodeDecodeError as exc:
            raise ValidationError(
                "ValidationError: No se pudo decodificar el CSV con el encoding seleccionado."
            ) from exc

        reader = csv.reader([header_line], delimiter=delimiter_value)
        try:
            header = next(reader)
        except Exception:
            header = []

        if header and header[0].startswith("\ufeff"):
            header[0] = header[0].lstrip("\ufeff")

        header = [col.strip() for col in header]

        missing = [col for col in FIFA_REQUIRED_COLUMNS if col not in header]
        if missing:
            detail = f"Faltan: {', '.join(missing)}."
            raise ValidationError(f"ValidationError: Solo se aceptan datasets oficiales de FIFA. {detail}")
    finally:
        stream.seek(0)


class TabularDatasetForm(FlaskForm):
    """Formulario para subir datasets tabulares CSV"""

    name = StringField("Nombre", validators=[DataRequired(message="Indica un nombre.")])

    csv_file = FileField(
        "CSV",
        validators=[
            DataRequired(message="Sube un archivo .csv"),
            validate_fifa_schema,
        ],
    )

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

    author_id = SelectField("Autor", coerce=int, validators=[Optional()], choices=[])

    community_id = StringField("Comunidad", validators=[Optional()])

    def validate_delimiter(self, field):
        if field.data == "\\t":
            raise ValidationError("Pega un TAB real, no la secuencia \\t.")
