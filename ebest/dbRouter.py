# DB router for trading app

class EbestDBRouter(object):
    """
    A router to control trading db operations
    """
    def db_for_read(self, model, **hints):
        "point all operations on trading models to db 'ebest'"
        if model._meta.app_label == 'ebest':
            return 'ebest'
        return None

    def db_for_write(self, model, **hints):
        "point all operations on trading models to db 'ebest'"
        if model._meta.app_label == 'ebest':
            return 'ebest'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "point all operations on trading models to db 'trading'"
        if obj1._meta.app_label == 'ebest' or \
           obj2._meta.app_label == 'ebest':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'ebest':
            return db == 'ebest'
        return None
