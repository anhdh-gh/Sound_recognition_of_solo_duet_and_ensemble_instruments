CREATE TABLE `File` (
  Id    int(10) NOT NULL AUTO_INCREMENT, 
  Name  varchar(255) NOT NULL, 
  Path  varchar(255) NOT NULL, 
  Label varchar(255) NOT NULL, 
  PRIMARY KEY (Id)) CHARACTER SET UTF8;
CREATE TABLE MusicalInstrument (
  Id     int(10) NOT NULL AUTO_INCREMENT, 
  FileId int(10) NOT NULL, 
  Name   varchar(255) NOT NULL, 
  PRIMARY KEY (Id)) CHARACTER SET UTF8;
CREATE TABLE Attribute (
  Id     int(10) NOT NULL AUTO_INCREMENT, 
  FileId int(10) NOT NULL, 
  Name   varchar(255) NOT NULL, 
  PRIMARY KEY (Id)) CHARACTER SET UTF8;
CREATE TABLE AttributeValue (
  Id          int(10) NOT NULL AUTO_INCREMENT, 
  AttributeId int(10) NOT NULL, 
  Value       float NOT NULL, 
  PRIMARY KEY (Id)) CHARACTER SET UTF8;
ALTER TABLE MusicalInstrument ADD CONSTRAINT FKMusicalIns298676 FOREIGN KEY (FileId) REFERENCES `File` (Id);
ALTER TABLE Attribute ADD CONSTRAINT FKAttribute394945 FOREIGN KEY (FileId) REFERENCES `File` (Id);
ALTER TABLE AttributeValue ADD CONSTRAINT FKAttributeV783829 FOREIGN KEY (AttributeId) REFERENCES Attribute (Id);
