from wtforms import Form, StringField


class UVLDatasetForm(Form):
    name = StringField("Nombre")
