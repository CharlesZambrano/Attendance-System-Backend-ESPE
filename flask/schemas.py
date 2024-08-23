from marshmallow import Schema, fields


class AppUserSchema(Schema):
    FIRST_NAME = fields.Str(required=True, description="Nombre del usuario")
    LAST_NAME = fields.Str(required=True, description="Apellido del usuario")
    EMAIL = fields.Email(
        required=True, description="Correo electrónico del usuario")
    PASSWORD = fields.Str(required=True, description="Contraseña del usuario")
    ROLE_ID = fields.Int(
        required=True, description="ID del rol asignado al usuario")
    REGISTRATION_DATE = fields.Date(
        required=True, description="Fecha de registro del usuario")
    PROFESSOR_ID = fields.Int(
        description="ID del profesor asociado (si aplica)")


class AppUserResponseSchema(Schema):
    USER_ID = fields.Int(required=True, description="ID del usuario")
    FIRST_NAME = fields.Str(required=True, description="Nombre del usuario")
    LAST_NAME = fields.Str(required=True, description="Apellido del usuario")
    EMAIL = fields.Email(
        required=True, description="Correo electrónico del usuario")
    ROLE_ID = fields.Int(
        required=True, description="ID del rol asignado al usuario")
    REGISTRATION_DATE = fields.Date(
        required=True, description="Fecha de registro del usuario")
    PROFESSOR_ID = fields.Int(
        description="ID del profesor asociado (si aplica)")


class ProfessorSchema(Schema):
    USER_ID = fields.Int(required=True, description="ID del usuario asociado")
    PROFESSOR_CODE = fields.Str(
        required=True, description="Código del profesor")
    FIRST_NAME = fields.Str(required=True, description="Nombre del profesor")
    LAST_NAME = fields.Str(required=True, description="Apellido del profesor")
    EMAIL = fields.Email(
        required=True, description="Correo electrónico del profesor")
    REGISTRATION_DATE = fields.Date(
        required=True, description="Fecha de registro del profesor")
    UNIVERSITY_ID = fields.Int(
        required=True, description="ID de la universidad asociada")
    ID_CARD = fields.Str(
        required=True, description="Número de identificación del profesor")
    PHOTO = fields.Str(description="Foto del profesor (opcional)")


class ProfessorResponseSchema(Schema):
    PROFESSOR_ID = fields.Int(required=True, description="ID del profesor")
    USER_ID = fields.Int(required=True, description="ID del usuario asociado")
    PROFESSOR_CODE = fields.Str(
        required=True, description="Código del profesor")
    FIRST_NAME = fields.Str(required=True, description="Nombre del profesor")
    LAST_NAME = fields.Str(required=True, description="Apellido del profesor")
    EMAIL = fields.Email(
        required=True, description="Correo electrónico del profesor")
    REGISTRATION_DATE = fields.Date(
        required=True, description="Fecha de registro del profesor")
    UNIVERSITY_ID = fields.Int(
        required=True, description="ID de la universidad asociada")
    ID_CARD = fields.Str(
        required=True, description="Número de identificación del profesor")
    PHOTO = fields.Str(description="Foto del profesor (opcional)")


class ClassScheduleSchema(Schema):
    PROFESSOR_ID = fields.Int(required=True, description="ID del profesor")
    KNOWLEDGE_AREA = fields.Str(
        required=True, description="Área de conocimiento")
    EDUCATION_LEVEL = fields.Str(
        required=True, description="Nivel de formación")
    CODE = fields.Str(required=True, description="Código de la asignatura")
    SUBJECT = fields.Str(required=True, description="Nombre de la asignatura")
    NRC = fields.Str(required=True, description="Número de Registro de Cursos")
    STATUS = fields.Str(required=True, description="Estado de la asignatura")
    SECTION = fields.Str(required=True, description="Sección de la asignatura")
    CREDITS = fields.Float(
        required=True, description="Número de créditos de la asignatura")
    TYPE = fields.Str(required=True, description="Tipo de clase")
    BUILDING = fields.Str(description="Edificio donde se imparte la clase")
    CLASSROOM = fields.Str(description="Aula donde se imparte la clase")
    CAPACITY = fields.Int(description="Capacidad del aula")
    START_TIME = fields.DateTime(
        required=True, description="Hora de inicio de la clase")
    END_TIME = fields.DateTime(
        required=True, description="Hora de finalización de la clase")
    DAYS_OF_WEEK = fields.Str(
        required=True, description="Días de la semana en los que se imparte la clase")


