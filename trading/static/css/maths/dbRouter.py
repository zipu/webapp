# DB router for maths app

class MathsDBRouter(object):
    """
    A router tdo control maths db operations
    """
    def db_for_read(self, model, **hints):
        "point all operations on maths models to db 'maths'"
        if model._meta.app_label == 'maths':
            return 'maths'
        return None

    def db_for_write(self, model, **hints):
        "point all operations on maths models to db 'maths'"
        if model._meta.app_label == 'maths':
            return 'maths'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "point all operations on maths models to db 'maths'"
        if obj1._meta.app_label == 'maths' or \
           obj2._meta.app_label == 'maths':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'maths':
            return db == 'maths'
        return None
