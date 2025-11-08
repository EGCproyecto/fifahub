from wtforms import BooleanField, Form, IntegerField, StringField


class TabularDatasetForm(Form):
    name = StringField("Nombre")
    delimiter = StringField("Delimitador", default=",")
    encoding = StringField("Encoding", default="utf-8")
    has_header = BooleanField("Tiene cabecera", default=True)
    sample_rows = IntegerField("Filas de muestra", default=5)


# Lo de arriba son campos minimos, habria que ampliarlos
