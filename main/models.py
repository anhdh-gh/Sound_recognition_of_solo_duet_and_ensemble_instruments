from django.db import models


class Attribute(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True)
    file = models.ForeignKey('File', models.CASCADE, db_column='FileId', related_name="attributes")
    name = models.CharField(db_column='Name', max_length=255)

    class Meta:
        managed = False
        db_table = 'attribute'


class AttributeValue(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True)
    attribute = models.ForeignKey(Attribute, models.CASCADE, db_column='AttributeId', related_name="attribute_values")
    value = models.FloatField(db_column='Value')

    class Meta:
        managed = False
        db_table = 'attributevalue'


class Chart(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True)
    file = models.ForeignKey('File', models.CASCADE, db_column='FileId', related_name="charts")
    absolute_path = models.CharField(db_column='AbsolutePath', max_length=255)
    relative_path = models.CharField(db_column='RelativePath', max_length=255)
    name = models.CharField(db_column='Name', max_length=255)

    class Meta:
        managed = False
        db_table = 'chart'


class File(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True)
    name = models.CharField(db_column='Name', max_length=255)
    absolute_path = models.CharField(db_column='AbsolutePath', max_length=255)
    label = models.CharField(db_column='Label', max_length=255)
    relative_path = models.CharField(db_column='RelativePath', max_length=255)

    class Meta:
        managed = False
        db_table = 'file'


class MusicalInstrument(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True)
    file = models.ForeignKey(File, models.CASCADE, db_column='FileId', related_name="musical_instruments")
    name = models.CharField(db_column='Name', max_length=255)

    class Meta:
        managed = False
        db_table = 'musicalinstrument'
