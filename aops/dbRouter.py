# DB router for aops app

class AopsDBRouter(object):
    """
    A router to control aops db operations
    """
    def db_for_read(self, model, **hints):
        "point all operations on aops models to db 'aops'"
        if model._meta.app_label == 'aops':
            return 'aops'
        return None

    def db_for_write(self, model, **hints):
        "point all operations on aops models to db 'aops'"
        if model._meta.app_label == 'aops':
            return 'aops'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "point all operations on aops models to db 'aops'"
        if obj1._meta.app_label == 'aops' or \
           obj2._meta.app_label == 'aops':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'aops':
            return db == 'aops'
        return None