class ClassScheduleResponseSchema(Schema):
    CLASS_SCHEDULE_ID = fields.Int(
        required=True, description="ID del horario de clase")
    PROFESSOR_ID = fields.Int(required=True, description="ID del profesor")
    KNOWLEDGE_AREA = fields.Str(
        required=True, description="Área de conocimiento")
    EDUCATION_LEVEL = fields.Str(
        required=True, description="Nivel de formación")
    CODE = fields.Str(required=True, description="Código de la asignatura")
    SUBJECT = fields.Str(required=True, description="Nombre de la asignatura")
    NRC = fields.Str(required=True, description="Número de Registro de Cursos")
    STATUS = fields.Str(required=True, description="Estado de la asignatura")
    SECTION = fields.Str(required=True, description="Sección de la asignatura")
    CREDITS = fields.Float(
        required=True, description="Número de créditos de la asignatura")
    TYPE = fields.Str(required=True, description="Tipo de clase")
    BUILDING = fields.Str(description="Edificio donde se imparte la clase")
    CLASSROOM = fields.Str(description="Aula donde se imparte la clase")
    CAPACITY = fields.Int(description="Capacidad del aula")
    START_TIME = fields.DateTime(
        required=True, description="Hora de inicio de la clase")
    END_TIME = fields.DateTime(
        required=True, description="Hora de finalización de la clase")
    DAYS_OF_WEEK = fields.Str(
        required=True, description="Días de la semana en los que se imparte la clase")


class ClassScheduleAttendanceSchema(Schema):
    CLASS_SCHEDULE_ID = fields.Int(
        required=True, description="ID del horario de clase")
    PROFESSOR_ID = fields.Int(required=True, description="ID del profesor")
    REGISTER_DATE = fields.Date(
        required=True, description="Fecha de registro de la asistencia")
    TIME = fields.DateTime(
        required=True, description="Hora de registro de la asistencia")


class ClassScheduleAttendanceResponseSchema(Schema):
    CLASS_SCHEDULE_ATTENDANCE_ID = fields.Int(
        required=True, description="ID del registro de asistencia")
    PROFESSOR_ID = fields.Int(required=True, description="ID del profesor")
    ATTENDANCE_CODE = fields.Str(
        required=True, description="Código de asistencia")
    REGISTER_DATE = fields.Date(
        required=True, description="Fecha de registro de la asistencia")
    ENTRY_TIME = fields.Str(
        required=True, description="Hora de entrada registrada")
    EXIT_TIME = fields.Str(description="Hora de salida registrada")
    TOTAL_HOURS = fields.Float(
        required=True, description="Horas totales registradas")
    LATE_ENTRY = fields.Str(
        required=True, description="Indica si hubo entrada tarde")
    TYPE = fields.Str(required=True, description="Tipo de asistencia")
    REGISTER_ENTRY = fields.Str(
        required=True, description="Indica si se registró la entrada")
    REGISTER_EXIT = fields.Str(
        required=True, description="Indica si se registró la salida")
    LATE_EXIT = fields.Str(description="Indica si hubo salida tarde")


class RoleSchema(Schema):
    ROLENAME = fields.Str(required=True, description="Nombre del rol")
    CREATIONDATE = fields.Date(
        required=True, description="Fecha de creación del rol")


class RoleResponseSchema(Schema):
    ROLE_ID = fields.Int(required=True, description="ID del rol")
    ROLENAME = fields.Str(required=True, description="Nombre del rol")
    CREATIONDATE = fields.Date(
        required=True, description="Fecha de creación del rol")


class WorkScheduleSchema(Schema):
    TEACHERID = fields.Int(required=True, description="ID del profesor")
    DAYS_OF_WEEK = fields.Str(
        required=True, description="Días de la semana en los que se imparte la clase")
    START_TIME = fields.DateTime(
        required=True, description="Hora de inicio de la jornada")
    END_TIME = fields.DateTime(
        required=True, description="Hora de finalización de la jornada")
    TOTAL_HOURS = fields.Float(
        required=True, description="Horas totales de la jornada")


class WorkScheduleResponseSchema(Schema):
    SCHEDULEID = fields.Int(
        required=True, description="ID de la jornada laboral")
    TEACHERID = fields.Int(required=True, description="ID del profesor")
    DAYS_OF_WEEK = fields.Str(
        required=True, description="Días de la semana en los que se imparte la clase")
    START_TIME = fields.DateTime(
        required=True, description="Hora de inicio de la jornada")
    END_TIME = fields.DateTime(
        required=True, description="Hora de finalización de la jornada")
    TOTAL_HOURS = fields.Float(
        required=True, description="Horas totales de la jornada")


class CreateEmbeddingSchema(Schema):
    maestro_id = fields.Int(required=True, description="ID del maestro")
    image = fields.Raw(
        required=True, description="Imagen del rostro para crear el embedding")


class CreateEmbeddingResponseSchema(Schema):
    message = fields.Str(required=True, description="Mensaje de éxito")


class DetectFaceSchema(Schema):
    image = fields.Raw(
        required=True, description="Imagen para detectar rostros")


class DetectFaceResponseSchema(Schema):
    faces = fields.List(fields.Dict(), required=True,
                        description="Lista de rostros detectados")


class RecognizeFaceSchema(Schema):
    image = fields.Raw(
        required=True, description="Imagen para reconocer rostros")
    faces = fields.List(fields.Dict(), required=True,
                        description="Coordenadas de los rostros detectados")


class RecognizeFaceResponseSchema(Schema):
    identities = fields.List(fields.Str(), required=True,
                             description="Lista de identidades reconocidas")
